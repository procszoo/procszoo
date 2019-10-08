# -*- coding: utf-8 -*-
# jsonrpc.py
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

# JSON-RPC 2.0 Specification: http://www.jsonrpc.org/specification

from __future__ import absolute_import, unicode_literals
from future.builtins import str, int

import json
import logging



from procszoo.ipc.common import AbstractMessage

LOGGER = logging.getLogger(__name__)


class AbstractJSONRPCObject(AbstractMessage, object):
    ENCODING = "utf-8"

    def __init__(self, id):
        """base class for JSON-RPC object

        :param id: An identifier established by the Client that MUST contain a String, Number, or NULL value if included.
                If it is not included it is assumed to be a notification.
                The value SHOULD normally not be Null and Numbers SHOULD NOT contain fractional parts.
                The Server MUST reply with the same value in the Response object if included. This member is used to correlate the context between the two objects.
        :except TypeError:
        """
        if id is not None and not isinstance(id, str) and not isinstance(id, int):
            raise TypeError("id is not None, str, or int")

        self.jsonrpc = "2.0"
        """A String specifying the version of the JSON-RPC protocol. MUST be exactly "2.0"."""

        self.id = id
        """An identifier established by the Client that MUST contain a String, Number, or NULL value if included."""

    @classmethod
    def from_dict(cls, d):
        # type: (dict) -> AbstractJSONRPCObject
        raise NotImplementedError()

    def to_dict(self):
        # type: (dict) -> AbstractJSONRPCObject
        raise NotImplementedError()

    @classmethod
    def from_json(cls, jsonstr):
        # type: (str) -> AbstractJSONRPCObject
        if not isinstance(jsonstr, str):
            raise TypeError("jsonstr must be str")
        try:
            json_dict = json.loads(jsonstr)  # type: dict
        except json.JSONDecodeError as e:
            raise JSONRPCParseError(internal_exception=e)
        return cls.from_dict(json_dict)

    def to_json(self):
        # type: () -> str
        return str(json.dumps(self.to_dict()))


    def to_bytes(self):
        # type: () -> bytes
        return self.to_json().encode(AbstractJSONRPCObject.ENCODING)

    @classmethod
    def from_bytes(cls, data):
        # type: (bytes) -> AbstractJSONRPCObject
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        return cls.from_json(data.decode(AbstractJSONRPCObject.ENCODING))


class JSONRPCRequest(AbstractJSONRPCObject, object):
    def __init__(self, id, method, params=None, is_notification=False):
        # type: (int, str, Union[list, dict, tuple], bool) -> None

        """
        initialize a JSON-RPC request object

        :param id: an identifier. An identifier established by the Client that MUST contain a String, Number, or NULL value
            if included. If it is not included it is assumed to be a notification.
        :param method: A String containing the name of the method to be invoked.
            Method names that begin with the word rpc followed by a period character (U+002E or ASCII 46) are reserved
            for rpc-internal methods and extensions and MUST NOT be used for anything else.
        :param params: An array or dictionary that holds the parameter values to be used during the invocation of
            the method. This member MAY be omitted.
        """
        if is_notification and id is not None:
            raise ValueError("id must be None for a notification")
        if not isinstance(method, str):
            raise TypeError("method must be str")
        if params is not None and not isinstance(params, tuple) and not isinstance(params, list) \
                and not isinstance(params, dict):
            raise TypeError("params must be None, tuple, list, or dict")

        AbstractJSONRPCObject.__init__(self, id)
        self.method = method
        self.params = params
        self._is_notification = is_notification

    @property
    def is_notification(self):
        return self._is_notification

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.__dict__)

    def to_dict(self):
        json_dict = {"jsonrpc": self.jsonrpc, "method": self.method}
        if not self._is_notification:
            json_dict["id"] = self.id
        if self.params:
            json_dict["params"] = self.params
        return json_dict

    @classmethod
    def from_dict(cls, json_dict):
        # type: (dict) -> JSONRPCRequest
        if json_dict.get("jsonrpc") != "2.0":
            raise JSONRPCInvalidRequestError()
        is_notification = "id" not in json_dict
        try:
            ret = JSONRPCRequest(None if is_notification else json_dict["id"], json_dict["method"],
                                 json_dict.get("params"), is_notification)
        except TypeError as e:
            raise JSONRPCInvalidRequestError(internal_exception=e)
        except ValueError as e:
            raise JSONRPCInvalidRequestError(internal_exception=e)
        return ret


