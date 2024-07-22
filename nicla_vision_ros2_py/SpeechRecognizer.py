#!/usr/bin/env python3

# Copyright 2024 HHCM, Istituto Italiano di Tecnologia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from vosk import Model, KaldiRecognizer
import json
import wave
import numpy as np


class SpeechRecognizer:
    # grammar format example = '["open", "bottle", "cup", "[unk]"]'
    def __init__(
        self,
        vosk_model_path: str,
        grammar: str,
        listen_seconds=3,
        wave_output_filename="",
    ):

        self.LISTEN_SECONDS = listen_seconds  # Duration to listen to audio in

        # nicla vision mic specs
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 512

        # For saving wavs
        self.WAVE_OUTPUT_FILENAME = wave_output_filename
        self.WAVE_OUTPUT_FILENAME_i = 0

        self.audio_buffer = np.array([], dtype="int16")
        if self.WAVE_OUTPUT_FILENAME:
            self.recording_frames = []  # Added for storing audio frames

        self.model = Model(vosk_model_path)
        self.recognizer = KaldiRecognizer(self.model, self.RATE)
        self.recognizer.SetGrammar(grammar)

    def process_audio(self, data):

        recognized_audio = ""

        tmp = np.frombuffer(data, dtype="int16")

        self.audio_buffer = np.concatenate((self.audio_buffer, tmp))
        if self.WAVE_OUTPUT_FILENAME:
            self.recording_frames.append(data)

        if (
            len(self.audio_buffer) > self.RATE * self.LISTEN_SECONDS
        ):  # process in blocks of 1 second
            chunk = self.audio_buffer[: round(self.RATE * self.LISTEN_SECONDS)]
            self.audio_buffer = self.audio_buffer[
                round(self.RATE * self.LISTEN_SECONDS):
            ]

            if self.recognizer.AcceptWaveform(chunk.tobytes()):
                result = json.loads(self.recognizer.Result())
                if result["text"]:
                    # print(f"Recognized: {result['text']}")
                    recognized_audio = result["text"]

        # print(len(self.recording_frames))
        # print(int(self.RATE / self.CHUNK * self.LISTEN_SECONDS))
        if self.WAVE_OUTPUT_FILENAME:
            if len(self.recording_frames) >= int(
                self.RATE / self.CHUNK * self.LISTEN_SECONDS
            ):
                self.save_audio_to_wav()

        return recognized_audio

    def save_audio_to_wav(self):
        self.WAVE_OUTPUT_FILENAME_i += 1
        if self.WAVE_OUTPUT_FILENAME_i == 21:
            self.WAVE_OUTPUT_FILENAME_i = 1

        with wave.open(
            self.WAVE_OUTPUT_FILENAME
            + str(self.WAVE_OUTPUT_FILENAME_i)
            + ".wav",
            "wb",
        ) as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(self.RATE)
            wf.writeframes(b"".join(self.recording_frames))

        msg_print = (
            "Saved recording as"
            + f"{self.WAVE_OUTPUT_FILENAME}"
            + f"{str(self.WAVE_OUTPUT_FILENAME_i)}"
            + ".wav"
        )
        print(msg_print)
        self.recording_frames = []
