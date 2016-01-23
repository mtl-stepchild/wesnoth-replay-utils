# -*- coding: utf-8 -*-
"""
Created on Fri Jan 22 20:59:30 2016

@author: Ginger
"""

import bz2
import os
import tkFileDialog
import zlib

from Tkinter import Tk


def with_file(func):
    def call_with(filename):
        with open(filename, 'rb') as f:
            return func(f)
    return call_with


@with_file
def decompress_gz(f):
    return zlib.decompress(f.read(), 16 + zlib.MAX_WBITS)


@with_file
def decompress_bz2(f):
    return bz2.decompress(f.read())


def decompress_replay(filename):
    extension_to_decompression_function = {
        ".gz": decompress_gz,
        ".bz2": decompress_bz2
    }
    extension = os.path.splitext(filename)[-1]
    return extension_to_decompression_function[extension](filename)


def copy_and_decompress_replay(compressed_filename, decompressed_filename):
    with open(decompressed_filename, 'w') as output_file:
        output_file.write(decompress_replay(compressed_filename))


if __name__ == "__main__":
    # Prevent the root window from drawing
    Tk().withdraw()

    # Acquire replays directory
    compressed_replays_dir = tkFileDialog.askdirectory(title="Open compressed replay directory...")
    uncompressed_replays_dir = tkFileDialog.askdirectory(title="Open directory for uncompressed replays...")

    for replay_basename in os.listdir(compressed_replays_dir):
        print("Decompressing {0}...".format(replay_basename))

        compressed_filename = os.path.join(compressed_replays_dir, replay_basename)

        uncompressed_basename = os.path.splitext(os.path.basename(replay_basename))[0] + ".txt"
        uncompressed_filename = os.path.join(uncompressed_replays_dir, uncompressed_basename)

        copy_and_decompress_replay(compressed_filename, uncompressed_filename)
