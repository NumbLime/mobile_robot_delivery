"""Launch only the delivery task server for an existing Nav2 simulation."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'leg_timeout_sec',
            default_value='120.0',
            description='Steady-clock timeout in seconds for each Nav2 leg.',
        ),
        Node(
            package='delivery_task_manager',
            executable='delivery_task_server',
            name='delivery_task_server',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'leg_timeout_sec': ParameterValue(
                    LaunchConfiguration('leg_timeout_sec'), value_type=float
                ),
            }],
        ),
    ])
