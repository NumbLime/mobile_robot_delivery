#!/usr/bin/env python3

"""Launch Gazebo Classic, the delivery robot, controllers, SLAM, and RViz."""

import os
from pathlib import Path
import tempfile

import yaml

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    RegisterEventHandler,
    SetLaunchConfiguration,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _remove_controller_params(context, *args, **kwargs):
    params_path = LaunchConfiguration(
        'controller_params_file'
    ).perform(context)
    try:
        Path(params_path).unlink()
    except FileNotFoundError:
        pass
    return []


def _next_or_shutdown(event, description, next_actions):
    if event.returncode == 0:
        return [LogInfo(msg=f'{description} completed.'), *next_actions]

    reason = f'{description} failed with exit code {event.returncode}.'
    return [
        LogInfo(msg=f'ERROR: {reason}'),
        EmitEvent(event=Shutdown(reason=reason)),
    ]


def _start_rviz(context, *args, **kwargs):
    if LaunchConfiguration('rviz').perform(context).lower() != 'true':
        return []

    navigation_enabled = (
        LaunchConfiguration('navigation').perform(context).lower() == 'true'
    )
    rviz_arguments = []
    if navigation_enabled:
        rviz_arguments = [
            '-d',
            LaunchConfiguration('navigation_rviz_config').perform(context),
        ]

    return [Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=rviz_arguments,
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }],
    )]


