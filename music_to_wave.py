import syllable

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('music_file_path', help='music file path')
    parser.add_argument('wave_file_path', help='wave file path')
    args = parser.parse_args()

    music = syllable.load_music(args.music_file_path)
    syllable.save_wave(args.wave_file_path, music, 48000)
