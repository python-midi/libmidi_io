#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
"""MIDI I/O RtMidi backend."""

from libmidi.types.messages.common import BaseMessage
from mido.backends import rtmidi
import rtmidi

from libmidi_io.types.device import Device
from libmidi_io.types.port import BasePort

def get_devices():
	devices = []

	mi = rtmidi.MidiIn()
	mo = rtmidi.MidiOut()

	input_names = mi.get_ports()
	output_names = mo.get_ports()

	for name in input_names + output_names:
		devices.append(Device(name, Port, name in input_names, name in output_names))

	mi.delete()
	mo.delete()

	return devices

class Port(BasePort):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self._rt = rtmidi.MidiOut()

		port_names = self._rt.get_ports()
		if not port_names:
			raise IOError("No ports available")

		if self.name is None:
			self.name = port_names[0]
		if self.name not in port_names:
			raise IOError(f"Unknown port {self.name!r}")

		port_id = port_names.index(self.name)

		try:
			self._rt.open_port(port_id)
		except RuntimeError as err:
			raise IOError(*err.args)

	def _close(self):
		self._rt.close_port()
		self._rt.delete()

	def is_input(self) -> bool:
		return False

	def is_output(self) -> bool:
		return True

	def _send(self, message: BaseMessage):
		self._rt.send_message(message.to_bytes())
