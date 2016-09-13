# procslink.py
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

from __future__ import absolute_import, print_function

import struct

from procszoo.ipc.common import AbstractMessageHeader, AbstractMessage


class ProcslinkMessageHeader(AbstractMessageHeader, object):
    """
    Procslink message header
        struct connectorhdr {
            __u16 version; /* version number, default: 1 */
            __u16 flag; /* reserved */
            __u32 length; /* length including header */
            __u16 payload_type; // payload_type message type ID */
            __u16 reserved; /* reserved */
            __u32 seq; /* sequence number */
            __u64 timestamp; /* timestamp */
        };

    """
    FORMAT = ">HHIHHIQ"
    SIZE = 24

    def __init__(self, version=1, flag=0, length=-1, payload_type=0, reserved=0, seq=0, timestamp=0):
        # type: (int, int, int ,int, int, int, int)
        self.version = version
        self.flag = flag
        self.seq = seq
        self.length = length
        self.payload_type = payload_type
        self.reserved = reserved
        self.timestamp = timestamp
        pass

    def struct_size(self):
        return ProcslinkMessageHeader.SIZE

    def struct_format(self):
        return ProcslinkMessageHeader.FORMAT

    def to_bytes(self):
        return struct.pack(self.FORMAT, self.version, self.flag, self.length,
                           self.payload_type, self.reserved, self.seq, self.timestamp)

    @classmethod
    def from_bytes(cls, data):
        if len(data) != ProcslinkMessageHeader.SIZE:
            raise ValueError("ProcslinkMessageHeader length does not match")
        header = ProcslinkMessageHeader(*struct.unpack(ProcslinkMessageHeader.FORMAT, data))
        if header.length < 0:
            raise ValueError("invalid ProcslinkMessageHeader.length")
        return header


class ProcslinkMessage(AbstractMessage, object):
    def __init__(self, header, payload):
        # type: (ProcslinkMessageHeader, bytes) -> None
        if header.length < 0:
            header.length = len(payload)
        self.header = header
        self.payload = payload

    def to_bytes(self):
        return self.header.to_bytes() + self.payload

    @classmethod
    def from_bytes(cls, data):
        if len(data) < ProcslinkMessageHeader.SIZE:
            raise ValueError("ProcslinkMessage message is too short")
        header = ProcslinkMessageHeader.from_bytes(data[0: ProcslinkMessageHeader.SIZE])
        payload = data[ProcslinkMessageHeader.SIZE:]
        if header.length != len(payload):
            raise ValueError("length field in header doesn't match actual message length")
        return ProcslinkMessage(header, payload)
