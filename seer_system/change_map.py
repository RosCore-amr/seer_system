import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from datetime import datetime, timedelta, timezone

# from action_tutorials_interfaces.action import Fibonacci
# from action_tutorials_interfaces.action import Fibonacci
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from robot_interfaces.srv import CommonRequest
from std_msgs.msg import String
from action_interfaces_msg.action import Mission

from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.action import ActionServer
from rclpy.action import CancelResponse
from rclpy.action import GoalResponse


class ChangeMap(Node):

    def __init__(self):
        super().__init__("action_change_map_seer")
        self.timer_cb = MutuallyExclusiveCallbackGroup()

        self.timer = self.create_timer(
            2.0, self.main_loop, callback_group=self.timer_cb
        )

        self._action_server = ActionServer(
            self,
            Mission,
            "action_change_map",
            execute_callback=self.execute_callback,
            callback_group=ReentrantCallbackGroup(),
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
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
        self.status_lift_up = True
        self.status_lift_down = True
        self.time_now = datetime.now(timezone.utc)

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

    def goal_callback(self, goal_request):
        # Accepts or rejects a client request to begin an action
        self.get_logger().info("Received goal request :)")
        self.goal = goal_request
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        # Accepts or rejects a client request to cancel an action
        self.get_logger().info("Received cancel request :(")
        return CancelResponse.ACCEPT

    def target_status_lift(self, goal_lif):
        if goal_lif == "up":
            return self.status_lift_up
        elif goal_lif == "down":
            return self.status_lift_down
        else:
            return False

    async def execute_callback(self, goal_handle):
        self.get_logger().info("Executing goal...")

        # feedback_msg = Fibonacci.Feedback()
        feedback_msg = Mission.Feedback()
        request_order = eval(goal_handle.request.order)
        # self.get_logger().info('request_order: "%s"' % (request_order))
        lift_request = request_order["lift"]
        _timeout = int(request_order["timeout"])
        # response_modbus = self.frame_sent_modbus(lift_request)
        expire = datetime.now(timezone.utc) + timedelta(seconds=_timeout)
        self.get_logger().info('time out : "%s"' % (_timeout))
        _time_sleep = True
        while _time_sleep:
            # self.get_logger().info('sleep time : "%s"' % (self.time_now))
            if self.time_now > expire:
                _time_sleep = False
                _result_lift = self.target_status_lift(lift_request)
                self.get_logger().info('_result_lift : "%s"' % (_result_lift))

        goal_handle.succeed()

        result = Mission.Result()
        result.success = _result_lift
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
        self.time_now = datetime.now(timezone.utc)
        # response_modbus = self.frame_sent_modbus("up")
        # self.get_logger().info('response_modbus: "%s"' % response_modbus)


def main(args=None):
    rclpy.init(args=args)

    action_change_map_seer = ChangeMap()
    executor = MultiThreadedExecutor()
    executor.add_node(action_change_map_seer)
    executor.spin()

    rclpy.shutdown()


if __name__ == "__main__":
    main()
