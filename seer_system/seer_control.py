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

from action_interfaces_msg.action import Fibonacci, Mission

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
        self._step_mission = 0
        self._pre_n_mission = 0
        self._misison_task = 0
        self._dict_mission = {}
        self._action_list = []
        self.robot_mode = True
        self.robot_error = False

        # robot_mode = True // == auto  or false == manual

        self.robot_status = "run"
        self.robot_status_publisher_ = self.create_publisher(String, "robot_status", 10)

        @app.post("/sent_mission")
        async def sent_mission(mission_had_sent: dict):
            # self.send_goal(mission_occupy)
            # self.send_goal(mission_occupy)
            # if not self._step_mission:
            activity_mission = self.comfirm_misison(mission_had_sent)
            self._action_list = activity_mission
            # self._dict_mission = mission_occupy
            # self.occupy_mission()
            # self._misison_task = 0
            # return {"call mission success"}
            return {"robot have mission"}

            # for key, value in mission_occupy.items():
            #     pass

    def comfirm_misison(self, mission):

        # _list_mission = list(self._dict_mission.values())[0]
        # self._step_mission = len(_list_mission)
        if mission["activity_type"]:
            # comfirm mission to fleet
            pass
        return mission["actions"]

    def parse_mission(self):

        # while self._step_mission != 0:
        # self.get_logger().info('_dict_mission: "%s"' % ("asdasd"))
        if self._pre_n_mission != self._step_mission:
            # self._step_mission = self._step_mission - 1
            # self.get_logger().info('_dict_mission: "%s"' % (self._dict_mission))
            self._misison_task = self._misison_task + 1

            self.get_logger().info('self.flag on looop : "%s"' % (self._step_mission))
            self._action_client = ActionClient(
                self, Mission, self._action_list[0]["name"]
            )
            _n_value = str(self._action_list[0]["params"])

            # for key, parameter_req in self._dict_mission.items():
            #     self._action_client = ActionClient(
            #         self, Fibonacci, parameter_req[0]["name"]
            #     )
            #     _n_value = parameter_req[0]["params"]["number"]
            # self.get_logger().info('value: "%s"' % _n_value["msg"])
            # self.get_logger().info('_n_value: "%s"' % json.loads((_n_value)))

            self.send_goal(_n_value)
            self._pre_n_mission = self._step_mission

        # pass

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
            self.get_logger().info("Result: {0}".format(result.success))
            # if lenresult.success:
            self.robot_error = False
            self._action_list.pop(0)
        else:
            self.robot_error = True
            # self.get_logger().info("Result: {0}".format(result.success))

            # self._pre_n_mission = self._step_mission
        # for key, value in self._dict_mission.items():
        #     # self._action_client = ActionClient(self, Fibonacci, value[0]["params"])
        #     value.pop(0)
        # self.flag = False

    def robot_error_process(self):
        if self.robot_error:
            for key, parameter_req in self._dict_mission.items():
                # self._action_client = ActionClient(
                #     self, Fibonacci, parameter_req[0]["name"]
                # )
                self.get_logger().info("parameter_req: {0}".format(parameter_req))

    def pub_robot_status(self):
        msg = String()
        _msg = {"robot_status": self.robot_status, "robot_mode": self.robot_mode}
        msg.data = str(_msg)
        self.robot_status_publisher_.publish(msg)

    def main_loop(self) -> None:
        # pass

        self._step_mission = len(self._action_list)
        if self._step_mission != 0:
            # self._pre_n_mission = 0
            # self.robot_error_process()
            self.parse_mission()
        else:
            self._misison_task = self._step_mission
            self._pre_n_mission = self._step_mission

        self.pub_robot_status()
        # self._pre_n_mission = self._step_mission
        self.get_logger().info('_pre_n_mission: "%s"' % (self._pre_n_mission))
        self.get_logger().info('_n_mission: "%s"' % (self._step_mission))

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
