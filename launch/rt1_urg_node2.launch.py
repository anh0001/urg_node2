# Copyright 2022 eSOL Co.,Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import launch
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch.actions import (DeclareLaunchArgument, EmitEvent, RegisterEventHandler)
from launch.event_handlers import OnProcessStart
from launch.events import matches_action
from launch_ros.actions import LifecycleNode
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState
from lifecycle_msgs.msg import Transition

def generate_launch_description():
    # Load default parameters from YAML
    config_file_path = os.path.join(
        get_package_share_directory('urg_node2'),
        'config',
        'params_serial.yaml'
    )
    
    with open(config_file_path, 'r') as file:
        config_params = yaml.safe_load(file)['urg_node2']['ros__parameters']

    # Declare all the LiDAR parameters with defaults from YAML if available
    declared_arguments = [
        DeclareLaunchArgument('auto_start', default_value='true'),
        DeclareLaunchArgument('node_name', default_value='urg_node2'),
        DeclareLaunchArgument('scan_topic_name', default_value='scan'),
        # URG specific parameters
        DeclareLaunchArgument('serial_port', 
            default_value=str(config_params.get('serial_port', '/dev/hokuyo'))),
        DeclareLaunchArgument('serial_baud', 
            default_value=str(config_params.get('serial_baud', '115200'))),
        DeclareLaunchArgument('frame_id', 
            default_value=str(config_params.get('frame_id', 'laser'))),
        DeclareLaunchArgument('calibrate_time', 
            default_value=str(config_params.get('calibrate_time', 'false'))),
        DeclareLaunchArgument('synchronize_time', 
            default_value=str(config_params.get('synchronize_time', 'false'))),
        DeclareLaunchArgument('publish_intensity', 
            default_value=str(config_params.get('publish_intensity', 'false'))),
        DeclareLaunchArgument('publish_multiecho', 
            default_value=str(config_params.get('publish_multiecho', 'false'))),
        DeclareLaunchArgument('error_limit', 
            default_value=str(config_params.get('error_limit', '4'))),
        DeclareLaunchArgument('error_reset_period', 
            default_value=str(config_params.get('error_reset_period', '5.0'))),
        DeclareLaunchArgument('diagnostics_tolerance', 
            default_value=str(config_params.get('diagnostics_tolerance', '0.05'))),
        DeclareLaunchArgument('diagnostics_window_time', 
            default_value=str(config_params.get('diagnostics_window_time', '5.0'))),
        DeclareLaunchArgument('time_offset', 
            default_value=str(config_params.get('time_offset', '0.0'))),
        DeclareLaunchArgument('angle_min', 
            default_value=str(config_params.get('angle_min', '-3.14'))),
        DeclareLaunchArgument('angle_max', 
            default_value=str(config_params.get('angle_max', '3.14'))),
        DeclareLaunchArgument('skip', 
            default_value=str(config_params.get('skip', '0'))),
        DeclareLaunchArgument('cluster', 
            default_value=str(config_params.get('cluster', '1')))
    ]

    # Create parameter dictionary that will override the YAML values
    override_params = {
        'serial_port': LaunchConfiguration('serial_port'),
        'serial_baud': LaunchConfiguration('serial_baud'),
        'frame_id': LaunchConfiguration('frame_id'),
        'calibrate_time': LaunchConfiguration('calibrate_time'),
        'synchronize_time': LaunchConfiguration('synchronize_time'),
        'publish_intensity': LaunchConfiguration('publish_intensity'),
        'publish_multiecho': LaunchConfiguration('publish_multiecho'),
        'error_limit': LaunchConfiguration('error_limit'),
        'error_reset_period': LaunchConfiguration('error_reset_period'),
        'diagnostics_tolerance': LaunchConfiguration('diagnostics_tolerance'),
        'diagnostics_window_time': LaunchConfiguration('diagnostics_window_time'),
        'time_offset': LaunchConfiguration('time_offset'),
        'angle_min': LaunchConfiguration('angle_min'),
        'angle_max': LaunchConfiguration('angle_max'),
        'skip': LaunchConfiguration('skip'),
        'cluster': LaunchConfiguration('cluster')
    }

    # Merge YAML config with override parameters
    # The override_params will take precedence over the YAML values
    merged_params = config_params.copy()
    merged_params.update(override_params)

    # URG Node as lifecycle node
    lifecycle_node = LifecycleNode(
        package='urg_node2',
        executable='urg_node2_node',
        name=LaunchConfiguration('node_name'),
        remappings=[('scan', LaunchConfiguration('scan_topic_name'))],
        parameters=[merged_params],
        namespace='',
        output='screen'
    )

    # Configure state transition handler
    urg_node2_node_configure_event_handler = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=lifecycle_node,
            on_start=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(lifecycle_node),
                        transition_id=Transition.TRANSITION_CONFIGURE,
                    ),
                ),
            ],
        ),
        condition=IfCondition(LaunchConfiguration('auto_start')),
    )

    # Activate state transition handler
    urg_node2_node_activate_event_handler = RegisterEventHandler(
        event_handler=OnStateTransition(
            target_lifecycle_node=lifecycle_node,
            start_state='configuring',
            goal_state='inactive',
            entities=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(lifecycle_node),
                        transition_id=Transition.TRANSITION_ACTIVATE,
                    ),
                ),
            ],
        ),
        condition=IfCondition(LaunchConfiguration('auto_start')),
    )

    # Create and return launch description
    return LaunchDescription(
        declared_arguments + [
            lifecycle_node,
            urg_node2_node_configure_event_handler,
            urg_node2_node_activate_event_handler,
        ]
    )