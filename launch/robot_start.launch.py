import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node

package_name = "seer_system"


def generate_launch_description():
    # rviz_config = os.path.join(
    #     get_package_share_directory("turtle_tf2_py"), "rviz", "turtle_rviz.rviz"
    # )
    config = os.path.join(
        get_package_share_directory(package_name), "config", "params.yaml"
    )
    # print("config", config)

    seer_control_system_node = Node(
        package=package_name,
        # namespace="minhdeptria",
        executable="seer_control",
        # name="sim",
        # parameters=[config],
    )

    seer_navigation_node = Node(
        package=package_name,
        # namespace="minhdeptria",
        executable="navigation_control",
        # name="sim",
        # parameters=[config],
    )

    seer_lifting_node = Node(
        package=package_name,
        # namespace="minhdeptria",
        executable="lift_control",
        # name="sim",
        # parameters=[config],
    )
    # mockup_node = Node(
    #     package="amd_sevtsv",
    #     # namespace="minhdeptria",
    #     executable="mockup",
    #     # name="sim",
    #     # parameters=[config],
    # )

    return LaunchDescription([seer_control_system_node, seer_lifting_node])
