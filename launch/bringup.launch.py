# Copyright 2026 Robby
# SPDX-License-Identifier: Apache-2.0
"""Launch one fixed, fully equipped TIAGo in the Jetty demonstration warehouse."""
import os
from pathlib import Path
import shlex

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.actions import SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import yaml


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('rviz', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('moveit', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('nvidia', default_value='false', choices=['true', 'false'],
                              description='Use NVIDIA PRIME graphics on hybrid laptops.'),
        DeclareLaunchArgument('x', default_value='1.5'),
        DeclareLaunchArgument('y', default_value='-2.5'),
        DeclareLaunchArgument('z', default_value='0.04'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        OpaqueFunction(function=bringup),
    ])


def bringup(context):
    share = Path(get_package_share_directory('tiago_jetty'))

    def enabled(name):
        return LaunchConfiguration(name).perform(context) == 'true'

    def load(name):
        return yaml.safe_load((share / 'config' / name).read_text())

    description = (share / 'urdf/tiago.urdf.in').read_text().replace('@SHARE_DIR@', str(share))
    semantic = (share / 'urdf/tiago.srdf').read_text()
    robot = {'robot_description': ParameterValue(description, value_type=str),
             'use_sim_time': True}
    actions = [SetEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH', os.pathsep.join([
            str(share.parent), str(share / 'models'),
            os.environ.get('GZ_SIM_RESOURCE_PATH', ''),
        ]))]
    if enabled('nvidia'):
        actions.extend([
            SetEnvironmentVariable('__NV_PRIME_RENDER_OFFLOAD', '1'),
            SetEnvironmentVariable('__GLX_VENDOR_LIBRARY_NAME', 'nvidia'),
        ])

    gz_args = ['-r', '-v', '2', str(share / 'worlds/jetty.sdf')]
    if enabled('gui'):
        gz_args += ['--gui-config', str(share / 'config/gui.config')]
    else:
        gz_args += ['-s']
    actions.append(IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(
            Path(get_package_share_directory('ros_gz_sim')) / 'launch/gz_sim.launch.py')),
        launch_arguments={'gz_args': ' '.join(shlex.quote(arg) for arg in gz_args),
                          'on_exit_shutdown': 'true'}.items(),
    ))
    actions.append(Node(package='robot_state_publisher', executable='robot_state_publisher',
                        parameters=[robot], output='screen'))
    spawn_args = ['-name', 'tiago', '-topic', 'robot_description', '-world', 'default']
    for option in ['x', 'y', 'z']:
        spawn_args += [f'-{option}', str(float(LaunchConfiguration(option).perform(context)))]
    spawn_args += ['-Y', str(float(LaunchConfiguration('yaw').perform(context)))]
    actions.append(Node(package='ros_gz_sim', executable='create',
                        arguments=spawn_args, output='screen'))
    actions.append(Node(package='ros_gz_bridge', executable='parameter_bridge',
                        name='bridge_ros_gz', parameters=[{
                            'config_file': str(share / 'config/bridge.yaml'), 'use_sim_time': True,
                        }], output='screen'))
    actions.append(Node(package='twist_stamper', executable='twist_stamper',
                        parameters=[{'use_sim_time': True}],
                        remappings=[('cmd_vel_in', '/cmd_vel'),
                                    ('cmd_vel_out', '/mobile_base_controller/cmd_vel')],
                        output='screen'))
    controllers = ['joint_state_broadcaster', 'mobile_base_controller', 'torso_controller',
                   'head_controller', 'arm_controller', 'gripper_controller', 'ft_sensor_controller']
    actions.append(Node(package='controller_manager', executable='spawner',
                        arguments=controllers + ['--activate-as-group',
                                                 '--param-file', str(share / 'config/controllers.yaml'),
                                                 '--controller-manager-timeout', '180',
                                                 '--service-call-timeout', '120',
                                                 '--switch-timeout', '60'], output='screen'))

    if enabled('moveit'):
        planning = {
            **robot,
            'robot_description_semantic': ParameterValue(semantic, value_type=str),
            'robot_description_kinematics': load('kinematics.yaml'),
            'robot_description_planning': load('joint_limits.yaml'),
            'planning_pipelines': ['ompl'], 'default_planning_pipeline': 'ompl',
            'ompl': load('ompl_planning.yaml'),
            **load('moveit_controllers.yaml'),
            'publish_robot_description': True,
            'publish_robot_description_semantic': True,
            'publish_planning_scene': True,
            'publish_geometry_updates': True,
            'publish_state_updates': True,
            'publish_transforms_updates': True,
        }
        actions.append(Node(package='moveit_ros_move_group', executable='move_group',
                            parameters=[planning], output='screen'))
        actions.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(
                Path(get_package_share_directory('play_motion2')) / 'launch/play_motion2.launch.py')),
            launch_arguments={'use_sim_time': 'true',
                              'motions_file': str(share / 'config/motions.yaml'),
                              'motion_planner_config': str(share / 'config/motion_planner.yaml')}.items(),
        ))
    if enabled('rviz'):
        actions.append(Node(package='rviz2', executable='rviz2',
                            arguments=['-d', str(share / 'config/tiago.rviz')],
                            parameters=[robot], output='screen'))
    return actions
