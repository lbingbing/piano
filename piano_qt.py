import os
import sys
import enum
import threading
import queue

from PySide6 import QtCore, QtWidgets

import syllable
import sound_player

middle_keys = [
    QtCore.Qt.Key_A,
    QtCore.Qt.Key_S,
    QtCore.Qt.Key_D,
    QtCore.Qt.Key_F,
    QtCore.Qt.Key_G,
    QtCore.Qt.Key_H,
    QtCore.Qt.Key_J,
    ]

high_keys = [
    QtCore.Qt.Key_Q,
    QtCore.Qt.Key_W,
    QtCore.Qt.Key_E,
    QtCore.Qt.Key_R,
    QtCore.Qt.Key_T,
    QtCore.Qt.Key_Y,
    QtCore.Qt.Key_U,
    ]

low_keys = [
    QtCore.Qt.Key_Z,
    QtCore.Qt.Key_X,
    QtCore.Qt.Key_C,
    QtCore.Qt.Key_V,
    QtCore.Qt.Key_B,
    QtCore.Qt.Key_N,
    QtCore.Qt.Key_M,
    ]

@enum.unique
class State(enum.Enum):
    RECORDING = 0
    PLAYING = 1

@enum.unique
class PlayerFlag(enum.Enum):
    MUSIC_END = 0
    STOP = 1

class Player(QtCore.QObject):
    data_consumed = QtCore.Signal()
    music_ended = QtCore.Signal()

    def __init__(self, sampling_rate):
        super().__init__()

        self.player = sound_player.SoundPlayer(sampling_rate)
        self.q = queue.SimpleQueue()
        self.play_thd = threading.Thread(target=self.worker)
        self.play_thd.start()

    def play(self, samples):
        self.q.put(samples)

    def worker(self):
        while True:
            data = self.q.get()
            if data == PlayerFlag.STOP:
                break
            elif data == PlayerFlag.MUSIC_END:
                self.music_ended.emit()
            else:
                self.player.play(data)
                self.data_consumed.emit()

    def close(self):
        self.q.put(PlayerFlag.STOP)
        self.play_thd.join()
        self.play_thd = None
        self.q = None
        self.player.close()
        self.player = None

