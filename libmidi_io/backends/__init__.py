#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
"""MIDI I/O backends."""

from importlib import import_module
from pathlib import Path
from pkgutil import iter_modules
from typing import Dict

from libmidi_io.types.backend import BackendModule

backends_path = Path(__file__).parent

def get_available_backends() -> Dict[str, BackendModule]:
	"""Return a list of available MIDI I/O backends."""
	backends = {}

	for _, name, _ in iter_modules([str(backends_path)]):
		try:
			module = import_module(f'{__name__}.{name}')
		except Exception:
			continue

		if not hasattr(module, 'get_devices') or not hasattr(module, 'Port'):
			continue

		backends[name] = module

	return backends

def get_backend(name: str) -> BackendModule:
	"""Return a backend module by name."""
	backends = get_available_backends()

	if name not in backends:
		raise ValueError(f"Unknown backend {name!r}")

	return backends[name]
