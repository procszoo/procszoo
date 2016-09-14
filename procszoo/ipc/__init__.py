# __init__.py
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

from __future__ import absolute_import, unicode_literals, print_function

import inspect
import logging
import os
import socket

from future.builtins import int, str

from procszoo.ipc.jsonrpc import JSONRPCRequest, JSONRPCResponse, JSONRPCError, JSONRPCMethodNotFoundError, \
    JSONRPCInternalError
from procszoo.ipc.netlink import NetlinkMessage, NetlinkMessageHeader
from procszoo.ipc.procslink import ProcslinkMessage, ProcslinkMessageHeader

LOGGER = logging.getLogger(__name__)


class AbstractRPCRequestDispatcher(object):
    def handle_request(self, procslink_message, functions):
        raise NotImplementedError()


class JSONRPCRequestDispatcher(AbstractRPCRequestDispatcher, object):
    def handle_request(self, procslink_message, functions):
        # type: (ProcslinkMessage, dict) -> ProcslinkMessage
        if procslink_message.header.payload_type != ProcslinkMessageHeader.PAYLOAD_TYPE_JSONRPC2_REQUEST:
            raise ValueError("Unsupported Procslink message payload type: %s" % procslink_message.header.payload_type)
        jsonrpc_request = None
        try:
            jsonrpc_request = JSONRPCRequest.from_bytes(procslink_message.payload)
            method = jsonrpc_request.method
            if method not in functions:
                raise JSONRPCMethodNotFoundError()
            params = jsonrpc_request.params
            LOGGER.debug("calling RPC method %s, params = %s'", method, params)
            if isinstance(params, list):
                retval = functions[method](*params)
            elif isinstance(params, dict):
                retval = functions[method](**params)
            else:
                retval = functions[method]()
            if jsonrpc_request.is_notification:
                LOGGER.debug("will not reply to a notification")
                return None
            jsonrpc_response = JSONRPCResponse(jsonrpc_request.id, result=retval)
        except Exception as e:
            LOGGER.debug("JSONRPCRequestDispatcher:handle_request: caught exception %s" % e)
            error = e if isinstance(e, JSONRPCError) else JSONRPCInternalError(data=str(e))
            jsonrpc_response = JSONRPCResponse(jsonrpc_request.id if jsonrpc_request is not None else None, error=error)

        procslink_response = ProcslinkMessage(ProcslinkMessageHeader(
            payload_type=ProcslinkMessageHeader.PAYLOAD_TYPE_JSONRPC2_RESPONSE), jsonrpc_response.to_bytes())
        return procslink_response