class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.sampling_rate = 48000
        self.music = syllable.Music()
        self.state = State.RECORDING
        self.harmonic_range = (0, 100)
        self.harmonic_freq_factors = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10]

        self.player = Player(self.sampling_rate)
        self.player.music_ended.connect(self.on_music_end)

        layout = QtWidgets.QVBoxLayout(self)

        octave_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(octave_layout)

        octave_label = QtWidgets.QLabel('octave:')
        octave_layout.addWidget(octave_label)
        self.octave_spin_box = QtWidgets.QSpinBox()
        self.octave_spin_box.setRange(*syllable.octave_range)
        self.octave_spin_box.setValue(4)
        octave_layout.addWidget(self.octave_spin_box)
        octave_spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        octave_layout.addItem(octave_spacer)

        harmonics_group_box = QtWidgets.QGroupBox('harmonics')
        layout.addWidget(harmonics_group_box)

        harmonics_layout = QtWidgets.QVBoxLayout(harmonics_group_box)

        harmonics_control_layout = QtWidgets.QHBoxLayout()
        harmonics_layout.addLayout(harmonics_control_layout)
        self.harmonic_freq_sliders = []
        self.harmonic_freq_spin_boxes = []
        for freq_factor in self.harmonic_freq_factors:
            harmonic_freq_control_layout = QtWidgets.QVBoxLayout()
            harmonics_control_layout.addLayout(harmonic_freq_control_layout)
            harmonic_freq_label = QtWidgets.QLabel('x{:2.2f}'.format(freq_factor))
            harmonic_freq_control_layout.addWidget(harmonic_freq_label)
            harmonic_freq_slider = QtWidgets.QSlider()
            harmonic_freq_slider.setRange(*self.harmonic_range)
            if freq_factor == 1:
                harmonic_freq_slider.setValue(self.harmonic_range[1])
            else:
                harmonic_freq_slider.setValue(self.harmonic_range[0])
            harmonic_freq_control_layout.addWidget(harmonic_freq_slider)
            harmonic_freq_spin_box = QtWidgets.QSpinBox()
            harmonic_freq_spin_box.setRange(*self.harmonic_range)
            if freq_factor == 1:
                harmonic_freq_spin_box.setValue(self.harmonic_range[1])
            else:
                harmonic_freq_spin_box.setValue(self.harmonic_range[0])
            harmonic_freq_control_layout.addWidget(harmonic_freq_spin_box)
            harmonic_freq_slider.valueChanged.connect(harmonic_freq_spin_box.setValue)
            harmonic_freq_slider.valueChanged.connect(self.change_harmonics)
            harmonic_freq_spin_box.valueChanged.connect(harmonic_freq_slider.setValue)
            harmonic_freq_spin_box.valueChanged.connect(self.change_harmonics)
            self.harmonic_freq_sliders.append(harmonic_freq_slider)
            self.harmonic_freq_spin_boxes.append(harmonic_freq_spin_box)

        reset_harmonics_button = QtWidgets.QPushButton('reset')
        reset_harmonics_button.clicked.connect(self.reset_harmonics)
        harmonics_layout.addWidget(reset_harmonics_button)

        self.music_text_edit = QtWidgets.QTextEdit()
        self.music_text_edit.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.music_text_edit.setFixedHeight(100)
        self.music_text_edit.setReadOnly(True)
        layout.addWidget(self.music_text_edit)

        control_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(control_layout)

        self.play_button = QtWidgets.QPushButton('play')
        self.play_button.clicked.connect(self.play_music)
        control_layout.addWidget(self.play_button)

        reset_music_button = QtWidgets.QPushButton('reset')
        reset_music_button.clicked.connect(self.reset_music)
        control_layout.addWidget(reset_music_button)

        save_button = QtWidgets.QPushButton('save')
        save_button.clicked.connect(self.save_music)
        control_layout.addWidget(save_button)

        load_button = QtWidgets.QPushButton('load')
        load_button.clicked.connect(self.load_music)
        control_layout.addWidget(load_button)

        self.installEventFilter(self)

    def change_harmonics(self):
        self.music.harmonics = [[freq_factor, harmonic_freq_slider.value()] for freq_factor, harmonic_freq_slider in zip(self.harmonic_freq_factors, self.harmonic_freq_sliders)]

    def reset_harmonics(self):
        for freq_factor, harmonic_freq_slider in zip(self.harmonic_freq_factors, self.harmonic_freq_sliders):
            if freq_factor == 1:
                harmonic_freq_slider.setValue(self.harmonic_range[1])
            else:
                harmonic_freq_slider.setValue(self.harmonic_range[0])

    def process_separator(self):
        self.add_note(syllable.separator)

    def process_space_note(self):
        note = syllable.space_note + '1'
        self.add_note(note)
        self.play_note(note)

    def process_middle_note(self, key, sharp):
        key_id = middle_keys.index(key)
        note = self.get_note(key_id, sharp, self.octave_spin_box.value())
        self.add_note(note)
        self.play_note(note)

    def process_high_note(self, key, sharp):
        key_id = high_keys.index(key)
        note = self.get_note(key_id, sharp, self.octave_spin_box.value()+1)
        self.add_note(note)
        self.play_note(note)

    def process_low_note(self, key, sharp):
        key_id = low_keys.index(key)
        note = self.get_note(key_id, sharp, self.octave_spin_box.value()-1)
        self.add_note(note)
        self.play_note(note)

    def get_note(self, key_id, sharp, octave):
        if key_id == 0:
            name = 'C' if sharp else 'c'
        elif key_id == 1:
            name = 'D' if sharp else 'd'
        elif key_id == 2:
            name = 'e'
        elif key_id == 3:
            name = 'F' if sharp else 'f'
        elif key_id == 4:
            name = 'G' if sharp else 'g'
        elif key_id == 5:
            name = 'A' if sharp else 'a'
        elif key_id == 6:
            name = 'b'
        else:
            assert 0
        note = '{}{}1'.format(name, octave)
        return note

    def add_note(self, note):
        self.music.notations.append(note)
        self.update_music_text()

    def remove_last_note(self):
        if self.music:
            del self.music.notations[-1]
            self.update_music_text()

    def update_music_text(self):
        self.music_text_edit.setPlainText(syllable.space.join(self.music.notations))

    def play_note(self, note):
        samples = syllable.get_syllable(note, self.music.harmonics, self.sampling_rate)
        self.player.play(samples)

    def play_music(self):
        self.play_button.setEnabled(False)
        samples = syllable.get_music_samples(self.music, self.sampling_rate)
        self.player.play(samples)
        self.player.play(PlayerFlag.MUSIC_END)

    def on_music_end(self):
        self.play_button.setEnabled(True)

    def reset_music(self):
        self.music.reset()
        self.update_music_text()

    def save_music(self):
        file_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Music', filter='Musics (*.txt)')
        if file_path[0]:
            syllable.save_music(file_path[0], self.music)

    def load_music(self):
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Load Music', filter='Musics (*.txt)')
        if file_path[0]:
            self.music = syllable.load_music(file_path[0])
            harmonics = [[freq_factor, freq_a] for freq_factor, freq_a in self.music.harmonics]
            for freq_factor, freq_a in harmonics:
                index = self.harmonic_freq_factors.index(freq_factor)
                self.harmonic_freq_sliders[index].setValue(freq_a)
            self.update_music_text()

    def eventFilter(self, obj, event):
        if self.state == State.RECORDING:
            if event.type() == QtCore.QEvent.KeyPress:
                if event.key() == QtCore.Qt.Key_Underscore:
                    self.process_space_note()
                elif event.key() == QtCore.Qt.Key_Comma:
                    self.process_separator()
                elif event.key() in middle_keys:
                    self.process_middle_note(event.key(), event.modifiers() == QtCore.Qt.ShiftModifier)
                elif event.key() in high_keys:
                    self.process_high_note(event.key(), event.modifiers() == QtCore.Qt.ShiftModifier)
                elif event.key() in low_keys:
                    self.process_low_note(event.key(), event.modifiers() == QtCore.Qt.ShiftModifier)
                elif event.key() == QtCore.Qt.Key_Backspace:
                    self.remove_last_note()
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        self.player.close()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = Widget()
    widget.show()
    sys.exit(app.exec())
