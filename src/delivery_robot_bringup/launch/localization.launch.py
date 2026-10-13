#!/usr/bin/env python3

"""Launch the delivery robot in Gazebo with static-map localization."""

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

    mapping_launch = IncludeLaunchDescription(
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
            'rviz': LaunchConfiguration('rviz'),
            'map': LaunchConfiguration('map'),
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
            description='Gazebo world file.',
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
            description='Static map YAML file.',
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
        mapping_launch,
    ])
