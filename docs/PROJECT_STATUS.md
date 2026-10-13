# Project status

## Current stage: Nav2 single-goal navigation runtime acceptance passed

The workspace contains the robot description, Gazebo Classic world, mapping and static-map localization launch files, and a task manager package reserved for the next stage. `navigation.launch.py` and its configuration run the Nav2 single-goal stack using Humble's planner, controller, behavior, BT navigator, velocity smoother, and lifecycle manager nodes. The user has confirmed that single-goal navigation runtime acceptance is complete.

The navigation bringup reuses the existing Gazebo, robot spawn, controller spawners, map server, AMCL, and RViz flow. Navigation is requested only after the robot spawn and both controllers have completed successfully. The map and AMCL are started once, and SLAM is disabled in this mode.

## Navigation interfaces

- Saved map: `maps/delivery_world.yaml` with image `maps/delivery_world.pgm`; 117 × 118 cells at 0.05 m/cell.
- Laser scan: `/scan`, frame `laser_link`.
- Localization TF: AMCL publishes `map -> odom`.
- Odometry TF: `diff_drive_controller` publishes `odom -> base_footprint`.
- Navigation base frame: `base_footprint`.
- Controller input: `/diff_drive_controller/cmd_vel_unstamped` (`use_stamped_vel: false`).
- Velocity path: Nav2 controller and behavior outputs feed the velocity smoother; its output is remapped to the differential-drive controller input.
- Global costmap: static `/map` layer and inflation layer.
- Local costmap: `/scan` obstacle layer and inflation layer.
- Footprint: 0.40 m by 0.38 m rectangle, including the wheel lateral extent, with 0.02 m padding.
- All navigation and localization nodes use simulation time.

## Build and launch

```bash
source /opt/ros/humble/setup.bash
cd ~/mobile_robot_delivery
colcon build --packages-up-to delivery_robot_bringup
source install/setup.bash
ros2 launch delivery_robot_bringup navigation.launch.py
```

Optional arguments include `map:=/absolute/path/to/map.yaml`, `x:=...`, `y:=...`, `z:=...`, `yaw:=...`, `gui:=false`, and `rviz:=false`.

The existing modes remain available:

```bash
ros2 launch delivery_robot_bringup mapping.launch.py
ros2 launch delivery_robot_bringup localization.launch.py
```

## Validation status

### Runtime acceptance passed

- Mapping and map saving are complete. The saved files are `maps/delivery_world.yaml` and `maps/delivery_world.pgm` (117 × 118 cells, 0.05 m/cell).
- Static-map localization has been run and verified: after setting AMCL's initial pose, localization worked and keyboard teleoperation moved the robot as expected.
- RViz initially did not receive the static map because the Map display subscription used Volatile durability. After setting that display to Reliable + Transient Local, the map was received and displayed.
- After localization initialization, Nav2 lifecycle nodes entered `active`, the `/navigate_to_pose` action server was available, and the `map` to `base_footprint` TF stayed stable.
- Three independent NavigateToPose goals each reported “Reached the goal!” and “Goal succeeded”:
  - `(-0.02, -0.01) → (0.66, -1.11)`
  - `(0.63, -0.98) → (0.12, -1.58)`
  - `(0.23, -1.53) → (-0.39, 1.48)`
- `ros2 topic info /diff_drive_controller/cmd_vel_unstamped --verbose` showed `velocity_smoother` as publisher and `diff_drive_controller` as subscriber. The Reliable publisher and Best Effort subscriber matched successfully; `ros2 topic echo` received non-zero `Twist` messages during motion. This is motion evidence, not a separate check of the stopped state.

### Build and static checks

- `navigation.launch.py`, `navigation.yaml`, and `navigation.rviz` are implemented. `delivery_robot_bringup` built successfully with `colcon build --packages-select delivery_robot_bringup`.
- Python syntax and flake8 checks passed for the launch files; YAML/RViz and package XML parsing passed; Xacro expanded successfully; and `--show-args` succeeded for the mapping, localization, and navigation launch entries. Static assertions confirmed the configured frames, topics, command remaps, costmap layers, and map display QoS.

### Acceptance boundary

The single-goal Nav2 run is accepted. The velocity topic evidence above confirms messages during movement; it does not separately document the final zero-velocity/stop observation. Navigation obstacle avoidance and replanning comparisons, and any custom planner comparison, remain later work.

## Navigation troubleshooting

See [Navigation troubleshooting notes](NAVIGATION_TROUBLESHOOTING.md) for checks covering map delivery/QoS, AMCL initialization and TF, Nav2 lifecycle/action availability, costmap parameters, velocity command QoS, and startup laser-message filters.

## Next stage: delivery task workflow development

The existing `delivery_task_manager` is currently an `ament_python` package scaffold: it declares `rclpy` and `nav2_msgs`, but has no task node entry point, task sequencing implementation, or project-defined action interface. Develop the delivery workflow here as a client of Nav2's `/navigate_to_pose` action, with station order and feedback/result handling.

Navigation obstacle avoidance/replanning scenarios and custom planner comparisons remain subsequent stages after the delivery task workflow.
