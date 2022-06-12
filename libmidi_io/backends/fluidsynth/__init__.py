#
# Copyright (C) 2022 Sebastiano Barezzi
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
"""MIDI I/O FluidSynth backend."""

from fluidsynth import Synth
from libmidi.types.messages.channel import (
	MessageNoteOff,
	MessageNoteOn,
	MessageAftertouch,
	MessageControlChange,
	MessageProgramChange,
	MessageChannelAftertouch,
	MessagePitchBend,
)
from libmidi.types.messages.common import BaseMessage

from libmidi_io.types.device import Device
from libmidi_io.types.port import BasePort

def get_devices():
	return [
		Device("FluidSynth", Port, False, True),
	]

class Port(BasePort):
	def __init__(self,
	             audio_driver: str = None,
				 audio_device: str = None,
				 midi_driver: str = None,
				 soundfont: str = None,
	             **kwargs):
		super().__init__(**kwargs)

		self.audio_driver = audio_driver
		self.audio_device = audio_device
		self.midi_driver = midi_driver
		self.soundfont = soundfont

		self.synth = Synth()
		self.synth.start(driver=self.audio_driver, device=self.audio_device,
		                 midi_driver=self.midi_driver)

		if self.soundfont is not None:
			self.sfid = self.synth.sfload(self.soundfont, 1)
		else:
			self.sfid = None

	def _close(self):
		if self.sfid is not None:
			self.synth.sfunload(self.sfid, 1)

		self.synth.delete()

	def is_input(self) -> bool:
		return False

	def is_output(self) -> bool:
		return True

	def _send(self, message: BaseMessage):
		if isinstance(message, MessageNoteOn):
			self.synth.noteon(message.channel, message.note, message.velocity)
		elif isinstance(message, MessageNoteOff):
			self.synth.noteoff(message.channel, message.note)
		elif isinstance(message, MessageAftertouch):
			#self.synth.aftertouch(message.channel, message.note, message.value)
			pass
		elif isinstance(message, MessageControlChange):
			self.synth.cc(message.channel, message.control, message.value)
		elif isinstance(message, MessageProgramChange):
			self.synth.program_change(message.channel, message.program)
		elif isinstance(message, MessageChannelAftertouch):
			#self.synth.channel_aftertouch(message.channel, message.value)
			pass
		elif isinstance(message, MessagePitchBend):
			self.synth.pitch_bend(message.channel, message.value)
		else:
			print(f"Unknown message type: {type(message)}")
