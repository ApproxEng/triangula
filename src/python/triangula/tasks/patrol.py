import time

from euclid import Point2
from triangula.chassis import DeadReckoning, Motion, Pose
from triangula.dynamics import MotionLimit
from triangula.navigation import TaskWaypoint
from triangula.task import Task, ExitTask, PauseTask
from triangula.util import IntervalCheck


class SimplePatrolExample(Task):
    """
    Task to test the basics of the patrol logic, just runs a single patrol to 30cm ahead, pauses, then moves sideways.
    Hopefully. Set to not loop, so should in theory just move in an 'L' shape.
    """

    def __init__(self):
        super(SimplePatrolExample, self).__init__(task_name='Patrol Test', requires_compass=False)

    def init_task(self, context):
        pass

    def poll_task(self, context, tick):
        """
        Create a set of simple waypoints and return the appropriate :class:`triangula.tasks.patrol.PatrolTask` which
        will visit them in turn then exit.
        """
        waypoints = [
            TaskWaypoint(pose=Pose(position=Point2(0, 300), orientation=0), task=PauseTask(pause_time=3), stop=True),
            TaskWaypoint(pose=Pose(position=Point2(300, 300), orientation=0))]
        return PatrolTask(waypoints=waypoints, max_power=0.4)


class PatrolTask(Task):
    """
    A task which manages movement through a sequence of waypoints, potentially running sub-tasks at each waypoint.
    """

    ACCEL_TIME = 0.2

    def __init__(self, waypoints, loop=False, linear_offset=20, angular_offset=0.1, max_power=1.0):
        """
        Create a new Patrol task, specifying a sequence of waypoints, whether to patrol continuously, and tolerances
        used to determine when we've hit a waypoint and should start executing the waypoint's task.

        :param waypoints:
            List of :class:`triangula.navigation.TaskWaypoint` defining the patrol route.
        :param loop:
            Whether to patrol continuously, defaults to False in which case this task will return an ExitTask when it
            has completed all its waypoints. If True the task will not exit, and will repeatedly run through its list
            of TaskWaypoint targets until otherwise interrupted.
        :param linear_offset:
            Maximum linear distance away from the target Pose for each waypoint before we consider that we've hit it.
            Specified in mm, defaults to 20
        :param angular_offset:
            Maximum angular distance away from the target Pose for each waypoint before we consider that we've hit it.
            Specified in radians, defaults to 0.1
        :param max_power:
            A scale applied to motor speeds being sent to the chassis, defaults to 1.0 to move as fast as possible,
            lower values might be helpful when testing!
        """
        super(PatrolTask, self).__init__(task_name='Patrol', requires_compass=False)
        self.waypoints = waypoints
        self.loop = loop
        self.linear_offset = linear_offset
        self.angular_offset = angular_offset
        self.active_waypoint_index = None
        self.active_subtask = None
        self.dead_reckoning = None
        self.motion_limit = None
        self.pose_update_interval = IntervalCheck(interval=0.025)
        self.subtask_tick = 0
        self.max_power = max_power

    def init_task(self, context):
        self.active_waypoint_index = 0
        self.dead_reckoning = DeadReckoning(chassis=context.chassis, counts_per_revolution=3310)
        self.motion_limit = MotionLimit(
            linear_acceleration_limit=context.chassis.get_max_translation_speed() / PatrolTask.ACCEL_TIME,
            angular_acceleration_limit=context.chassis.get_max_rotation_speed() / PatrolTask.ACCEL_TIME)

    def poll_task(self, context, tick):
        # Check to see whether the minimum interval between dead reckoning updates has passed
        # Do this whether we're navigating or not, as it'll also register motion performed during the execution of a
        # task while at a waypoint.
        if self.pose_update_interval.should_run():
            self.dead_reckoning.update_from_counts(context.arduino.get_encoder_values())
            print self.dead_reckoning.pose

        waypoint = self.waypoints[self.active_waypoint_index]

        # If we don't have an active sub-task, we're in waypoint seeking mode.
        if self.active_subtask is None:
            target_pose = waypoint.pose
            # Are we close enough?
            if self.dead_reckoning.pose.is_close_to(target_pose, max_distance=self.linear_offset,
                                                    max_orientation_difference=self.angular_offset):
                # Close enough, do we have to come to a complete stop first?
                print 'Waypoint reached'
                if waypoint.stop:
                    braking_start_time = time.time()
                    while time.time() - braking_start_time <= PatrolTask.ACCEL_TIME:
                        self._set_motion(motion=Motion(), context=context)
                        if self.pose_update_interval.should_run():
                            self.dead_reckoning.update_from_counts(context.arduino.get_encoder_values())
                    # Stop full, this should already have happened but in case it didn't we don't want the
                    # robot to be moving while it runs the intermediate tasks.
                    context.arduino.set_motor_power(0, 0, 0)
                # Stopped or not, we now pick the waypoint task and start running it
                self.active_subtask = waypoint.task
                print 'Task is {}'.format(self.active_subtask)
                if self.active_subtask is None:
                    self.active_subtask = ExitTask()
                self.active_subtask.init_task(context=context)
                self.subtask_tick = 0
            else:
                # Not close enough, move towards waypoint
                print 'Moving towards waypoint'
                motion = self.dead_reckoning.pose.pose_to_pose_motion(to_pose=target_pose, time_seconds=0.01)
                scale = context.chassis.get_wheel_speeds(motion=motion).scaling
                motion = Motion(translation=motion.translation * scale, rotation=motion.rotation * scale)
                print motion
                self._set_motion(motion=motion, context=context)
        else:
            # We have a sub-task, should probably run it or something. Check it's not an ExitTask first though
            if isinstance(self.active_subtask, ExitTask):
                print 'Subtask is an ExitTask, moving on'
                self.active_subtask = None
            else:
                print 'Polling subtask, tick {}'.format(self.subtask_tick)
                task_result = self.active_subtask.poll_task(context=context, tick=self.subtask_tick)
                self.subtask_tick += 1
                if task_result is not None:
                    self.subtask_tick = 0
                    self.active_subtask = task_result
                    self.active_subtask.init_task(context=context)
            if self.active_subtask is None:
                print 'self.active_subtask is None, moving to next waypoint'
                # A previous sub-task returned an ExitTask, so we're done here. Move to the next waypoint, or exit
                # if we've hit all of them and we're not looping
                self.active_waypoint_index += 1
                if self.active_waypoint_index >= len(self.waypoints):
                    if self.loop:
                        self.active_waypoint_index = 0
                    else:
                        return ExitTask()

    def _set_motion(self, motion, context):
        """
        Using the motion limit traction control, apply the specified motion to the chassis.
        """
        motion = self.motion_limit.limit_and_return(motion=motion)
        wheel_speeds = context.chassis.get_wheel_speeds(motion=motion)
        speeds = wheel_speeds.speeds
        power = [speeds[i] / context.chassis.wheels[i].max_speed for i in range(0, 3)]
        context.arduino.set_motor_power(power[0] * self.max_power,
                                        power[1] * self.max_power,
                                        power[2] * self.max_power)
