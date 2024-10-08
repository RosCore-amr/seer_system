from setuptools import find_packages, setup
import os
from glob import glob

package_name = "seer_system"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.[pxy][yma]*")),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob(os.path.join("config", "*.*")),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="mm",
    maintainer_email="engineer.pqm@gmail.com",
    description="TODO: Package description",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "seer_control = seer_system.seer_control:main",
            "test = seer_system.sever_:main",
            "communication_modbus = seer_system.communication_modbus:main",
            "socket_communication = seer_system.socket_seer_communication:main",
            "lift_control = seer_system.lift_control:main",
            "led_control = seer_system.led_control:main",
            "navigation_control = seer_system.navigation_control:main",
            "map_change = seer_system.change_map:main",
        ],
    },
)
