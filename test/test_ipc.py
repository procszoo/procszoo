# test_ipc.py
# IPC Support for Procszoo
# Copyright (C) 2016 Rayson Zhu <vfreex+procszoo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import json
import unittest

from procszoo.ipc.jsonrpc import JSONRPCRequest, JSONRPCResponse
from procszoo.ipc.netlink import NetlinkMessageHeader, NetlinkMessage
from procszoo.ipc.procslink import ProcslinkMessageHeader, ProcslinkMessage


class JSONRPCTestCase(unittest.TestCase, object):
    def test_JSONRPCRequest_create_not_notification(self):
        JSONRPCRequest(None, "foo")
        JSONRPCRequest(1, "foo")
        JSONRPCRequest("", "foo")
        JSONRPCRequest("1", "foo")
        JSONRPCRequest("1", "foo", [])
        JSONRPCRequest("1", "foo", ())
        JSONRPCRequest("1", "foo", {})
        with self.assertRaises(TypeError):
            JSONRPCRequest([], "foo")
        with self.assertRaises(TypeError):
            JSONRPCRequest(1.0, "foo")
        with self.assertRaises(TypeError):
            JSONRPCRequest(1.0, "foo", params=1)
        with self.assertRaises(TypeError):
            JSONRPCRequest(1.0, "foo", params="")

    def test_JSONRPCRequest_create_notification(self):
        JSONRPCRequest(None, method="foo", is_notification=True)
        with self.assertRaises(ValueError):
            JSONRPCRequest(1, method="foo", is_notification=True)

    def test_JSONRPCRequest_to_json(self):
        rpc_req = JSONRPCRequest(2333, "foo", params=[1, "abc", True])
        rpc_req_json = rpc_req.to_json()
        rpc_req_json_dict_actual = json.loads(rpc_req_json)
        rpc_req_json_dict_expect = {"method": "foo", "params": [1, "abc", True], "id": 2333, "jsonrpc": "2.0"}
        self.assertEqual(rpc_req_json_dict_expect, rpc_req_json_dict_actual)

        rpc_req2 = JSONRPCRequest.from_json(rpc_req_json)
        rpc_req_json_dict_actual2 = json.loads(rpc_req2.to_json())
        self.assertEqual(rpc_req_json_dict_expect, rpc_req_json_dict_actual2)

    def test_JSONRPCResponse_to_json(self):
        rpc_res = JSONRPCResponse(2333, result=[1, "abc", True])
        rpc_res_json = rpc_res.to_json()
        rpc_res_json_dict_actual = json.loads(rpc_res_json)
        rpc_res_json_dict_expect = {"result": [1, "abc", True], "id": 2333, "jsonrpc": "2.0"}
        self.assertEqual(rpc_res_json_dict_expect, rpc_res_json_dict_actual)

        rpc_res2 = JSONRPCResponse.from_json(rpc_res_json)
        rpc_res_json_dict_actual2 = json.loads(rpc_res2.to_json())
        self.assertEqual(rpc_res_json_dict_expect, rpc_res_json_dict_actual2)


class ProcslinkTestCase(unittest.TestCase, object):
    def test_procszlink_to_json_and_from_json(self):
        msg1 = ProcslinkMessage(ProcslinkMessageHeader(), b'abc123')
        msg2 = ProcslinkMessage.from_bytes(msg1.to_bytes())
        self.assertEqual(msg1.to_bytes(), msg2.to_bytes())


class NetlinkTestCase(unittest.TestCase, object):
    def test_netlink_to_json_and_from_json(self):
        msg1 = NetlinkMessage(NetlinkMessageHeader(), b'abc123')
        msg2 = NetlinkMessage.from_bytes(msg1.to_bytes())
        self.assertEqual(msg1.to_bytes(), msg2.to_bytes())

import logging
import sys
import os
from procszoo.ipc import RPCPeer
logging.basicConfig(level=logging.DEBUG)

def hello(name):
    print("Hello %s!" % name)
    return "Hello %s!" % name


class RPCTestCase(unittest.TestCase):
    def setUp(self):
        self.server = RPCPeer()
        pid = os.fork()
        if pid == 0:
            self.server.register_function(hello)
            self.server.run_server_forever()
        self.server_pid = pid
        #os.system("sleep 1")

    def test_rpc_call(self):
        client = RPCPeer()
        client.talk_to(self.server.nl_pid).hello("IPC")

    def tearDown(self):
        os.kill(self.server_pid, 9)
        os.waitpid(self.server_pid, 0)

if __name__ == '__main__':
    unittest.main()




