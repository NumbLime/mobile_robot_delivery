# Indoor Delivery AMR

ROS 2 Humble 与 Gazebo Classic 中的室内差速配送机器人项目。

## Packages

- `delivery_robot_description`: 差速底盘、激光雷达和 Gazebo 控制接口。
- `delivery_robot_bringup`: 仿真、建图、静态地图定位和 Nav2 导航启动配置。
- `delivery_task_interfaces`: 取货点与送达点任务的 ROS action 接口。
- `delivery_task_manager`: 顺序调用 Nav2 的取货、送达任务节点；两站成功、分段取消和超时已在 Gazebo/Nav2 中运行验收，独立停车证据及限制见项目状态文档。

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

Once navigation and AMCL are ready, start the delivery task server in another terminal:

```bash
ros2 launch delivery_task_manager task_manager.launch.py
```

This launch starts only the task server. Its `leg_timeout_sec` argument defaults to `120.0` seconds per navigation leg; for example, `ros2 launch delivery_task_manager task_manager.launch.py leg_timeout_sec:=30.0`. The timeout uses a steady clock, requests Nav2 goal cancellation, and waits for Nav2 to finish before the delivery action returns. See [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for result semantics, validation status, and manual checks.

For operator-run success, cancellation, and timeout checks, use the separate `delivery_acceptance_client` executable and follow [docs/DELIVERY_ACCEPTANCE.md](docs/DELIVERY_ACCEPTANCE.md). The client is a test tool; it does not start Gazebo/Nav2 or change the task server's navigation logic.

V0.1 的运行日志、bag、离线分析报告和演示录像保存在仓库外的 `~/mobile_robot_delivery_acceptance_logs/`；GitHub 备份仅包含本仓库内的源码、配置、地图与文档，不包含这些运行证据文件。
