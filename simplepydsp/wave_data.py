"""Process WAVE file contents using Python data structures."""

import argparse
import pcm_wave
import sys

class WaveData(object):
    def __init__(self, input_file=None, output_file=None):
        """
        Instantiate input and output wave objects.

        Defaults to STDIN and STDOUT if input_file or output_file are None or 
        unspecified.

        :param input_file: input file path or handle, None for STDIN.
        :param output_file: output file path or handle, None for STDOUT.
        """
        self.input_file = input_file if input_file else sys.stdin
        self.output_file = output_file if output_file else sys.stdout

        self.input_wave = pcm_wave.open(self.input_file, 'r')
        self.output_wave = pcm_wave.open(self.output_file, 'w')

        # Default output_wave parameters to the input_wave values
        self.output_wave.set_parameters(self.input_wave.get_parameters())

        # Override max_int if the output_wave uses a different number of bits
        # per sample than the input_wave
        self.max_int = 2 ** (self.output_wave.sample_width * 8) - 1

    def get_wave_data(self):
        """
        Returns a generator of frames.

        Each frame is a list of integer samples, where the list length is the
        number of channels in the WAVE file.
        """
        while True:
            frame = self.input_wave.read_frames(1)
            if not frame:
                break
            yield list(frame)

    def write_data(self, data):
        """Write frames to the output file."""
        for frame in data:
            for i, channel in enumerate(frame):
                frame[i] = self.limit_sample(channel)
            self.output_wave.write_frames([frame])

    def limit_sample(self, sample):
        """
        Ensure that the sample doesn't exceed the range of possible integers
        that the output bits can store.
        """
        sample = min(sample, self.max_int)
        sample = max(sample, -self.max_int)
        return sample


class Effect(object):
    """Base class for creating digital signal effects."""
    def __init__(self, description='Process WAVE Data'):
        self.parser = argparse.ArgumentParser(description=description)
        self.add_arguments()
        self.add_effect_arguments()

    def add_arguments(self):
        self.parser.add_argument(
            'input_file', default=None,
            help='Path to the input file. Defaults to STDIN',
        )
        self.parser.add_argument(
            'output_file', default=None,
            help='Path to the output file. Defaults to STDOUT')

    def add_effect_arguments(self):
        """Override to define effect-specific arguments"""
        pass

    def parse_arguments(self, argv=None):
        args = self.parser.parse_args(argv)
        return args
