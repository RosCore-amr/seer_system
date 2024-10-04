#!/usr/bin/env python
# -*- coding: utf-8 -*-

import jwt
import uvicorn
import requests
import yaml
import json
from fastapi import FastAPI, Request
from pydantic import BaseModel
import threading

from example_interfaces.srv import AddTwoInts
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from robot_interfaces.srv import (
    CreatMission,
    SearchStock,
    ExcuteMission,
    CommandApi,
    Collision,
    GetInformation,
)
from robot_interfaces.msg import MissionTransport, MissionCurrent
from fastapi.middleware.cors import CORSMiddleware

from action_interfaces_msg.action import Fibonacci

from rclpy.action import ActionClient


app = FastAPI(
    title="Robot API",
    openapi_url="/openapi.json",
    docs_url="/docs",
    description="controlsystem",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SumResponse(BaseModel):
    sum: int


class SeerControl(Node):
    def __init__(self):
        super().__init__("mission_process_client_async")

        self.timer_cb = MutuallyExclusiveCallbackGroup()

        self.timer = self.create_timer(
            1.0, self.main_loop, callback_group=self.timer_cb
        )
        # self._action_client = ActionClient(self, Fibonacci, "fibonacci")
        self.flag = False
        self._n_mission = 0
        self._pre_n_mission = 0
        self._misison_task = 0
        self._dict_mission = {}
        self._action_list = []
        self.robot_mode = True
        # robot_mode = True // == auto  or false == manual

        self.robot_status = "IDE"

        @app.post("/sent_mission")
        async def sent_mission(mission_had_sent: dict):
            # self.send_goal(mission_occupy)
            # self.send_goal(mission_occupy)
            if not self._n_mission:
                activity_mission = self.comfirm_misison(mission_had_sent)
                self._action_list = activity_mission
                # self._dict_mission = mission_occupy
                # self.occupy_mission()
                # self._misison_task = 0
                return {"call mission success"}
            return {"robot have mission"}

            # for key, value in mission_occupy.items():
            #     pass

    def comfirm_misison(self, mission):

        # _list_mission = list(self._dict_mission.values())[0]
        # self._n_mission = len(_list_mission)
        if mission["activity_type"]:
            # comfirm mission to fleet
            pass
        return mission["actions"]

    def parse_mission(self):

        # while self._n_mission != 0:
        self.get_logger().info('_dict_mission: "%s"' % ("asdasd"))
        if self._pre_n_mission != self._n_mission:
            # self._n_mission = self._n_mission - 1
            # self.get_logger().info('_dict_mission: "%s"' % (self._dict_mission))
            self._misison_task = self._misison_task + 1

            self.get_logger().info('self.flag on looop : "%s"' % (self._n_mission))
            self._action_client = ActionClient(
                self, Fibonacci, self._action_list[0]["name"]
            )
            _n_value = self._action_list[0]["params"]["number"]

            # for key, parameter_req in self._dict_mission.items():
            #     self._action_client = ActionClient(
            #         self, Fibonacci, parameter_req[0]["name"]
            #     )
            #     _n_value = parameter_req[0]["params"]["number"]
            #     self.get_logger().info('value: "%s"' % _n_value)

            self.send_goal(_n_value)
            self._pre_n_mission = self._n_mission

        # pass

    def send_goal(self, order):
        goal_msg = Fibonacci.Goal()
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
        # self.get_logger().info("Result: {0}".format(result.sequence))

        if len(result.sequence) != 0:
            self._action_list.pop(0)
            # for key, value in self._dict_mission.items():
            #     # self._action_client = ActionClient(self, Fibonacci, value[0]["params"])
            #     value.pop(0)
            # self.flag = False

    def main_loop(self) -> None:
        # pass

        self._n_mission = len(self._action_list)
        if self._n_mission != 0:
            self.parse_mission()
        else:
            self._misison_task = self._n_mission
        self.get_logger().info('_action_list: "%s"' % (self._action_list))
        self.get_logger().info('_n_mission: "%s"' % (self._n_mission))

    def msg2json(self, msg):
        # y = json.load(str(msg))
        return json.dumps(msg, indent=4)


def main(args=None):
    rclpy.init(args=args)

    seer_control = SeerControl()

    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(seer_control)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()
    seer_control.get_logger().info("Swagger run http://127.0.0.0:7200/docs#/")

    uvicorn.run(app, host="0.0.0.0", port=7200, log_level="warning")
    seer_control.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()
