import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from robot_interfaces.srv import CommonRequest
from std_msgs.msg import String
from action_interfaces_msg.action import Fibonacci, Mission
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.action import ActionServer
from rclpy.action import CancelResponse
from rclpy.action import GoalResponse
from seer_system.api import navigation
import requests


class NavigationControlSeer(Node):

    def __init__(self):
        super().__init__("action_navigation_seer")
        self.timer_cb = MutuallyExclusiveCallbackGroup()

        self.timer = self.create_timer(
            2.0, self.main_loop, callback_group=self.timer_cb
        )

        # self._action_server = ActionServer(
        #     self, Mission, "action_navigation", self.execute_callback
        # )
        self._action_server = ActionServer(
            self,
            Mission,
            "action_navigation",
            execute_callback=self.execute_callback,
            callback_group=ReentrantCallbackGroup(),
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
        )

        self.cli_client_navigation_api = self.create_client(
            CommonRequest, "navigation_seer_api"
        )
        self.current_position = "LM33"
        self.seer_response_subscription_ = self.create_subscription(
            String, "seer_response", self.seer_callback, 10
        )
        self.seer_response_subscription_

    def goal_callback(self, goal_request):
        # Accepts or rejects a client request to begin an action
        self.get_logger().info("Received goal request :)")
        self.goal = goal_request
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        # Accepts or rejects a client request to cancel an action
        self.get_logger().info("Received cancel request :(")
        return CancelResponse.ACCEPT

    async def execute_callback(self, goal_handle):
        self.get_logger().info("Executing goal...")

        feedback_msg = Mission.Feedback()

        request_order = eval(goal_handle.request.order)
        _destination = request_order["position"]
        resquest_seer = {
            "seer_api": navigation.robot_task_gotarget_req,
            "request": {"id": _destination},
        }
        sent_api_goal = self.processing_modbus_client(resquest_seer)
        self.get_logger().info('position: "%s"' % (request_order["position"]))
        goal_handle.succeed()
        result = Mission.Result()

        if _destination != self.current_position:
            self.get_logger().info('false position: "%s"' % (_destination))
            result.success = False
        else:
            result.success = True

        # {"id": "lm23"}
        # time.sleep(2)
        # sent_api_seer = goal_handle.request.order["position"]

        # feedback_msg.operating_status = sent_api_seer

        # for i in range(1, goal_handle.request.order):
        #     feedback_msg.partial_sequence.append(
        #         feedback_msg.partial_sequence[i] + feedback_msg.partial_sequence[i - 1]
        #     )
        #     self.get_logger().info(
        #         "Feedback: {0}".format(feedback_msg.partial_sequence)
        #     )
        #     goal_handle.publish_feedback(feedback_msg)
        #     time.sleep(1)
        feedback_msg.operating_status = "sent_api_seer"
        goal_handle.publish_feedback(feedback_msg)
        return result

    def check_target(self, data_status: dict, target: str):
        # time.sleep(1)
        if data_status["task_status"] == 4:
            if (data_status["current_station"]) == target:
                return True
            else:
                return False
        else:
            return False

    def processing_modbus_client(self, _request_body):
        req = CommonRequest.Request()
        while not self.cli_client_navigation_api.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("service not available, waiting again...")
            return False

        req.msg_request = str(_request_body)
        future = self.cli_client_navigation_api.call_async(req)
        while rclpy.ok():
            if future.done() and future.result():
                return future.result()

        return None

    def seer_callback(self, msg):
        _seer_msg = msg.data

    def comfirm_moving_collision(self):
        request_body = {
            # "robot_code": "robot_2",
            "position_collision": ["Tmh"],
            "map_code": "pickup_location",
        }
        try:
            res = requests.post(
                self.__url_gw + self.__device_control + self.__device_call,
                headers=self.__token_gw,
                json=request_body,
                timeout=4,
            )
            response = res.json()
            if not response:
                return None

            return response
        except Exception as e:
            return None

    def main_loop(self):
        pass
        # self.comfirm_moving_collision()
        # response_modbus = self.frame_sent_modbus("up")
        # self.get_logger().info('response_modbus: "%s"' "loop run")


def main(args=None):
    rclpy.init(args=args)

    action_navigation_seer = NavigationControlSeer()
    executor = MultiThreadedExecutor()
    rclpy.spin(action_navigation_seer, executor=executor)

    # executor.add_node(action_navigation)
    # executor.spin()

    rclpy.shutdown()


if __name__ == "__main__":
    main()
