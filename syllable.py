import math
import struct
import json
import wave

byte_num_per_sample = 2
amplitude = (2 ** (byte_num_per_sample * 8 - 1)) - 1
amplitude /= 2
duration_unit = 250

separator = ','
space = ' '
space_note = '_'
octave_range = (0, 8)

name_to_index_mapping = {
    'c': 0,
    'C': 1,
    'd': 2,
    'D': 3,
    'e': 4,
    'f': 5,
    'F': 6,
    'g': 7,
    'G': 8,
    'a': 9,
    'A': 10,
    'b': 11,
}

class Music:
    def __init__(self):
        self.reset()

    def reset(self):
        self.harmonics = [(1, 1)]
        self.notations = []

    def to_json(self):
        return {
            'harmonics': self.harmonics,
            'notations': space.join(self.notations),
            }

def parse_notation(notation):
    notes = []
    i = 0
    while i < len(notation):
        if notation[i] in name_to_index_mapping:
            notes.append(notation[i:i+2])
            i += 2
        elif notation[i] == '_':
            notes.append(notation[i])
            i += 1
        else:
            break
    duration = int(notation[i:])
    return notes, duration

def get_frequency(note):
    name = note[0]
    if name == '_':
        return 0
    else:
        octave = int(note[1])
        key_id = name_to_index_mapping[name] + octave * 12 - 8
        return math.pow(2, (key_id - 49) / 12) * 440

harmonics1 = [
    [1, 1],
    [2, 0.01],
    [3, 0.1],
    [4, 0.02],
    [5, 0.05],
    [6, 0.01],
    [7, 0.01],
    ]

harmonics2 = [
    [1, 1],
    [2, 0.1],
    [3, 0.05],
    [4, 0.2],
    [5, 0.05],
    [6, 0.1],
    [7, 0.1],
    ]

harmonics3 = [
    [1, 0.3],
    [3, 0.2],
    [5, 0.2],
    [7, 0.1],
    [9, 0.1],
    ]

harmonics4 = [
    [1, 0.1],
    [2, 0.2],
    [3, 0.05],
    [4, 0.2],
    [5, 0.05],
    [6, 0.2],
    [7, 0.05],
    [8, 0.1],
    ]

def get_syllable(notation, harmonics, sampling_rate):
    syllable = []
    notes, duration = parse_notation(notation)
    sample_frame_num = round(sampling_rate * duration * duration_unit / 1000)
    frequencies = [get_frequency(note) for note in notes]
    harmonic_a_sum = sum(freq_a for freq_factor, freq_a in harmonics)
    for t in range(sample_frame_num):
        sum1 = 0
        for frequency in frequencies:
            for freq_factor, freq_a in harmonics:
                sum1 += amplitude * freq_a / harmonic_a_sum * math.exp(-t / sample_frame_num) * abs(math.sin(freq_factor * frequency * 4)) * math.sin(2 * math.pi * freq_factor * frequency * t / sampling_rate)
        sum1 /= len(frequencies)
        syllable.append(round(sum1))
    return syllable

def get_music_samples(music, sampling_rate):
    samples = []
    for notation in music.notations:
        if notation != separator:
            samples += get_syllable(notation, music.harmonics, sampling_rate)
    return samples

def save_music(file_path, music):
    with open(file_path, 'w') as f:
        json.dump(music.to_json(), f, indent=4)

def save_wave(file_path, music, sampling_rate):
    samples = get_music_samples(music, sampling_rate)
    with wave.open(file_path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(byte_num_per_sample)
        w.setframerate(sampling_rate)
        w.writeframes(struct.pack('<{}h'.format(len(samples)), *samples))

def load_music(file_path):
    with open(file_path) as f:
        music_json = json.load(f)
    music = Music()
    music.harmonics = music_json['harmonics']
    music.notations = music_json['notations'].split(space)
    return music
