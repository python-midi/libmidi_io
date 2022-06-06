#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
"""libmidi messages utils."""

from libmidi.types.messages.channel import MessageControlChange

DEFAULT_NUM_CHANNELS = 16

def reset_messages(num_channels: int = DEFAULT_NUM_CHANNELS):
	"""Yield "All Notes Off" and "Reset All Controllers" for all channels."""
	ALL_NOTES_OFF = 123
	RESET_ALL_CONTROLLERS = 121
	for channel in range(num_channels):
		for control in [ALL_NOTES_OFF, RESET_ALL_CONTROLLERS]:
			yield MessageControlChange(channel=channel, control=control, value=0)

def panic_messages(num_channels: int = DEFAULT_NUM_CHANNELS):
	"""
	Yield "All Sounds Off" for all channels.

	This will mute all sounding notes regardless of
	envelopes. Useful when notes are hanging and nothing else
	helps.
	"""
	ALL_SOUNDS_OFF = 120
	for channel in range(num_channels):
		yield MessageControlChange(channel=channel, control=ALL_SOUNDS_OFF, value=0)
