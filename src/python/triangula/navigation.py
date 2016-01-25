class TaskWaypoint:
    """
    Consists of a target Pose defining a location and orientation, and a Task which should be run when the robot reaches
    the target position. The task can be None, in which case the robot won't attempt to do anything at the target point.
    """

    def __init__(self, pose, task=None, stop=False):
        """
        Constructor

        :param triangula.chassis.Pose pose:
            The target Pose, defining the location and orientation of this waypoint
        :param triangula.task.Task task:
            A Task to run when the target point is reached. The task will be run until a non-None value is returned from
            the poll method. Defaults to None, in which case no task will be invoked and the robot will proceed
            immediately to the next waypoint.
        :param stop:
            Defaults to False, if this is set to True then the robot will come to a complete stop before either running
            the sub-task or proceeding to the next waypoint.
        """
        self.pose = pose
        self.task = task
        self.stop = stop