def _generate_launch_description(context, *args, **kwargs):
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context).lower()
    if use_sim_time not in ('true', 'false'):
        raise RuntimeError("'use_sim_time' must be 'true' or 'false'.")

    slam_enabled = LaunchConfiguration('slam').perform(context).lower()
    localization_enabled = LaunchConfiguration(
        'localization'
    ).perform(context).lower()
    navigation_enabled = LaunchConfiguration(
        'navigation'
    ).perform(context).lower()
    if slam_enabled not in ('true', 'false'):
        raise RuntimeError("'slam' must be 'true' or 'false'.")
    if localization_enabled not in ('true', 'false'):
        raise RuntimeError("'localization' must be 'true' or 'false'.")
    if navigation_enabled not in ('true', 'false'):
        raise RuntimeError("'navigation' must be 'true' or 'false'.")
    if slam_enabled == 'true' and localization_enabled == 'true':
        raise RuntimeError(
            'SLAM and static map localization cannot run together.'
        )
    if localization_enabled == 'true' and use_sim_time != 'true':
        raise RuntimeError(
            'Static map localization requires use_sim_time:=true.'
        )
    if navigation_enabled == 'true' and localization_enabled != 'true':
        raise RuntimeError(
            'Navigation requires static map localization to be enabled.'
        )
    if navigation_enabled == 'true' and use_sim_time != 'true':
        raise RuntimeError(
            'Navigation requires use_sim_time:=true.'
        )

    bringup_share = Path(
        FindPackageShare('delivery_robot_bringup').perform(context)
    )
    controller_params_path = bringup_share / 'config' / 'ros2_controllers.yaml'
    controller_params = yaml.safe_load(controller_params_path.read_text())
    manager_parameters = controller_params.get('controller_manager', {}).get(
        'ros__parameters'
    )
    if not isinstance(manager_parameters, dict):
        raise RuntimeError(
            'Expected controller_manager.ros__parameters in '
            f'{controller_params_path}'
        )
    manager_parameters['use_sim_time'] = use_sim_time == 'true'

    file_descriptor, generated_params_path = tempfile.mkstemp(
        prefix='delivery_robot_controllers_', suffix='.yaml'
    )
    with os.fdopen(file_descriptor, 'w') as generated_params_file:
        yaml.safe_dump(
            controller_params, generated_params_file, sort_keys=False
        )

    use_sim_time_config = LaunchConfiguration('use_sim_time')
    controller_params_config = LaunchConfiguration('controller_params_file')
    robot_description_path = PathJoinSubstitution([
        FindPackageShare('delivery_robot_description'),
        'urdf',
        'delivery_robot.urdf.xacro',
    ])
    robot_description = Command([
        FindExecutable(name='xacro'),
        ' ',
        robot_description_path,
        ' controllers_file:=',
        controller_params_config,
    ])

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('gazebo_ros'),
            'launch',
            'gazebo.launch.py',
        ])),
        launch_arguments={
            'world': LaunchConfiguration('world'),
            'gui': LaunchConfiguration('gui'),
        }.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': use_sim_time_config,
        }],
    )

    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_delivery_robot',
        output='screen',
        arguments=[
            '-entity', 'delivery_robot',
            '-topic', '/robot_description',
            '-timeout', '60.0',
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', LaunchConfiguration('z'),
            '-Y', LaunchConfiguration('yaw'),
        ],
    )

    joint_state_spawner = Node(
        package='controller_manager',
        executable='spawner',
        name='spawn_joint_state_broadcaster',
        output='screen',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60.0',
            '--service-call-timeout', '60.0',
        ],
    )

    diff_drive_spawner = Node(
        package='controller_manager',
        executable='spawner',
        name='spawn_diff_drive_controller',
        output='screen',
        arguments=[
            'diff_drive_controller',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60.0',
            '--service-call-timeout', '60.0',
        ],
    )

    slam = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            str(bringup_share / 'config' / 'slam_toolbox.yaml'),
            {'use_sim_time': use_sim_time_config},
        ],
        condition=IfCondition(LaunchConfiguration('slam')),
    )

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('nav2_bringup'),
            'launch',
            'localization_launch.py',
        ])),
        launch_arguments={
            'map': LaunchConfiguration('map'),
            'params_file': LaunchConfiguration('localization_params_file'),
            'use_sim_time': use_sim_time_config,
            'autostart': 'true',
            'use_composition': 'False',
            'use_respawn': 'False',
        }.items(),
        condition=IfCondition(LaunchConfiguration('localization')),
    )

    navigation_params = LaunchConfiguration('navigation_params_file')
    navigation_condition = IfCondition(LaunchConfiguration('navigation'))
    tf_remappings = [('/tf', 'tf'), ('/tf_static', 'tf_static')]
    navigation_nodes = [
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output='screen',
            parameters=[navigation_params, {'use_sim_time': True}],
            remappings=tf_remappings + [('cmd_vel', '/cmd_vel_nav')],
            condition=navigation_condition,
        ),
        Node(
            package='nav2_smoother',
            executable='smoother_server',
            name='smoother_server',
            output='screen',
            parameters=[navigation_params, {'use_sim_time': True}],
            remappings=tf_remappings,
            condition=navigation_condition,
        ),
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[navigation_params, {'use_sim_time': True}],
            remappings=tf_remappings,
            condition=navigation_condition,
        ),
        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            output='screen',
            parameters=[navigation_params, {'use_sim_time': True}],
            remappings=tf_remappings + [('cmd_vel', '/cmd_vel_nav')],
            condition=navigation_condition,
        ),
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[navigation_params, {'use_sim_time': True}],
            remappings=tf_remappings,
            condition=navigation_condition,
        ),
        Node(
            package='nav2_waypoint_follower',
            executable='waypoint_follower',
            name='waypoint_follower',
            output='screen',
            parameters=[navigation_params, {'use_sim_time': True}],
            remappings=tf_remappings,
            condition=navigation_condition,
        ),
        Node(
            package='nav2_velocity_smoother',
            executable='velocity_smoother',
            name='velocity_smoother',
            output='screen',
            parameters=[navigation_params, {'use_sim_time': True}],
            remappings=tf_remappings + [
                ('cmd_vel', '/cmd_vel_nav'),
                (
                    'cmd_vel_smoothed',
                    '/diff_drive_controller/cmd_vel_unstamped',
                ),
            ],
            condition=navigation_condition,
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'autostart': True,
                'node_names': [
                    'controller_server',
                    'smoother_server',
                    'planner_server',
                    'behavior_server',
                    'bt_navigator',
                    'waypoint_follower',
                    'velocity_smoother',
                ],
            }],
            condition=navigation_condition,
        ),
    ]
    rviz = OpaqueFunction(function=_start_rviz)

    return [
        SetLaunchConfiguration(
            'controller_params_file', generated_params_path
        ),
        RegisterEventHandler(OnShutdown(on_shutdown=[OpaqueFunction(
            function=_remove_controller_params
        )])),
        gazebo,
        robot_state_publisher,
        RegisterEventHandler(OnProcessExit(
            target_action=spawn_robot,
            on_exit=lambda event, ctx: _next_or_shutdown(
                event, 'Robot spawn', [joint_state_spawner]
            ),
        )),
        RegisterEventHandler(OnProcessExit(
            target_action=joint_state_spawner,
            on_exit=lambda event, ctx: _next_or_shutdown(
                event, 'Joint state broadcaster', [diff_drive_spawner]
            ),
        )),
        RegisterEventHandler(OnProcessExit(
            target_action=diff_drive_spawner,
            on_exit=lambda event, ctx: _next_or_shutdown(
                event,
                'Diff drive controller',
                [slam, localization, *navigation_nodes, rviz],
            ),
        )),
        spawn_robot,
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=PathJoinSubstitution([
                FindPackageShare('delivery_robot_bringup'),
                'worlds',
                'delivery_room.world',
            ]),
            description='Gazebo Classic world file.',
        ),
        DeclareLaunchArgument(
            'gui', default_value='true', description='Start the Gazebo GUI.'
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use the Gazebo clock for ROS nodes and controllers.',
        ),
        DeclareLaunchArgument(
            'slam',
            default_value='true',
            description='Start asynchronous SLAM Toolbox.',
        ),
        DeclareLaunchArgument(
            'localization',
            default_value='false',
            description='Start Nav2 map_server and AMCL localization.',
        ),
        DeclareLaunchArgument(
            'navigation',
            default_value='false',
            description='Start the Nav2 single-goal navigation stack.',
        ),
        DeclareLaunchArgument(
            'navigation_params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('delivery_robot_bringup'),
                'config',
                'navigation.yaml',
            ]),
            description=(
                'Nav2 planner, controller, costmap and behavior parameters.'
            ),
        ),
        DeclareLaunchArgument(
            'navigation_rviz_config',
            default_value=PathJoinSubstitution([
                FindPackageShare('delivery_robot_bringup'),
                'config',
                'navigation.rviz',
            ]),
            description='RViz profile for single-goal navigation.',
        ),
        DeclareLaunchArgument(
            'rviz', default_value='true', description='Start RViz2.'
        ),
        DeclareLaunchArgument(
            'map',
            default_value=PathJoinSubstitution([
                FindPackageShare('delivery_robot_bringup'),
                'maps',
                'delivery_world.yaml',
            ]),
            description='Static map YAML file for Nav2 localization.',
        ),
        DeclareLaunchArgument(
            'localization_params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('delivery_robot_bringup'),
                'config',
                'amcl_localization.yaml',
            ]),
            description='Nav2 map_server and AMCL parameter file.',
        ),
        DeclareLaunchArgument(
            'x', default_value='0.0', description='Spawn x position.'
        ),
        DeclareLaunchArgument(
            'y', default_value='0.0', description='Spawn y position.'
        ),
        DeclareLaunchArgument(
            'z', default_value='0.0', description='Spawn z position.'
        ),
        DeclareLaunchArgument(
            'yaw', default_value='0.0', description='Spawn yaw in radians.'
        ),
        OpaqueFunction(function=_generate_launch_description),
    ])
