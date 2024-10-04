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


class LiftControlSeer(Node):

    def __init__(self):
        super().__init__("lift_seer_control")
        self.timer_cb = MutuallyExclusiveCallbackGroup()

        self.timer = self.create_timer(
            2.0, self.main_loop, callback_group=self.timer_cb
        )

        self._action_server = ActionServer(
            self, Fibonacci, "fibonacci", self.execute_callback
        )
        self.option = {"up": 2, "down": 1}
        self.modbus_register = 1
        self.cli_client_communication_modbus = self.create_client(
            CommonRequest, "modbus_communication"
        )
        self.subscription_sensor_lift = self.create_subscription(
            String, "lifting_sensor", self.sensor_lift_callback, 1
        )
        self.subscription_sensor_lift  # prevent unused variable warning
        self.sensor_up = 0
        self.sensor_down = 0
        self.status_lift_up = False
        self.status_lift_down = False

        self.initial_protocol()

    def initial_protocol(self):
        pass

    def sensor_lift_callback(self, msg):
        _sensor_lift = eval(msg.data)
        self.sensor_up = _sensor_lift["sensor_up"]
        self.sensor_down = _sensor_lift["sensor_down"]
        self.status_lift_up = bool(self.sensor_up and not self.sensor_down)
        self.status_lift_down = bool(self.sensor_down and not self.sensor_up)
        # self.get_logger().info('_sensor_lift: "%s"' % _sensor_lift)
        # self.get_logger().info('status_lift_up: "%s"' % self.status_lift_up)
        # self.get_logger().info('status_lift_down: "%s"' % self.status_lift_down)

    def execute_callback(self, goal_handle):
        self.get_logger().info("Executing goal...")

        feedback_msg = Fibonacci.Feedback()
        feedback_msg.partial_sequence = [0, 1]

        for i in range(1, goal_handle.request.order):
            feedback_msg.partial_sequence.append(
                feedback_msg.partial_sequence[i] + feedback_msg.partial_sequence[i - 1]
            )
            self.get_logger().info(
                "Feedback: {0}".format(feedback_msg.partial_sequence)
            )
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(1)

        goal_handle.succeed()

        result = Fibonacci.Result()
        result.sequence = feedback_msg.partial_sequence
        return result

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

    def frame_sent_modbus(self, _option):

        _modbus_req = {
            "address": self.modbus_register,
            "value": self.option[_option],
            "slave": 1,
        }
        modbus_response = self.processing_modbus_client(_modbus_req)
        _modbus_response = eval(modbus_response.msg_response)
        return _modbus_response

    def main_loop(self):
        pass
        # response_modbus = self.frame_sent_modbus("up")
        # self.get_logger().info('response_modbus: "%s"' % response_modbus)


def main(args=None):
    rclpy.init(args=args)

    lift_seer_control = LiftControlSeer()
    executor = MultiThreadedExecutor()
    executor.add_node(lift_seer_control)
    executor.spin()

    rclpy.shutdown()


if __name__ == "__main__":
    main()
