#!/usr/bin/env python3

"""Launch the delivery robot with static-map single-goal Nav2 navigation."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    default_world = PathJoinSubstitution([
        FindPackageShare('delivery_robot_bringup'),
        'worlds',
        'delivery_room.world',
    ])
    default_map = PathJoinSubstitution([
        FindPackageShare('delivery_robot_bringup'),
        'maps',
        'delivery_world.yaml',
    ])
    default_navigation_params = PathJoinSubstitution([
        FindPackageShare('delivery_robot_bringup'),
        'config',
        'navigation.yaml',
    ])
    default_rviz_config = PathJoinSubstitution([
        FindPackageShare('delivery_robot_bringup'),
        'config',
        'navigation.rviz',
    ])

    bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('delivery_robot_bringup'),
            'launch',
            'mapping.launch.py',
        ])),
        launch_arguments={
            'world': LaunchConfiguration('world'),
            'gui': LaunchConfiguration('gui'),
            'use_sim_time': 'true',
            'slam': 'false',
            'localization': 'true',
            'navigation': 'true',
            'rviz': LaunchConfiguration('rviz'),
            'map': LaunchConfiguration('map'),
            'navigation_params_file': LaunchConfiguration(
                'navigation_params_file'
            ),
            'navigation_rviz_config': LaunchConfiguration(
                'navigation_rviz_config'
            ),
            'x': LaunchConfiguration('x'),
            'y': LaunchConfiguration('y'),
            'z': LaunchConfiguration('z'),
            'yaw': LaunchConfiguration('yaw'),
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=default_world,
            description='Gazebo Classic world file.',
        ),
        DeclareLaunchArgument(
            'gui', default_value='true', description='Start the Gazebo GUI.'
        ),
        DeclareLaunchArgument(
            'rviz', default_value='true', description='Start RViz2.'
        ),
        DeclareLaunchArgument(
            'map',
            default_value=default_map,
            description='Static map YAML file for localization.',
        ),
        DeclareLaunchArgument(
            'navigation_params_file',
            default_value=default_navigation_params,
            description='Nav2 navigation parameter file.',
        ),
        DeclareLaunchArgument(
            'navigation_rviz_config',
            default_value=default_rviz_config,
            description='RViz profile for navigation.',
        ),
        DeclareLaunchArgument(
            'x', default_value='0.0', description='Robot spawn x position.'
        ),
        DeclareLaunchArgument(
            'y', default_value='0.0', description='Robot spawn y position.'
        ),
        DeclareLaunchArgument(
            'z', default_value='0.0', description='Robot spawn z position.'
        ),
        DeclareLaunchArgument(
            'yaw',
            default_value='0.0',
            description='Robot spawn yaw in radians.',
        ),
        bringup_launch,
    ])
