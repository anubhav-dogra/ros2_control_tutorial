from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument,  RegisterEventHandler, TimerAction, IncludeLaunchDescription
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessStart, OnProcessExit
from launch.launch_description_source import LaunchDescriptionSource


def generate_launch_description():
    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "runtime_config_package",
            default_value="controlko_bringup",
            description="Package with controller's configuration in the config folder. \
            Usually the argument is not set, it enables use of a custom setup",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "controllers_file",
            default_value="rrbot_controllers.yaml",
            description="YAML file with the controller configuration",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "description_package",
            default_value="controlko_description",
            description="Description package with robot URDF.  Usually the argument \
            is not set, it enables use of a custom description",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "description_file",
            default_value="rrbot.urdf.xacro",
            description="URDF file with the robot description",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "prefix",
            default_value='""',
            description="Prefix of the joint names, useful for \
            multi-robot setup. If changed than the 'robot' and 'gripper' \
            namespaces in the controllers' configuration have to be updated.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_mock_hardware",
            default_value="true",
            description="Start robot with fake hardware mirroring command to its states.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "mock_sensor_commands",
            default_value="true",
            description="Enable fake command interfaces for sensors used for simple simulations. \
            Used only if 'use_mock_hardware' parameter is true.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "robot_controller",
            default_value="joint_trajectory_controller",
            choices=["forward_position_controller", "joint_trajectory_controller"],
            description="Robot controller to start",
        )
    )

    # Initialize Arguments
    runtime_config_package = LaunchConfiguration("runtime_config_package")
    controllers_file = LaunchConfiguration("controllers_file")
    description_package = LaunchConfiguration("description_package")
    description_file = LaunchConfiguration("description_file")
    prefix = LaunchConfiguration("prefix")
    use_mock_hardware = LaunchConfiguration("use_mock_hardware")
    mock_sensor_commands = LaunchConfiguration("mock_sensor_commands")
    robot_controller = LaunchConfiguration("robot_controller")


    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare(runtime_config_package),
            "config",
            controllers_file
        ]
    )

    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare(description_package), "rviz", "rrbot.rviz"]
    )
    # Get URDF via xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare(description_package), "urdf", description_file]
            ),
            " ",
            "prefix:=",
            prefix,
            " ",
            "use_mock_hardware:=false",
            " ",
            "mock_sensor_commands:=false",
            " ",
            "sim_gazebo_classic:=true",
            " ",
            "sim_gazebo:=true",
            " ",
            "simulation_controllers:=",
            robot_controllers,
            " ",
        ]
    )
    
    robot_description = {"robot_description": robot_description_content}

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
    )

    # joint_state_publisher_node = Node(
    #     package="joint_state_publisher_gui",
    #     executable="joint_state_publisher_gui",
    # )
    

     # Gazebo nodes
    gazebo = IncludeLaunchDescription(
        LaunchDescriptionSource(
            [FindPackageShare("gazebo_ros"), "/launch", "/gazebo.launch.py"]
        ),
    )
    # Spawn robot
    gazebo_spawn_robot = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        name="spawn_rrbot",
        arguments=["-entity", "rrbot", "-topic", "robot_description"],
        output="screen",
    )
    # delay_rviz_after_joint_state_publisher_node = RegisterEventHandler(
    #     event_handler=OnProcessStart(
    #         target_action=joint_state_publisher_node,
    #         on_start=[
    #             TimerAction(
    #                 period=2.0,
    #                 actions=[rviz_node],
    #             ),
    #         ],
    #     )
    # )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager", 
            "/controller_manager",
        ],
    )

    robot_controllers = [robot_controller]
    # robot_controllers = ["forward_position_controller", "joint_trajectory_controller"]
    robot_controller_spawners = []
    for controller in robot_controllers:
        robot_controller_spawners += [
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[
                    controller,
                    "-c", 
                    "/controller_manager"],
                )
        ]

    controllers_to_spawn = robot_controller_spawners

    return LaunchDescription(
        declared_arguments
        + [
            gazebo,
            gazebo_spawn_robot,
            robot_state_publisher_node,
            rviz_node,
            joint_state_broadcaster_spawner]
        + 
            controllers_to_spawn            
    )
