triangula.navigation: Navigation and Routing
============================================

This module handles navigation, waypoints and similar.

Waypoints
---------

At the moment we have a single waypoint class. The :class:`triangula.navigation.TaskWaypoint` defines a target pose and,
optionally, a task to run when that pose is reached. This is used by the :class:`triangula.task.patrol.PatrolTask` to
navigate to a list of places and perform actions in each place.

.. autoclass:: triangula.navigation.TaskWaypoint
    :members: