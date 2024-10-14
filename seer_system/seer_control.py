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
        self.seer_status = {}
        self.robot_information = {}
        self._action_list = []
        self.robot_mode = True
        self.robot_error = False
        self.robot_safety_error = False
        self.action_activity = ""
        self.mission_robot = None
        self._url_sever = "http://192.168.1.7:5000/"

        # robot_mode = True // == auto  or false == manual

        self.robot_status = None
        self.robot_status_publisher_ = self.create_publisher(String, "robot_status", 10)
        self.subscription_seer_response = self.create_subscription(
            String, "seer_response", self.seer_callback, 10
        )
        self.subscription_seer_response

        @app.post("/sent_mission")
        async def sent_mission(mission_had_sent: dict):
            # self.send_goal(mission_occupy)
            # self.send_goal(mission_occupy)
            if not self._step_mission:
                activity_mission = self.check_mission_activities(mission_had_sent)
                # self.get_logger().info('activity_mission: "%s"' % (activity_mission))
                if not activity_mission["run_misison"]:
                    return {"code": 0}
                # self._action_list = activity_mission["mission"]
                return {"call mission success"}
            return {"robot have mission"}

        @app.post("/clear_action")
        async def clear_action(clear_action: bool):
            if clear_action:
                self._action_list = []
                self.action_activity = ""
                self.robot_error = False
            return {"clear success"}

        @app.post("/change_robot_mode")
        async def clear_action(mode_status: bool):
            self.robot_mode = mode_status
            if mode_status:
                return {"robot_mode": "auto"}
            # if clear_action:
            #     self._action_list = []
            #     self.action_activity = ""
            #     self.robot_error = False
            return {"robot_mode": "manual"}

    def check_mission_activities(self, mission):

        # _list_mission = list(self._dict_mission.values())[0]
        # self._step_mission = len(_list_mission)
        if not mission["activity_type"] and not self.robot_mode:
            return {"run_misison": True, "mission": mission["actions"]}
        elif mission["activity_type"] and self.robot_mode:
            _dict_request_misison = {
                "excute_code": mission["excute_code"],
                "mission_code": mission["mission_code"],
            }
            self.mission_robot = mission["mission_code"]
            request_sever = self.post_sever_request(
                "robot_comfirm_mission", _dict_request_misison
            )
            self.get_logger().info('request_sever: "%s"' % (request_sever))

            return {"run_misison": True, "mission": mission["actions"]}

        return {"run_misison": False, "mission": None}

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
            self.action_activity = _n_value

            # for key, parameter_req in self._dict_mission.items():
            #     self._action_client = ActionClient(
            #         self, Fibonacci, parameter_req[0]["name"]
            #     )
            #     _n_value = parameter_req[0]["params"]["number"]
            # self.get_logger().info('value: "%s"' % _n_value["msg"])
            self.get_logger().info('_n_value: "%s"' % ((_n_value)))

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

    def robot_error_process(self):
        # self.mission_robot = None
        if self.robot_error:
            self.get_logger().info('robot_error: "%s"' % (self.robot_error))

    def seer_callback(self, msg):
        _seer_msg = eval(msg.data)
        self.seer_status = _seer_msg
        # self.get_logger().info('dict_order: "%s"' % (dict_order["number"]))

    def pub_robot_status(self):
        msg = String()
        _msg = {"robot_status": self.robot_status, "robot_mode": self.robot_mode}
        msg.data = str(_msg)
        self.robot_status_publisher_.publish(msg)

    def post_sever_request(self, _url, _request_body):

        # request_body = {
        #     # "robot_code": "robot_2",
        #     "position_collision": ["dasd"],
        #     "map_code": "pickup_locations",
        # }
        self.get_logger().info('_url_sever: "%s"' % str(self._url_sever + _url))

        try:
            # res = requests.post(
            #     str(self._url_sever + _url),
            #     headers=self.__token_gw,
            #     json=_request_body,
            #     timeout=4,
            # )
            # response = res.json()
            # if not response:
            #     return None
            return True
            return response
        except Exception as e:
            return None

    def main_processing(self) -> None:
        if bool(self.seer_status):
            if (
                self.seer_status["emergency"]
                or self.seer_status["blocked"]
                or self.robot_error
            ):
                _robot_safety_error = True
                self.robot_status = "ERROR"
            if self.seer_status["battery_level"] < 40:
                self.robot_status = "LOW_BATERY"
                _robot_low_batery = True
            if not _robot_safety_error and not _robot_low_batery:
                _robot_safety_error = False
                _robot_low_batery = False
                if self._step_mission != 0:
                    self.robot_status = "RUN"
                else:
                    self.robot_status = "IDLE"
                    self.mission_robot = None
                # if  self.seer_status["battery_level"]

        _dict_request_misison = {}
        request_sever = self.post_sever_request(
            "update_robot_status", _dict_request_misison
        )

        self.robot_error_process()

    def main_loop(self) -> None:
        # pass

        self._step_mission = len(self._action_list)
        # self.main_processing()
        if self._step_mission != 0:
            # self.robot_error_process()
            self.parse_mission()
        # else:
        self._misison_task = self._step_mission
        self._pre_n_mission = self._step_mission
        self.pub_robot_status()
        # self._pre_n_mission = self._step_mission
        # self.get_logger().info('_pre_n_mission: "%s"' % (self._pre_n_mission))
        # self.get_logger().info('_step_mission: "%s"' % (self._step_mission))

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
