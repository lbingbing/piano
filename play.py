import syllable
import sound_player

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('music_file_path', help='music file path')
    parser.add_argument('--repeat_num', type=int, default=1, help='repeat num')
    args = parser.parse_args()

    music = syllable.load_music(args.music_file_path)

    sampling_rate = 48000
    player = sound_player.SoundPlayer(sampling_rate)
    samples = syllable.get_music_samples(music, sampling_rate)
    print('playing')
    for i in range(args.repeat_num):
        player.play(samples)
    player.close()
