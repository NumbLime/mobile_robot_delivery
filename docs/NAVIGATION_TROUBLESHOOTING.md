# Navigation troubleshooting notes

These checks are based on the current Humble bringup and observed issues. Startup warnings can be transient; verify the node state, time, TF, and endpoints before changing configuration.

## Static map is missing in RViz

Check the map server lifecycle state and topic endpoints separately:

```bash
ros2 lifecycle get /map_server
ros2 topic info /map --verbose
```

If `map_server` is not `active`, `/map` may not yet have a publisher. Check lifecycle activation first instead of concluding that RViz QoS is wrong. Once active, inspect the publisher count, `nav_msgs/msg/OccupancyGrid` type, and offered QoS in the verbose topic output. A subscriber that starts after a static map was published needs compatible Transient Local durability to receive the retained map. In this project, changing the RViz Map display to Reliable + Transient Local resolved the missing-map display.

## AMCL initial pose and TF

The AMCL message `AMCL cannot publish a pose... Please set the initial pose` means AMCL needs an initial pose consistent with the robot's actual position in Gazebo. Set it with RViz **2D Pose Estimate**, then allow localization and transforms to settle.

Before initialization, a missing `map` frame or a brief `past extrapolation` from `tf2_echo` can occur while localization, simulation time, and the TF buffer are becoming ready. After setting the pose, recheck the expected chain:

```bash
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo odom base_footprint
```

If errors continue after the chain should be stable, check `/clock`, `use_sim_time` on localization/navigation nodes, the TF publishers, and message/transform timestamps.

## `controller_server` exits and dependent services do not appear

During earlier troubleshooting, `controller_server` exited with code `-6`, while the planner, BT navigator, or other nodes waited for services. That observation alone does not establish a single root cause.

For a costmap parameter failure, compare the source YAML, installed YAML, and the file actually passed by the launch argument `navigation_params_file`. Nav2 Humble expects integer types for the local costmap `width` and `height` parameters in this configuration; a decimal value such as `3.0` can trigger a parameter type mismatch. The current source file and current install file `install/delivery_robot_bringup/share/delivery_robot_bringup/config/navigation.yaml` both contain integer values `3` for these parameters, and the launch passes the selected navigation parameter file to `controller_server` and the other Nav2 nodes. If changing the source config, rebuild the package and inspect the installed file and launch argument again before rerunning. Do not attribute an earlier crash to this issue unless the corresponding error log confirms it.

## Lifecycle nodes and `/navigate_to_pose`

At launch startup, some Nav2 nodes may not yet be `active`; this alone does not mean navigation will remain unavailable. First set the AMCL initial pose and allow `map -> odom -> base_footprint` and the costmaps to initialize. Then check lifecycle state and action-server availability:

```bash
ros2 lifecycle nodes
ros2 lifecycle get /bt_navigator
ros2 lifecycle get /controller_server
ros2 action info /navigate_to_pose
```

If RViz reports that the action server is unavailable, check the BT navigator lifecycle state and earlier initialization errors in the launch output.

## Velocity command chain and QoS

Verify the final command topic endpoints and their QoS:

```bash
ros2 topic info /diff_drive_controller/cmd_vel_unstamped --verbose
ros2 topic echo /diff_drive_controller/cmd_vel_unstamped
```

The expected chain is Nav2 controller/behavior output to `velocity_smoother`, then the smoother to `/diff_drive_controller/cmd_vel_unstamped`. In the accepted run, the publisher was `velocity_smoother`, the subscriber was `diff_drive_controller`, and the Reliable publisher matched the Best Effort subscriber; `ros2 topic echo` received messages. Non-zero `Twist` while the robot is moving confirms motion commands are flowing, not that the robot stopped at the goal. Check the stopped state separately if stop behavior is part of the acceptance test.

## RViz laser message filter warnings

Laser messages may be filtered during startup while TF or simulation time is settling, for example when the transform is not yet available for the message timestamp. Wait for the TF chain and clock to stabilize, then check whether the warning persists. If it does, inspect the `/scan` frame, the TF chain to `base_footprint`, `use_sim_time`, and the scan and transform timestamps; do not assume continuing drops are harmless.
