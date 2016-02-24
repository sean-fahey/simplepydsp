"""Simple reader and writer of PCM WAVE (RIFF) files."""

import __builtin__
import struct


class WaveBase(object):
    """Common base class for Wave objects."""

    def get_channels(self):
        return self.channels

    def get_frames(self):
        return self.frames

    def get_sample_width(self):
        return self.sample_width

    def get_frame_rate(self):
        return self.frame_rate

    def get_parameters(self):
        return self.get_channels(), self.get_sample_width(), \
               self.get_frame_rate(), self.get_frames(),

    def __del__(self):
        self.close()

    def close(self):
        self._file.close()


class WaveReader(WaveBase):
    """Reader class for wave files."""
    def __init__(self, f):
        if isinstance(f, basestring):
            f = __builtin__.open(f, 'rb')
        self._file = f
        self.read_header()

    def read_header(self):
        """Reads wave header and set attributes."""
        # Read the RIFF chunk
        chunk_id = _unpack('4s', 'big', self._file.read(4))
        if chunk_id != 'RIFF':
            err = "Expecting 'RIFF' chunk_id, received {}".format(chunk_id)
            raise RuntimeError(err)

        chunk_size = _unpack('L', 'little', self._file.read(4))
        format_id = _unpack('4s', 'big', self._file.read(4))
        if format_id != 'WAVE':
            err = "Expected 'WAVE' format, received '{}'".format(format_id)
            raise RuntimeError(err)

        # Read the WAVE sub-chunk
        subchunk_id = _unpack('4s', 'big', self._file.read(4))
        if subchunk_id != 'fmt ':
            err = "Expected subchunk_id 'fmt ', received '{}'".format(subchunk_id)
            raise RuntimeError(err)

        subchunk_size = _unpack('L', 'little', self._file.read(4))
        audio_format = _unpack('H', 'little', self._file.read(2))
        if audio_format != 1:
            err = "Non-PCM streams are not supported."
            raise RuntimeError(err)

        self.channels = _unpack('H', 'little', self._file.read(2))
        self.frame_rate = _unpack('L', 'little', self._file.read(4))
        byte_rate = _unpack('L', 'little', self._file.read(4))
        self.block_align = _unpack('H', 'little', self._file.read(2))
        self.bits_per_sample = _unpack('H', 'little', self._file.read(2))
        self.sample_width = self.bits_per_sample // 8
        self.frame_size = self.channels * self.sample_width

        # TODO: handle the possibility of additional sub-chunks

        # Read the data sub-chunk
        data_chunk_id = _unpack('4s', 'big', self._file.read(4))
        if data_chunk_id != 'data':
            err = "Expected data_chunk_id 'data', received '{}'".format(data_chunk_id)
            raise RuntimeError(err)

        data_chunk_size = _unpack('L', 'little', self._file.read(4))
        self.frames = data_chunk_size // self.frame_size

        # Add file to the interface so that raw data is accessible
        self.file = self._file

    def read_raw_data(self, count):
        """
        Read the specified number of frames and return the corresponding bytes.
        """
        if count == 0:
            return

        size = count * self.channels * self.sample_width
        return self.file.read(size)

    def read_raw_frames(self, count):
        """
        Read the specified number of frames and yield each as bytes.
        """
        if count == 0:
            return

        offset = self.channels * self.sample_width
        size = count * offset

        for i in xrange(0, size, offset):
            frame = self.file.read(offset)
            if frame:
                yield frame
            else:
                raise StopIteration

    def read_frames(self, count):
        """
        Read the specified number of frames and return unpacked data.
        """
        if count == 0:
            return

        format_map = {1: 'b', 2: 'h', 4: 'l', 8: 'q'}

        byte_count = self.sample_width
        offset = self.channels * self.sample_width
        size = count * offset

        # Handle 24 bit (plus 40, 48, and 56 bit, if they were to exist)
        # Treat packed values as the closest available C struct
        # TODO: determine whether this needs to handle endianness
        if byte_count % 2 and byte_count > 1:
            # Find the closest next power of two
            next_power = 2 ** int(round(byte_count ** 0.5 + 0.5))
            pad_factor = next_power - byte_count
            format_str = format_map[next_power]

            output = []
            while True:
                data = self.file.read(byte_count)
                if not data:
                    break
                data = '\x00' * pad_factor + data
                output.append(_unpack(format_str, 'little', data))
                if len(output) == self.channels:
                    yield output
                    output = []
        else:
            frames = self.file.read(size)

            if not frames:
                return
            format_str = str(count * self.channels) + format_map[byte_count]
            data = _unpack(format_str, 'little', frames)

            for i in xrange(0, count * self.channels, self.channels):
                yield data[i:i+self.channels]


