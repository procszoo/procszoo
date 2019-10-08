# -*- coding: utf-8 -*-
# common.py
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


class AbstractMessage(object):
    def to_bytes(self):
        # type: () -> bytes
        raise NotImplementedError()

    @classmethod
    def from_bytes(cls, data):
        # type: () ->  AbstractMessage
        raise NotImplementedError()

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.__dict__)


class AbstractMessageHeader(AbstractMessage, object):
    def struct_size(self):
        # type: () -> int
        raise NotImplementedError()

    def struct_format(self):
        # type: () -> str
        raise NotImplementedError()

    def to_bytes(self):
        # type: () -> bytes
        raise NotImplementedError()

    @classmethod
    def from_bytes(cls, data):
        # type: () ->  AbstractMessageHeader
        raise NotImplementedError()