class JSONRPCResponse(AbstractJSONRPCObject, object):
    def __init__(self, id, result=None, error=None):
        # type: (int, object, JSONRPCError) -> None
        """
        initialize a JSON-RPC response object

        :param id: This member is REQUIRED.
            It MUST be the same as the value of the id member in the Request Object.
            If there was an error in detecting the id in the Request object (e.g. Parse error/Invalid Request),
            it MUST be Null.
        :param result: This member is REQUIRED on success.
            This member MUST NOT exist if there was an error invoking the method.
            The value of this member is determined by the method invoked on the Server.
        :param error: This member is REQUIRED on error.
            This member MUST NOT exist if there was no error triggered during invocation.
        """
        if error is not None:
            if not isinstance(error, JSONRPCError):
                raise TypeError("error must be JSONRPCError")
            if result is not None:
                raise ValueError("result must be None when an error occurs")

        AbstractJSONRPCObject.__init__(self, id)
        self.result = result
        self.error = error

    def to_dict(self):
        json_dict = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error:
            json_dict["error"] = self.error.to_dict()
        else:
            json_dict["result"] = self.result
        return json_dict

    @classmethod
    def from_dict(cls, json_dict):
        # type: (dict) -> JSONRPCResponse
        if json_dict.get("jsonrpc") != "2.0":
            raise JSONRPCInvalidRequestError("jsonrpc field must be '2.0'")
        try:
            error_dict = json_dict.get("error")
            error = JSONRPCError.from_dict(error_dict) if error_dict else None
            ret = JSONRPCResponse(json_dict["id"], json_dict.get("result"), error)
        except TypeError as e:
            raise JSONRPCInvalidRequestError(internal_exception=e)
        except ValueError as e:
            raise JSONRPCInvalidRequestError(internal_exception=e)
        return ret


class JSONRPCError(Exception, AbstractJSONRPCObject):
    def __init__(self, code, message, data=None, internal_exception=None):
        """
        JSON-RPC error object
        :param code:  A Number that indicates the error type that occurred. This MUST be an integer.
        :param message: A String providing a short description of the error.
            The message SHOULD be limited to a concise single sentence.
        :param data: A Primitive or Structured value that contains additional information about the error.
            This may be omitted.
            The value of this member is defined by the Server (e.g. detailed error information, nested errors etc.).
        """

        if not isinstance(code, int):
            raise TypeError("code must be int")
        if not isinstance(message, str):
            raise TypeError("code must be str")

        self.code = code
        """
        A Number that indicates the error type that occurred.
        This MUST be an integer.
        """

        self.message = message
        """
        A String providing a short description of the error.
        The message SHOULD be limited to a concise single sentence.
        """

        self.data = data
        """
        A Primitive or Structured value that contains additional information about the error.
        This may be omitted.
        The value of this member is defined by the Server (e.g. detailed error information, nested errors etc.).
        """

        self.internal_exception = internal_exception

    def to_dict(self):
        json_dict = self.__dict__.copy()
        if self.data is None:
            del json_dict["data"]
        if self.internal_exception is None:
            del json_dict["internal_exception"]
        return json_dict

    @classmethod
    def from_dict(cls, json_dict):
        # type: (dict) -> JSONRPCError
        try:
            ret = JSONRPCError(json_dict["code"], json_dict["message"], json_dict.get("data"))
        except TypeError as e:
            raise JSONRPCInvalidRequestError(internal_exception=e)
        return ret


class JSONRPCParseError(JSONRPCError):
    def __init__(self, message="Parse error", internal_exception=None):
        JSONRPCError.__init__(self, -32700, message, internal_exception)


class JSONRPCInvalidRequestError(JSONRPCError):
    def __init__(self, message="Invalid Request", internal_exception=None):
        JSONRPCError.__init__(self, -32600, message, internal_exception)


class JSONRPCMethodNotFoundError(JSONRPCError):
    def __init__(self, message="Method not found"):
        JSONRPCError.__init__(self, -32601, message)


class JSONRPCInvalidParamsError(JSONRPCError):
    def __init__(self, message="Invalid params"):
        JSONRPCError.__init__(self, -32602, message)


class JSONRPCInternalError(JSONRPCError):
    def __init__(self, message="Internal error", data=None, internal_exception=None):
        JSONRPCError.__init__(self, -32603, message, data, internal_exception)


class JSONRPCServerError(JSONRPCError):
    def __init__(self, message="Server error", code=-32000):
        if code < -32099 or code > -32000:
            raise ValueError("code out of range: [-32099, -32000]")
        JSONRPCError.__init__(self, code, message)


class JSONRPCAppError(JSONRPCError):
    def __init__(self, message, code=-1):
        if code <= -32000:
            raise ValueError("code must be greater than -32000")
        JSONRPCError.__init__(self, code, message)
