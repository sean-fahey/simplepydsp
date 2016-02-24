===========
simplepydsp
===========

A simple python library to create audio dsp effects and stream audio between them.
----------------------------------------------------------------------------------

simplepydsp is a Python 2.7 library that can be used to read and write WAVE files,
and create digital signal processing effects using streaming Python data
structures to represent the WAVE data.

Unlike the standard Python wave library, the simplepydsp WAVE reader and
writer support non-seekable files like standard-in and standard-out. This
allows effects to be strung together serially (either in Python, or externally
with, e.g., shell scripts).

The pcm_wave.py classes are written more simply than the Python standard
library, and only support linear PCM data. As a result, this library is slower
and is better suited for beginner learning, modification ease, or in
offline / batch processing situations.


Copyright (C) 2016 Sean Fahey.

Released under the MIT License. See LICENSE for details.
