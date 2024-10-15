import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

# from action_tutorials_interfaces.action import Fibonacci
# from action_tutorials_interfaces.action import Fibonacci
from action_interfaces_msg.action import Fibonacci
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
import asyncio
import sys
import serial

#add logging capability
import logging

import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_rtu as modbus_rtu

from std_msgs.msg import String
from robot_interfaces.srv import CommonRequest


class ModbusProcess(Node):

    def __init__(self):
        super().__init__("modbus_comunication")
        self.timer_cb = MutuallyExclusiveCallbackGroup()

        self.timer = self.create_timer(
            1.0, self.main_loop, callback_group=self.timer_cb
        )
        self.sensor_lift_publisher_ = self.create_publisher(
            String, "lifting_sensor", 10
        )
        self.srv_get_mission = self.create_service(
            CommonRequest, "modbus_communication", self.modbus_contact_srv
        )

        self.port = "/dev/ttyUSB0"
        self.initial_protocol()

    def initial_protocol(self):
        if self.connect_serial():
            pass

    def connect_serial(self):
        try:
            self.target = modbus_rtu.RtuMaster(serial.Serial(port=self.port, baudrate=115200, bytesize=8, parity='N', stopbits=1, xonxoff=0))
            # self.target.serve_forever()
             self.target.set_timeout(5.0)
             self.target.set_verbose(True)
            # self.target.connect()
            return True
            # Robot.error = None
            # handleLog(f"RTU Master connect Success", type=log)
        except Exception as E:
            msg = f"Connect RTU Master Fail"
            # handleLog(msg, type="A")
            # Robot.error = msg
            time.sleep(2)
            self.connect_serial()

    def readValue(self, _dress: int, _count: int, _slave: int):
        # if self.target.is_socket_open():
        try:
            # result = self.target.read_holding_registers(
            #     address=address, count=count, slave=slave
            # )
            result = self.target.execute(_slave, cst.READ_HOLDING_REGISTERS, _dress, _count)
            if not result.isError():
                msg = ""
                for index, value in enumerate(result.registers):
                    msg = msg + str(address + index) + ":" + str(value) + ", "
                # Robot.error = None
                # handleLog(f"RTU Master read: {msg} success")
                return result.registers
            elif result.isError():
                msg = f"RTU Master read address: {address}, count: {count}, slave: {slave} error"
        except:
            pass

    def robot_read_input_registers(self, _address: int, _count: int, _slave: int):
        try:
            # result = self.target.read_input_registers(
            #     address=_address, count=_count, slave=_slave
            # )
            result = master.execute(_slave, cst.READ_INPUT_REGISTERS, _address, _count)
            return result
            # _sensor_up = result.registers[0]
            # _sensor_down = result.registers[1]
        except:
            return None

    def writeValue(self, _address: int, _value: int, _slave: int):
        # if self.target.is_socket_open():
        try:
            # result = self.target.write_register(
            #     address=_address, value=_value, slave=_slave
            # )
             result = self.targe.execute(_slave, cst.WRITE_SINGLE_REGISTER, _address, output_value=_value)
            return = True
        
        except modbus_tk.modbus.ModbusError as exc:
            return = False

    def modbus_contact_srv(self, request, response):
        _value_req = eval(request.msg_request)
        _respon_modbus = self.writeValue(
            _value_req["address"],
            _value_req["value"],
            _value_req["slave"],
        )
        self.get_logger().info('_sent_modbus: "%s"' % _respon_modbus)
        data_response = {"code": _respon_modbus}
        response.msg_response = str(data_response)
        return response

    def pub_sensor_(self):
        _read_sensor_lift = self.robot_read_input_registers(5, 2, 1)

        msg = String()
        _msg = {
            "sensor_up": _read_sensor_lift.registers[0],
            "sensor_down": _read_sensor_lift.registers[1],
        }
        # _msg = {
        #     "sensor_up": 0,
        #     "sensor_down": 0,
        # }
        msg.data = str(_msg)
        self.sensor_lift_publisher_.publish(msg)

    def check_connect_mobbus(self):
        if self.target.is_socket_open():
            pass
        else:
            self.connect_serial()

    def main_loop(self):
        # pass
        # self.check_connect_mobbus()
        self.pub_sensor_()


def main(args=None):
    rclpy.init(args=args)

    modbus_comunication = ModbusProcess()
    executor = MultiThreadedExecutor()
    executor.add_node(modbus_comunication)
    executor.spin()

    rclpy.shutdown()


if __name__ == "__main__":
    main()
