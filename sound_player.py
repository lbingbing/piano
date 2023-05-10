import struct

import pyaudio

class SoundPlayer:
    def __init__(self, sampling_rate):
        self.handle = pyaudio.PyAudio()
        self.stream = self.handle.open(format=self.handle.get_format_from_width(2), channels=1, rate=sampling_rate, output=True)

    def play(self, samples):
        sample_bytes = struct.pack('<{}h'.format(len(samples)), *samples)
        self.stream.write(sample_bytes)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.handle.terminate()
