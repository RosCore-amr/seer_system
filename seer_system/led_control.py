import time

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


class LedControlSeer(Node):

    def __init__(self):
        super().__init__("led_control_seer")
        self.timer_cb = MutuallyExclusiveCallbackGroup()

        self.timer = self.create_timer(
            2.0, self.main_loop, callback_group=self.timer_cb
        )

        self.modbus_register = 0
        self.cli_client_communication_modbus = self.create_client(
            CommonRequest, "modbus_communication"
        )
        self.subscription_sensor_lift = self.create_subscription(
            String, "robot_status", self.robot_status_callback, 1
        )
        self.option = {
            "1": 1,
            "green": 2,
            "blue_green_font": 3,
            "blue_green_rear": 4,
            "blue_green_2_4": 5,
            "blue_green_1_3": 6,
            "blue_flash": 7,
            "red": 8,
            "red_flash": 9,
            "yellow": 10,
            "yellow_flash": 11,
            "white": 12,
            "green_flash": 13,
            "blue_sky": 14,
            "violet": 15,
            "yellow_nhat": 16,
        }
        self.current_status_robot = None
        self.pre_status_robot = None
        self.initial_protocol()

    def initial_protocol(self):
        pass

    def robot_status_callback(self, msg):
        _data_robot_status = eval(msg.data)
        self.current_status_robot = _data_robot_status["robot_status"]
        self.get_logger().info('_data_robot_status: "%s"' % _data_robot_status)

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

    def frame_sent_modbus(self, _optiopn):

        _modbus_req = {
            "address": self.modbus_register,
            "value": self.option[_optiopn],
            "slave": 1,
        }
        modbus_response = self.processing_modbus_client(_modbus_req)
        _modbus_response = eval(modbus_response.msg_response)
        return _modbus_response

    def main_loop(self):

        light_set = "white"
        if self.current_status_robot == "emergency":
            light_set = "red"
        elif self.current_status_robot == "run":
            light_set = "green"

        if self.pre_status_robot != self.current_status_robot:
            # response_modbus = self.frame_sent_modbus(light_set)
            self.pre_status_robot = self.current_status_robot
        self.get_logger().info('_resutl: "%s"' % self.current_status_robot)


def main(args=None):
    rclpy.init(args=args)

    led_control_seer = LedControlSeer()
    executor = MultiThreadedExecutor()
    executor.add_node(led_control_seer)
    executor.spin()

    rclpy.shutdown()


if __name__ == "__main__":
    main()
