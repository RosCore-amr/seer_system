#!/usr/bin/python3
from socket import socket

from seer_system.frame import tranmit
from seer_system.api import status, navigation, config, control, other
import socket

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

# from action_tutorials_interfaces.action import Fibonacci
# from action_tutorials_interfaces.action import Fibonacci
from action_interfaces_msg.action import Fibonacci
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from robot_interfaces.srv import CommonRequest
from std_msgs.msg import String


class SockerControlSeer(Node):

    def __init__(self):
        super().__init__("communication_socker_seer")
        self.timer_cb = MutuallyExclusiveCallbackGroup()

        self.timer = self.create_timer(
            1.0, self.main_loop, callback_group=self.timer_cb
        )
        self.seer_response_publisher_ = self.create_publisher(
            String, "seer_response", 10
        )

        self.srv_seer_api_navigation = self.create_service(
            CommonRequest, "navigation_seer_api", self.navigation_seer_srv
        )
        self.srv_seer_api_robot_control = self.create_service(
            CommonRequest, "robot_control_seer_api", self.robot_control_seer_srv
        )

        # self.subscription_sensor_lift = self.create_subscription(
        #     String, "robot_status", self.robot_status_callback, 1
        # )
        self.key_seer = {
            "keys": [
                "area_ids",
                "confidence",
                "current_station",
                "last_station",
                "vx",
                "vy",
                "blocked",
                "block_reason",
                "battery_level",
                "task_status",
                "target_id",
                "emergency",
                "x",
                "y",
                "unfinished_path",
                "target_dist",
                "angle",
                "reloc_status",
                "current_map",
                "charging",
            ],
            "return_laser": False,
            "return_beams3D": False,
        }

        self.status_connect_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.control_connect_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.navigation_connect_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        self.config_connect_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.other_connect_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.initial_protocol()

    def initial_protocol(self):
        _port_status = 19204
        _port_control = 19205
        _port_navigation = 19206
        _port_config = 19207
        _port_other = 19210
        self.host_seer = "192.168.1.103"

        status_connect = self.connect_socket(self.status_connect_socket, _port_status)
        control_connect = self.connect_socket(
            self.control_connect_socket, _port_control
        )
        navigation_connect = self.connect_socket(
            self.navigation_connect_socket, _port_navigation
        )
        config_connect = self.connect_socket(self.config_connect_socket, _port_config)
        other_connect = self.connect_socket(self.other_connect_socket, _port_other)

        if (
            status_connect
            and control_connect
            and navigation_connect
            and config_connect
            and other_connect
        ):
            self.get_logger().info(" all connect success")
        else:
            self.initial_protocol()

    def connect_socket(self, _socket, _port):
        # self.get_logger().info(': "%s"' % _socket)
        return True

        # try:
        #     _socket.settimeout(5000)
        #     _socket.connect((self.host_seer, _port))
        # except socket.error:
        #     # logging.info("connection STATUS lost... reconnecting")
        #     # time.sleep(5)
        #     self.connect_status()

    def sent_api_seer(
        self, socket_protocal: socket, api_code: int, value_request: dict
    ) -> dict:

        result = tranmit.sendAPI(socket_protocal, api_code, value_request)
        if result["ret_code"] != 0:
            return False
        return result

    def robot_status_callback(self, msg):
        _data_robot_status = eval(msg.data)
        self.current_status_robot = _data_robot_status["robot_status"]
        self.get_logger().info('_data_robot_status: "%s"' % _data_robot_status)

    def robot_control_seer_srv(self, request, response):

        # request_example = {"api": 2000, "request_body": {}}
        _request = eval(request.msg_request)
        _response = self.sent_api_seer(
            self.control_connect_socket,
            _request["api"],
            _request["request_body"],
        )
        # _sent_modbus = self.writeValue(
        #     _value_req["address"],
        #     _value_req["value"],
        #     _value_req["slave"],
        # )
        # self.get_logger().info('_value_req: "%s"' % _request["address"])
        data_response = _response
        response.msg_response = str(data_response)
        return response

    def navigation_seer_srv(self, request, response):

        # request_example = {"api": 2000, "request_body": {}}
        _request = eval(request.msg_request)
        # _response = self.sent_api_seer(
        #     self.navigation_connect_socket,
        #     _request["api"],
        #     _request["request_body"],
        # )

        self.get_logger().info('_request: "%s"' % _request)
        data_response = {"connect": "asdasd"}
        response.msg_response = str(data_response)
        return response

    def processing_modbus_client(self, _request_body):
        req = CommonRequest.Request()
        while not self.cli_client_communication_modbus.wait_for_service(
            timeout_sec=1.0
        ):
            self.get_logger().info("service not available, waiting again...")
            return False

        req.msg_request = str(_request_body)
        future = self.cli_client_communication_modbus.call_async(req)
        while rclpy.ok():
            if future.done() and future.result():
                return future.result()

        return None

    def read_seer_response(self):
        msg = String()

        _value = self.sent_api_seer(
            self.status_connect_socket, status.robot_status_all1_req, self.key_seer
        )
        msg.data = str(_value)
        self.seer_response_publisher_.publish(msg)
        # self.get_logger().info('_value: "%s"' % _value)

    def main_loop(self):
        # self.read_seer_response()
        pass


def main(args=None):
    rclpy.init(args=args)

    communication_socker_seer = SockerControlSeer()
    executor = MultiThreadedExecutor()
    executor.add_node(communication_socker_seer)
    executor.spin()

    rclpy.shutdown()


if __name__ == "__main__":
    main()
