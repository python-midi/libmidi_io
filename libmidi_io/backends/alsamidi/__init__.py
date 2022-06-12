#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
"""MIDI I/O ALSA MIDI backend."""

from alsa_midi import MidiBytesEvent, PortCaps, PortType, SequencerClient
from alsa_midi.mido_backend import _find_port
from libmidi.types.message import message_from_bytes
from libmidi.types.messages.common import BaseMessage
from threading import Thread
from weakref import WeakValueDictionary

from libmidi_io.types.device import Device
from libmidi_io.types.port import BasePort

class _Client:
	instance: '_Client' = None

	def __init__(self):
		name = "libmidi_io"
		self.ports: WeakValueDictionary[int, Port] = WeakValueDictionary()
		self.client = SequencerClient(name)
		self.closing = False
		self.in_thread = Thread(name="ALSA seq input", target=self._input_loop, daemon=True)
		self.in_thread.start()

	def __del__(self):
		self.close()

	def close(self):
		self.closing = True
		self.client.close()

	@classmethod
	def get_instance(cls):
		if cls.instance is not None:
			return cls.instance
		cls.instance = cls()
		return cls.instance

	def _input_loop(self):
		try:
			while not self.closing:
				event = self.client.event_input(timeout=1, prefer_bytes=True)
				if event is None:
					continue
				if not isinstance(event, MidiBytesEvent):
					continue

				assert event.dest is not None

				libmidi_io_port = self.ports.get(event.dest.port_id)
				if libmidi_io_port is None:
					continue
				if not libmidi_io_port.is_input():
					continue

				libmidi_io_port._handle_input_bytes(event.midi_bytes)
		except Exception as e:
			print(f"Error in libmidi_io.backend.alsamidi input loop: {e}")

def get_devices():
	devices = []

	client = _Client.get_instance().client

	for port in client.list_ports():
		devices.append(Device(
			f"{port.client_name}:{port.name} {port.client_id}:{port.port_id}",
			Port, port.capability & PortCaps.READ,
			port.capability & PortCaps.WRITE
		))

	return devices

class Port(BasePort):
	_last_num = 0
	_name_prefix = "inout"

	def __init__(self,
	             port_caps: PortCaps = PortCaps.READ | PortCaps.WRITE,
	             port_type: PortType = PortType.MIDI_GENERIC,
	             **kwargs):
		super().__init__(**kwargs)

		self.port_caps = port_caps
		self.port_type = port_type

		client = _Client.get_instance()

		name = self._generate_alsa_port_name()

		ports = client.client.list_ports()
		if not ports:
			raise IOError("no ports available")

		self._dest_port = ports[0] if self.name is None else _find_port(ports, self.name)
		self._port = client.client.create_port(name, caps=self.port_caps, type=self.port_type)

		if self._dest_port is not None:
			if self.is_input():
				self._port.connect_from(self._dest_port)
			if self.is_output():
				self._port.connect_to(self._dest_port)

		client.ports[self._port.port_id] = self

	def _close(self):
		if self._port is not None:
			self._port.close()
			self._port = None

	def is_input(self):
		return self._dest_port.capability & PortCaps.READ

	def is_output(self):
		return self._dest_port.capability & PortCaps.WRITE

	def _receive(self, block: bool):
		return None

	def _send(self, message: BaseMessage):
		client = _Client.get_instance().client
		event = MidiBytesEvent(message.to_bytes())
		client.event_output(event, port=self._port, dest=self._dest_port)
		client.drain_output()

	@classmethod
	def _generate_alsa_port_name(cls) -> str:
		num = cls._last_num + 1
		cls._last_num = num
		return f"{cls._name_prefix}{num}"

	def _handle_input_bytes(self, midi_bytes: bytes):
		self._messages.append(message_from_bytes(midi_bytes))
