#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
"""MIDI port type."""

from collections import deque
from libmidi.types.messages.common import BaseMessage
from random import shuffle
from threading import RLock
from time import sleep
from typing import List

from libmidi_io.utils.lock import DummyLock
from libmidi_io.utils.messages import reset_messages, panic_messages
from libmidi_io.utils.sleep import get_sleep_time

class BasePort:
	"""
	Base class for MIDI port.

	Subclass and override _open() and _close().
	Override is_input() and _receive() if this port supports input.
	Override is_output() and _send() if this port supports output.
	If the port allows multiple access at the same time, set _locking to False.
	"""
	_locking: bool = True

	def __init__(self, name: str = None, autoreset: bool = False, **kwargs):
		"""
		Create an output port

		name is the port name, as returned by output_names(). If
		name is None, the default output is used instead.
		Set autoreset to True to reset the port when it is closed.
		You can pass additional arguments to the backend-specific
		_open() method with kwargs.
		"""
		self.name = name
		self.autoreset = autoreset

		self._lock = RLock() if self._locking else DummyLock()

		# Input
		self._messages = deque()

		self.closed = True
		self._open(**kwargs)
		self.closed = False

	def is_input(self) -> bool:
		"""Return True if this is an input port."""
		raise NotImplementedError

	def is_output(self) -> bool:
		"""Return True if this is an output port."""
		raise NotImplementedError

	def _open(self, **kwargs) -> None:
		"""
		Backend-specific open() implementation.

		This method is called by __init__() and should not be called
		directly.
		If your backend doesn't need any special initialization,
		override _open() and do nothing.
		"""
		raise NotImplementedError

	def _close(self) -> None:
		"""
		Backend-specific close() implementation.

		This method is called by close() and must not be called
		directly.
		If your backend doesn't need any special cleanup,
		override _close() and do nothing.
		"""
		raise NotImplementedError

	def _receive(self, block: bool) -> BaseMessage:
		"""
		Backend-specific receive() implementation.

		This method is called by receive() to get a message.
		You can use libmidi.types.message.message_from_bytes() to
		parse a message from a byte string.
		If block is False, this method must return None if there is
		no message available.
		"""
		raise NotImplementedError

	def _send(self, msg: BaseMessage) -> None:
		"""
		Backend-specific send() implementation.
		
		This method is called by send() to send a message.
		You can use msg.to_bytes() to get a byte string of the message.
		"""
		raise NotImplementedError

	def __del__(self):
		"""Close the port when the object is garbage collected."""
		self.close()

	def __enter__(self):
		"""With context manager, return self."""
		return self

	def __exit__(self, type, value, traceback):
		"""With context manager, close the port."""
		self.close()
		return False

	def close(self):
		"""
		Close the port.

		If the port is already closed, nothing will happen. The port
		is automatically closed when the object goes out of scope or
		is garbage collected.
		"""
		with self._lock:
			if not self.closed:
				if self.autoreset:
					try:
						self.reset()
					except IOError:
						pass

				self._close()
				self.closed = True

	# Input

	def iter_pending(self):
		"""Iterate through pending messages."""
		while True:
			msg = self.receive(block=False)
			if msg is None:
				return
			else:
				yield msg

	def receive(self, block: bool = True) -> BaseMessage:
		"""
		Return the next message.

		This will block until a message arrives.

		If you pass block=False it will not block and instead return
		None if there is no available message.

		If the port is closed and there are no pending messages, IOError will be raised.
		If the port closes while waiting inside receive(), IOError will be raised.
		"""
		if not self.is_input():
			raise ValueError('Not an input port')

		# If there is a message pending, return it right away.
		with self._lock:
			if self._messages:
				return self._messages.popleft()

		if self.closed:
			if block:
				raise ValueError('receive() called on closed port')
			else:
				return None

		while True:
			with self._lock:
				msg = self._receive(block=block)
				if msg:
					return msg

				if self._messages:
					return self._messages.popleft()
				elif not block:
					return None
				elif self.closed:
					raise IOError("port closed during receive()")

			sleep(get_sleep_time())

	def __iter__(self):
		"""Iterate through messages until the port closes."""
		while True:
			try:
				yield self.receive()
			except IOError:
				if self.closed:
					return
				else:
					raise

	# Output

	def send(self, msg: BaseMessage) -> None:
		"""
		Send a message on the port.

		A copy of the message will be sent, so you can safely modify
		the original message without any unexpected consequences.
		"""
		if not self.is_output():
			raise ValueError("Not an output port")
		elif self.closed:
			raise ValueError("send() called on closed port")

		with self._lock:
			self._send(msg.copy())

	def reset(self) -> None:
		"""Send "All Notes Off" and "Reset All Controllers" on all channels."""
		if self.closed:
			return

		for msg in reset_messages():
			self.send(msg)

	def panic(self) -> None:
		"""
		Send "All Sounds Off" on all channels.

		This will mute all sounding notes regardless of
		envelopes. Useful when notes are hanging and nothing else
		helps.
		"""
		if self.closed:
			return

		for msg in panic_messages():
			self.send(msg)

class EchoPort(BasePort):
	"""A port that echoes messages back to the sender."""
	def _open(self, **kwargs):
		pass

	def _close(self):
		pass

	def is_input(self):
		return True

	def is_output(self):
		return True

	def _receive(self, block: bool):
		pass

	def _send(self, message: BaseMessage):
		self._messages.append(message)

	def __iter__(self):
		"""Get messages from _messages."""
		while True:
			msg = self.receive(block=False)
			if msg is None:
				return
			else:
				yield msg

class MultiPort(BasePort):
	"""A multi-port implementation."""
	def __init__(self, ports: List[BasePort], yield_ports: bool = False):
		"""Initialize a MultiPort."""
		super().__init__(self, "multi")

		self.ports = ports
		self.yield_ports = yield_ports

	def _open(self, **kwargs):
		pass

	def _close(self):
		pass

	def is_input(self):
		if not self.ports:
			return False

		return any(p.is_input() for p in self.ports)

	def is_output(self):
		if not self.ports:
			return False

		return any(p.is_output() for p in self.ports)

	def _send(self, message: BaseMessage):
		for port in self.ports:
			if not port.is_output():
				continue
			if port.closed:
				continue

			# TODO: what if a SocketPort connection closes in-between here?
			port.send(message)

	def _receive(self, block: bool):
		while True:
			# Make a shuffled copy of the port list.
			shuffle(self.ports)

			for port in self.ports:
				if not port.is_input():
					continue
				if port.closed:
					continue

				for message in port.iter_pending():
					if self.yield_ports:
						yield port, message
					else:
						yield message

			if block:
				sleep(get_sleep_time())
			else:
				break
