#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
"""MIDI I/O KDMAPI backend."""

from kdmapi import KDMAPI
from libmidi.types.messages.common import BaseMessage
from libmidi.types.messages.system import BaseMessageSystem

from libmidi_io.types.device import Device
from libmidi_io.types.port import BasePort

def get_devices():
	devices = []

	if KDMAPI.IsKDMAPIAvailable():
		maj, min, build, rev = KDMAPI.ReturnKDMAPIVer()
		devices.append(Device(f'OmniMIDI {maj}.{min}.{build} Rev. {rev}', Port, False, True))

	return devices

class Port(BasePort):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		KDMAPI.InitializeKDMAPIStream()

	def _close(self):
		KDMAPI.TerminateKDMAPIStream()

	def is_input(self) -> bool:
		return False

	def is_output(self) -> bool:
		return True

	def _send(self, message: BaseMessage):
		if isinstance(message, BaseMessageSystem):
			# SysEx messages are written as a string.
			KDMAPI.SendDirectLongDataNoBuf(message.to_bytes())
		else:
			# The bytes of a message as packed into a 32 bit integer.
			packed_message = 0
			for byte in reversed(message.to_bytes()):
				packed_message <<= 8
				packed_message |= byte

			KDMAPI.SendDirectData(packed_message)
