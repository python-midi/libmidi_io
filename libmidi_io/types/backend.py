#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
"""MIDI I/O backend type."""

from typing import Callable, List

from libmidi_io.types.device import Device
from libmidi_io.types.port import BasePort

class BackendModule:
	"""Base backend module class for typing."""
	get_devices: Callable[[], List[Device]]
	"""Return a list of devices supported by this backend."""
	Port: BasePort
	"""The port type for this backend."""