class RPCPeer(object):
    def __init__(self, sock=None, dispatcher_cls=JSONRPCRequestDispatcher, registered_functions={}):
        """

        :param sock: if sock is None, a new Netlink socket will be created
        """
        self._socket = self.new_netlink_socket() if sock is None else sock
        self._nl_pid = self._socket.getsockname()[0]
        LOGGER.debug("RPCPeer is ready, fd=%s, nl_pid = %s", self._socket.fileno(), self._nl_pid)
        self._dispatcher = dispatcher_cls()
        self._registered_functions = registered_functions

    @classmethod
    def new_netlink_socket(cls):
        sock = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, socket.NETLINK_USERSOCK)
        sock.bind((0, 0))
        LOGGER.debug("new Netlink socket created, fd = %s, addr=%s", sock.fileno(), sock.getsockname())
        return sock

    @property
    def socket(self):
        return self._socket

    @property
    def nl_pid(self):
        return self._nl_pid

    def register_function(self, function, alternate_name=None):
        # type: (Callable, str) -> None
        if not inspect.isfunction(function) and not inspect.ismethod(function):
            raise TypeError("PCPeer:register_function: %s (%s) is not function" % (type(function), function))
        if alternate_name is not None and not isinstance(alternate_name, str):
            raise TypeError("PCPeer:register_function: alternate_name %s is not str" % alternate_name)
        name = function.__name__ if alternate_name is None else alternate_name
        if name in self._registered_functions:
            raise ValueError("fPCPeer:register_function: unction name 's' has been registered", name)
        self._registered_functions[name] = function
        LOGGER.debug("PCPeer:register_function: registered RPC function '%s' -> %s()", name, function.__name__)

    def register_functions_in_object(self, obj):
        LOGGER.debug("RPCPeer:register_functions_in_object: register method in object %s", obj)
        for member in dir(obj):
            if member.startswith("_"):
                LOGGER.debug("RPCPeer:register_functions_in_object: ignore member %s starting with '_'", member)
                continue
            func = getattr(obj, member)
            LOGGER.debug("RPCPeer:register_functions_in_object: inspecting member %s", member)
            if not inspect.ismethod(func):
                LOGGER.debug("RPCPeer:register_functions_in_object: member %s is not a method", member)
                continue
            self.register_function(func)

    def run_server_forever(self):
        while True:
            try:
                LOGGER.debug("RPC server: waiting for RPC request...")
                data, src_addr = self._socket.recvfrom(NetlinkMessageHeader.MESSAGE_SIZE_LIMIT)
                remote_nl_pid = src_addr[0]
                LOGGER.debug("RPC server: Message received from %s. length: %s, content: %s", remote_nl_pid, len(data),
                             data)
                netlink_message = NetlinkMessage.from_bytes(data)
                LOGGER.debug("RPC server: Netlink message unpacked: %s", netlink_message)
                if netlink_message.header.nlmsg_pid == 0 or netlink_message.header.nlmsg_pid != remote_nl_pid:
                    LOGGER.warning("message sender in Netlink header (%s) does not match its actual sender (%s)!",
                                   netlink_message.header.nlmsg_pid, remote_nl_pid)
                    raise ValueError("RPC server: invalid nlmsg_pid in Netlink message")
                procslink_message = ProcslinkMessage.from_bytes(netlink_message.payload)
                LOGGER.debug("RPC server: Procslink message unpacked: %s", procslink_message)
                procslink_response = self._dispatcher.handle_request(procslink_message, self._registered_functions)
                if procslink_response is not None:
                    netlink_response = NetlinkMessage(NetlinkMessageHeader(nlmsg_pid=self.nl_pid),
                                                      procslink_response.to_bytes())
                    self._socket.sendto(netlink_response.to_bytes(), (remote_nl_pid, 0))
            except Exception as e:
                LOGGER.warning("RPC server: An exception occurred during processing the request: %s", e)

    class RPCChannel(object):
        _COUNTER = 0

        def __init__(self, local, target):
            # type: (RPCPeer, int) -> None
            self._target = target
            self._local = local

        def __getattr__(self, item):
            item = str(item)
            LOGGER.debug("RPCChannel: function to call: %s, target: %s", item, self._target)

            def callee(*args, **kwargs):
                LOGGER.debug("RPCChannel: will call %s, args=%s, kwargs=%s, target: %s", item, args, kwargs,
                             self._target)
                if args and kwargs:
                    raise ValueError(
                        "RPC client: You can use index based parameter or name based parameter, but not both")
                RPCPeer.RPCChannel._COUNTER += 1
                jsonrpc_request = JSONRPCRequest(id=RPCPeer.RPCChannel._COUNTER, method=item,
                                                 params=args if args else (kwargs if kwargs else None))
                LOGGER.debug("RPCChannel: jsonrpc_request=%s", jsonrpc_request)
                procslink_request = ProcslinkMessage(ProcslinkMessageHeader(
                    payload_type=ProcslinkMessageHeader.PAYLOAD_TYPE_JSONRPC2_REQUEST), jsonrpc_request.to_bytes())
                netlink_request = NetlinkMessage(NetlinkMessageHeader(nlmsg_pid=self._local.nl_pid),
                                                 procslink_request.to_bytes())
                self._local._socket.sendto(netlink_request.to_bytes(), (self._target, 0))
                data, peer_addr = self._local._socket.recvfrom(
                    NetlinkMessageHeader.MESSAGE_SIZE_LIMIT)  # type: NetlinkMessage, tuple
                netlink_response = NetlinkMessage.from_bytes(data)
                LOGGER.debug("RPC client: Netlink message unpacked: %s", netlink_response)
                remote_nl_pid = peer_addr[0]
                if remote_nl_pid != self._target:
                    LOGGER.warning("RPC client: message sender in Netlink header does not match its actual sender!")
                    raise ValueError("RPC client: invalid nlmsg_pid in Netlink message")
                procslink_response = ProcslinkMessage.from_bytes(netlink_response.payload)
                LOGGER.debug("RPC client: Procslink message unpacked: %s", procslink_response)
                jsonrpc_response = JSONRPCResponse.from_bytes(procslink_response.payload)
                LOGGER.debug("RPC client: JSON-RPC response message unpacked: %s", jsonrpc_response)
                LOGGER.debug("RPC client: received JSON-RPC from server: %s", jsonrpc_response.to_json())
                if jsonrpc_response.error:
                    raise jsonrpc_response.error.data if isinstance(jsonrpc_response.error,
                                                                    JSONRPCInternalError) else jsonrpc_response.error
                return jsonrpc_response.result

            return callee

    def talk_to(self, target):
        # type: (int) -> RPCPeer.RPCChannel
        if not isinstance(target, int):
            raise TypeError("target must be int")
        LOGGER.debug("%s will talk to %s, caller pid=%s", self._nl_pid, target, os.getpid())
        return RPCPeer.RPCChannel(self, target)