class WaveWriter(WaveBase):
    """Reader class for wave files."""
    def __init__(self, f):
        if isinstance(f, basestring):
            f = __builtin__.open(f, 'wb')
        self._file = f
        self.set_defaults()
        self.file = self._file

    def set_defaults(self):
        self.channels = 0
        self.sample_width = 0
        self.frame_rate = 0
        self.frames = 0
        self.header_written = False

    def set_channels(self, channels):
        self.channels = channels

    def set_frames(self, frames):
        self.frames = frames

    def set_sample_width(self, sample_width):
        self.sample_width = sample_width

    def set_frame_rate(self, frame_rate):
        self.frame_rate = frame_rate

    def set_parameters(self, parameters):
        channels, sample_width, frame_rate, frames = parameters
        self.set_channels(channels)
        self.set_sample_width(sample_width)
        self.set_frame_rate(frame_rate)
        self.set_frames(frames)

    def write_header(self):
        """Write the wave header to the file."""
        # Write the RIFF chunk
        chunk_id = _pack('4s', 'big', 'RIFF')
        size = 36 + self.frames * self.channels * self.sample_width
        chunk_size = _pack('L', 'little', size)
        format_id = _pack('4s', 'big', 'WAVE')

        riff_chunk = chunk_id + chunk_size + format_id
        self.file.write(riff_chunk)

        # Write the WAVE sub-chunk
        subchunk_id = _pack('4s', 'big', 'fmt ')
        subchunk_size = _pack('L', 'little', 16)
        audio_format = _pack('H', 'little', 1)

        channels = _pack('H', 'little', self.channels)
        frame_rate = _pack('L', 'little', self.frame_rate)
        byte_rate = self.frame_rate * self.channels * self.sample_width
        byte_rate = _pack('L', 'little', byte_rate)
        block_align = _pack('H', 'little', self.channels * self.sample_width)
        bits_per_sample = _pack('H', 'little', self.sample_width * 8)

        wave_chunk = subchunk_id + subchunk_size + audio_format + channels + \
            frame_rate + byte_rate + block_align + bits_per_sample
        self.file.write(wave_chunk)

        # Write the start of the data sub-chunk
        data_subchunk_id = _pack('4s', 'big', 'data')
        data_size = self.frames * self.channels * self.sample_width
        data_chunk_size = _pack('L', 'little', data_size)

        data_chunk = data_subchunk_id + data_chunk_size
        self.file.write(data_chunk)
        self.file.flush()

        self.header_written = True

    def write_raw_data(self, data):
        """
        Write data to the file.

        :param data: a string of packed C structs
        """
        if not self.header_written:
            self.write_header()
        self.file.write(data)
        self.file.flush()

    def write_raw_frames(self, data):
        """
        Write data to the file.

        :param data: iterable of strings of packed C structs
        """
        if not self.header_written:
            self.write_header()
        self.file.write(''.join(data))
        self.file.flush()

    def write_frames(self, data):
        """
        Write data to the file.

        :param data: an iterable of data frames (iterables of integers)
        """
        if not self.header_written:
            self.write_header()

        format_map = {1: 'b', 2: 'h', 4: 'l', 8: 'q'}

        byte_count = self.sample_width

        # Handle 24 bit (plus 40, 48, and 56 bit, if they were to exist)
        if byte_count % 2 and byte_count > 1:
            # Find the closest next power of two
            next_power = 2 ** int(round(byte_count ** 0.5 + 0.5))
            for frame in data:
                for sample in frame:
                    sample = _pack(format_map[next_power], 'little', sample)
                    # Strip padded zeroes
                    sample = sample[-byte_count:]
                    self.file.write(sample)
        else:
            for frame in data:
                format_str = str(self.channels) + format_map[byte_count]
                frame = _pack(format_str, 'little', *frame)
                self.file.write(frame)
        self.file.flush()


def _pack(fmt, endian, *data):
    """
    Helper method to pack data into C structs by wrapping the python
    ``struct.pack`` method.

    :param fmt: python ``struct`` format characters
    :param endian: endianness, 'big' or 'little'
    :param data: data to pack
    :returns: result or tuple of results
    """
    if endian == 'big':
        endian = '>'
    elif endian == 'little':
        endian = '<'
    return struct.pack(endian + fmt, *data)


def _unpack(fmt, endian, data):
    """
    Helper method to unpack data from C structs by wrapping the python
    ``struct.unpack`` method

    :param fmt: python ``struct`` format characters
    :param endian: endianness, 'big' or 'little'
    :param data: data to unpack
    :returns: result or tuple of results
    """
    if endian == 'big':
        endian = '>'
    elif endian == 'little':
        endian = '<'
    result = struct.unpack(endian + fmt, data)
    if len(result) < 2:
        return result[0]
    return result


def open(f, mode="rb"):
    """Return an instance of the correct reader or writer."""
    if mode in ('r', 'rb'):
        return WaveReader(f)
    elif mode in ('w', 'wb'):
        return WaveWriter(f)
    else:
        raise RuntimeError("Mode must be 'r', 'rb', 'w', or 'wb'")


