# 项目协作说明

## 项目环境

- 项目使用 Ubuntu 22.04.5、ROS 2 Humble 和 Gazebo Classic；本机工作区为 `~/mobile_robot_delivery`。
- 用户希望通过完成项目理解代码。代码修改和验证完成后，请分步解释关键代码、节点关系和数据流。

## 修改与验证

- 修改前先检查实际仓库结构和配置；不要猜测路径、参数、话题或运行状态。
- 汇报时明确区分构建/静态检查结果与仿真运行验证结果，不要把静态检查描述成运行验证。
- 静态检查任务不要擅自启动 Gazebo/RViz，也不要发送机器人运动命令。若任务要求运行验证，启动前先检查是否已有仿真实例，避免重复启动。
- 不要自动执行 git commit 或 push。

## 项目开发 Skill

- 本机项目开发 Skill 位于 `~/ros2-robotics-learning/.agents/skills/ros2-project-to-portfolio/`。需要遵循时，从该位置读取；不要复制到当前仓库。
