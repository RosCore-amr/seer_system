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
import requests
from rclpy.action import ActionClient


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
        self.seer_response_subscription_ = self.create_subscription(
            String, "seer_response", self.seer_callback, 10
        )
        self._action_client = ActionClient(self, Mission, "action_navigation")
        self.current_map = "pickup_location_xx"
        self._next_step = False
        self.initial_protocol()

    def initial_protocol(self):
        pass

    def goal_callback(self, goal_request):
        # Accepts or rejects a client request to begin an action
        self.get_logger().info("Received goal request")
        self.goal = goal_request
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        # Accepts or rejects a client request to cancel an action
        self.get_logger().info("Received cancel request :")
        return CancelResponse.ACCEPT

    async def execute_callback(self, goal_handle):
        self.get_logger().info("Executing goal...")

        # feedback_msg = Fibonacci.Feedback()
        feedback_msg = Mission.Feedback()
        request_order = eval(goal_handle.request.order)
        self.get_logger().info('request_order: "%s"' % (request_order))
        map_request = request_order["arrival_map"]
        # _timeout = int(request_order["timeout"])
        goal_handle.succeed()
        result = Mission.Result()
        if map_request == self.current_map:
            result.success = True
            return result

        _elevator_and_change_map = False
        while not _elevator_and_change_map:
            request_body = str({"msg": "Mission", "position": "LM33", "timeout": 0.5})
            sent_goal = self.send_goal(request_body)
            if self._next_step:
                self._next_step = False
                _elevator_and_change_map = True

        result.success = True
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

    def post_data_api(self, url, value):
        try:
            res = requests.post(
                url,
                json=value,
                # headers=self.token,
                timeout=3,
            )

            response_post_data = res.json()
            return response_post_data
        except Exception as e:
            print("error update status mission")
        return False

    def send_goal(self, order):
        goal_msg = Mission.Goal()
        dict_order = eval(order)
        # self.get_logger().info('dict_order: "%s"' % (dict_order["number"]))

        goal_msg.order = order

        self._action_client.wait_for_server()
        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info("Goal rejected :(")
            return

        # self.get_logger().info("Goal accepted :)")

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        # self.get_logger().info("Result: {0}".format(result.success))
        if result.success:
            self._next_step = True

    def seer_callback(self, msg):
        _seer_msg = msg.data

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
