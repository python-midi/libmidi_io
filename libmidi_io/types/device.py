#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
"""MIDI I/O device type."""

from typing import Type

from libmidi_io.types.port import BasePort

class Device:
	"""Class representing a MIDI device."""
	def __init__(self, name: str, backend: Type[BasePort], is_input: bool, is_output: bool):
		self.name = name
		self.backend = backend
		self.is_input = is_input
		self.is_output = is_output

	def open(self, **kwargs) -> BasePort:
		"""Handy method to open the device."""
		return self.backend(name=self.name, **kwargs)
