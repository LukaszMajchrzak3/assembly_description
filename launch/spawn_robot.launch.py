import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # 1. Ścieżki do paczki i plików
    pkg_name = 'assembly_description'
    pkg_share = get_package_share_directory(pkg_name)
    urdf_file = os.path.join(pkg_share, 'urdf', 'robot.urdf')

    # Wczytanie zawartości pliku URDF
    with open(urdf_file, 'r') as infp:
        robot_desc = infp.read()

    # 2. Zmienna środowiskowa - BARDZO WAŻNE DLA GAZEBO FORTRESS
    # Mówi symulatorowi, gdzie ma szukać plików z przedrostkiem "package://"
    # share_dir to ścieżka do /install/assembly_description/share, dodajemy jej rodzica
    ign_resource_path = AppendEnvironmentVariable(
        'IGN_GAZEBO_RESOURCE_PATH',
        os.path.join(pkg_share, '..')
    )

    # 3. Węzeł Robot State Publisher (czyta URDF i publikuje go dla innych węzłów)
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_desc, 'use_sim_time': True}]
    )

    # 4. Uruchomienie Gazebo Fortress (pusty świat)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')]),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(),
    )

    # 5. Węzeł Spawnujący robota w Gazebo
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'Assembly',  # Nazwa zdefiniowana w URDF
            '-z', '0.2'           # Spawnuje robota lekko nad ziemią, żeby nie utknął w podłodze
        ]
    )

    # 6. Mostek komunikacyjny ROS 2 <-> Gazebo (Napęd pojazdu)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist'
        ],
        output='screen'
    )

    return LaunchDescription([
        ign_resource_path,
        gazebo,
        node_robot_state_publisher,
        spawn_entity,
        bridge
    ])