#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
"""libmidi sleep utils."""

_DEFAULT_SLEEP_TIME = 0.001
"""Default sleep time before polling."""
_sleep_time: float = _DEFAULT_SLEEP_TIME
"""How many seconds to sleep before polling again."""

def get_sleep_time() -> float:
	"""Get number of seconds sleep() will sleep."""
	return _sleep_time

def set_sleep_time(seconds: float = _DEFAULT_SLEEP_TIME) -> None:
	"""Set the number of seconds sleep() will sleep."""
	global _sleep_time
	_sleep_time = seconds
