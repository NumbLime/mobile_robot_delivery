# Indoor Delivery AMR

ROS 2 Humble 与 Gazebo Classic 中的室内差速配送机器人项目。

## Packages

- `delivery_robot_description`: 差速底盘、激光雷达和 Gazebo 控制接口。
- `delivery_robot_bringup`: 仿真、建图、静态地图定位和 Nav2 导航启动配置。
- `delivery_task_manager`: 后续多站点任务管理包。

## Build

```bash
source /opt/ros/humble/setup.bash
cd ~/mobile_robot_delivery
colcon build
source install/setup.bash
```

## Bringup modes

Build a map:

```bash
ros2 launch delivery_robot_bringup mapping.launch.py
```

Localize on the saved map:

```bash
ros2 launch delivery_robot_bringup localization.launch.py
```

Start the robot with static-map localization and Nav2 single-goal navigation:

```bash
ros2 launch delivery_robot_bringup navigation.launch.py
```

The navigation RViz profile provides an initial-pose tool and a Nav2 goal tool. Set the AMCL initial pose before sending a goal. The default saved map is `maps/delivery_world.yaml`; the map, spawn pose, Gazebo GUI, and RViz can be overridden through launch arguments. Keyboard teleoperation remains a separate terminal workflow.

See [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for the current navigation design and manual validation steps.
