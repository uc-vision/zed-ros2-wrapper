# Copyright 2024 Stereolabs
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import yaml

from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    OpaqueFunction,
    IncludeLaunchDescription,
    LogInfo
)
from launch.substitutions import (
    LaunchConfiguration,
    TextSubstitution
)

def load_config_file(config_path):
    """Load and parse the YAML configuration file"""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print(f"Error loading config file {config_path}: {e}")
        return None

def launch_setup(context, *args, **kwargs):
    """Setup function that determines which launch file to use based on config"""
    
    actions = []
    
    # Automatically find the config file
    wrapper_dir = get_package_share_directory('zed_wrapper')
    config_path = os.path.join(wrapper_dir, 'config', 'zed_launch_config.yaml')
    
    actions.append(LogInfo(msg=TextSubstitution(text=f"Loading config from: {config_path}")))
    
    # Load configuration
    config = load_config_file(config_path)
    if config is None:
        return [LogInfo(msg=TextSubstitution(text="Failed to load configuration file. Using default single camera mode."))]
    
    mode = config.get('mode', 'single').lower()
    
    # Log the selected mode
    actions.append(LogInfo(msg=TextSubstitution(text=f"ZED Launch Mode: {mode}")))
    
    # wrapper_dir already defined above
    
    if mode == 'single':
        # Single camera configuration
        single_config = config.get('single_camera', {})
        
        actions.append(LogInfo(msg=TextSubstitution(text="Launching single ZED camera configuration")))
        
        # Prepare launch arguments for single camera - only pass specified parameters
        launch_args = {}
        
        # Required parameter
        if 'camera_model' in single_config:
            launch_args['camera_model'] = single_config['camera_model']
        else:
            actions.append(LogInfo(msg=TextSubstitution(text="ERROR: camera_model is required in single_camera config")))
            return actions
            
        # Optional parameters - only add if specified in config
        if 'camera_name' in single_config:
            launch_args['camera_name'] = single_config['camera_name']
        if 'serial_number' in single_config:
            launch_args['serial_number'] = str(single_config['serial_number'])
        if 'camera_id' in single_config:
            launch_args['camera_id'] = str(single_config['camera_id'])
        if 'namespace' in single_config:
            launch_args['namespace'] = single_config['namespace']
        
        # Include single camera launch file
        single_camera_launch = IncludeLaunchDescription(
            launch_description_source=PythonLaunchDescriptionSource([
                wrapper_dir, '/launch/zed_camera.launch.py'
            ]),
            launch_arguments=launch_args.items()
        )
        actions.append(single_camera_launch)
        
    elif mode == 'multi':
        # Multi camera configuration
        multi_config = config.get('multi_camera', {})
        
        actions.append(LogInfo(msg=TextSubstitution(text="Launching multi ZED camera configuration")))
        
        # Required parameters
        if 'cam_names' not in multi_config or 'cam_models' not in multi_config:
            actions.append(LogInfo(msg=TextSubstitution(text="ERROR: cam_names and cam_models are required in multi_camera config")))
            return actions
        
        cam_names = multi_config['cam_names']
        cam_models = multi_config['cam_models']
        
        # Optional parameters
        cam_serials = multi_config.get('cam_serials', [])
        cam_ids = multi_config.get('cam_ids', [])
        
        # Format arrays as strings
        cam_names_str = '[' + ','.join(cam_names) + ']'
        cam_models_str = '[' + ','.join(cam_models) + ']'
        cam_serials_str = '[' + ','.join(map(str, cam_serials)) + ']' if cam_serials else '[]'
        cam_ids_str = '[' + ','.join(map(str, cam_ids)) + ']' if cam_ids else '[]'
        
        # Prepare launch arguments for multi camera - only required ones
        launch_args = {
            'cam_names': cam_names_str,
            'cam_models': cam_models_str,
            'cam_serials': cam_serials_str,
            'cam_ids': cam_ids_str
        }
        
        # Include multi camera launch file
        multi_camera_launch = IncludeLaunchDescription(
            launch_description_source=PythonLaunchDescriptionSource([
                wrapper_dir, '/launch/zed_multi_camera.launch.py'
            ]),
            launch_arguments=launch_args.items()
        )
        actions.append(multi_camera_launch)
        
    else:
        actions.append(LogInfo(msg=TextSubstitution(
            text=f"Unknown mode '{mode}'. Please set mode to 'single' or 'multi' in the config file.")))
    
    return actions

def generate_launch_description():
    """Generate the launch description"""
    
    return LaunchDescription([
        OpaqueFunction(function=launch_setup)
    ])
