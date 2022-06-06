#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
"""libmidi lock utils."""

class DummyLock(object):
	"""Dummy lock class."""
	def acquire(self, blocking=True, timeout=-1) -> bool:
		return True

	__enter__ = acquire

	def release(self) -> None:
		return None

	__exit__ = release
