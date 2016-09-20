# -*- coding: utf-8 -*-
# netlink.py
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

from __future__ import absolute_import, unicode_literals
from future.utils import text_to_native_str

import struct

from .common import AbstractMessage, AbstractMessageHeader


class NetlinkMessageHeader(AbstractMessageHeader, object):
    """
    Netlink message header:
           struct nlmsghdr {
               __u32 nlmsg_len;    /* Length of message including header. */
               __u16 nlmsg_type;   /* Type of message content. */
               __u16 nlmsg_flags;  /* Additional flags. */
               __u32 nlmsg_seq;    /* Sequence number. */
               __u32 nlmsg_pid;    /* Sender port ID. */
           };
    """

    FORMAT = ">IHHII"
    SIZE = 16
    MESSAGE_SIZE_LIMIT = 4096

    def __init__(self, nlmsg_len=-1, nlmsg_type=0, nlmsg_flags=0, nlmsg_seq=0,
                 nlmsg_pid=0):
        # type: (int, int, int ,int ,int)
        self.nlmsg_len = nlmsg_len
        self.nlmsg_type = nlmsg_type
        self.nlmsg_flags = nlmsg_flags
        self.nlmsg_seq = nlmsg_seq
        self.nlmsg_pid = nlmsg_pid

    def struct_size(self):
        return NetlinkMessageHeader.SIZE

    def struct_format(self):
        return NetlinkMessageHeader.FORMAT

    def to_bytes(self):
        # TODO: This is a WORKAROUND!
        # Before Python 2.7.7, struct.pack() only accepts native str.
        # Uses of unicode will cause TypeError: Struct() argument 1 must be string, not unicode.
        # This have been fixed by the Python community:
        # https://hg.python.org/cpython/raw-file/f89216059edf/Misc/NEWS
        return struct.pack(text_to_native_str(self.FORMAT), self.nlmsg_len, self.nlmsg_type, self.nlmsg_flags,
                           self.nlmsg_seq, self.nlmsg_pid)

    @classmethod
    def from_bytes(cls, data):
        if len(data) != NetlinkMessageHeader.SIZE:
            raise ValueError("Netlink header does not match")
        nlmsghdr = NetlinkMessageHeader(*struct.unpack(NetlinkMessageHeader.FORMAT, data))
        if nlmsghdr.nlmsg_len < 0 or nlmsghdr.nlmsg_len > NetlinkMessageHeader.MESSAGE_SIZE_LIMIT:
            raise ValueError("invalid nlmsg_len")
        return nlmsghdr


class NetlinkMessage(AbstractMessage, object):
    def __init__(self, header, payload):
        # type: (NetlinkMessageHeader, bytes) -> None
        if header.nlmsg_len < 0:
            header.nlmsg_len = len(payload)
        self.header = header
        self.payload = payload

    def to_bytes(self):
        return self.header.to_bytes() + self.payload

    @classmethod
    def from_bytes(cls, data):
        if len(data) < NetlinkMessageHeader.SIZE:
            raise ValueError("Netlink message is too short")
        nlmsghdr = NetlinkMessageHeader.from_bytes(data[0: NetlinkMessageHeader.SIZE])
        payload = data[NetlinkMessageHeader.SIZE:]
        if nlmsghdr.nlmsg_len != len(payload):
            raise ValueError("nlmsg_len field in header doesn't match actual message length")
        return NetlinkMessage(nlmsghdr, payload)
