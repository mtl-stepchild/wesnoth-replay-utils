# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 22:57:19 2016

@author: Ginger
"""

import os
import tkFileDialog
import wesnoth_replay_crawler

from Tkinter import Tk


TRANSCRIPT_DIR = "transcripts"
SPEAK_TAG_STR = "speak"
SPEAK_TAG_FIELDS = ["id", "message"]


def wml_split(wml_str, tag):
    """
    Generate all the contents between [tag][/tag]
    http://stackoverflow.com/questions/2097921/easy-way-to-get-data-between-tags-of-xml-or-html-files-in-python
    """
    start = "[{0}]".format(tag)
    end = "[/{0}]".format(tag)
    for item in wml_str.split(end):
        if start in item:
            yield item[item.find(start) + len(start):]


def tag_to_dict(tag_contents, fields):
    results = dict()
    for field in fields:
        matching_lines = [line.strip().split("=")[-1] for line in tag_contents.split("\n")
                          if line.strip().startswith(field)]
        results[field] = "\n".join(matching_lines)
    return results


def prettify_tag(tag_contents, fields):
    tag_dict = tag_to_dict(tag_contents, fields)
    return "\n".join(["{0}: {1}".format(field, tag_dict[field]) for field in fields])


def prettify_speak_tag(tag_contents, fields):
    tag_dict = tag_to_dict(tag_contents, fields)
    speaker = tag_dict["id"].replace("\"", "")
    message = tag_dict["message"].replace("\"", "")
    return "{0}: {1}".format(speaker, message)


def copy_and_transcriptify_replay(replay_filename, transcript_filename):
    with open(replay_filename, 'r') as replay_file, open(transcript_filename, 'w') as transcript_file:
        transcript_lines = list()
        player_set = set()
        # Build transcript and list of players who speak during the game
        for speak_tag in wml_split(replay_file.read(), SPEAK_TAG_STR):
            transcript_lines.append("{0}\n".format(prettify_speak_tag(speak_tag, SPEAK_TAG_FIELDS)))
            player_set.add(tag_to_dict(speak_tag, ["id"])["id"].replace("\"", ""))
        player_list_string = "STARRING: {0}\n\n".format(", ".join(sorted(list(player_set))))

        # Write to transcript file
        transcript_file.write("".join([player_list_string] + transcript_lines))


def transcriptify_dir(replay_dir, transcript_dir):
    wesnoth_replay_crawler.check_dir(replay_dir)

    for filename in os.listdir(replay_dir):
        print("Transcriptifying {0}...".format(filename))

        replay_filename = os.path.join(replay_dir, filename)
        transcript_filename = os.path.join(transcript_dir, "{0}-formatted.txt".format(os.path.splitext(filename)[0]))
        copy_and_transcriptify_replay(replay_filename, transcript_filename)


if __name__ == "__main__":
    # Prevent the root window from drawing
    Tk().withdraw()

    # Acquire replays directory
    uncompressed_replays_dir = tkFileDialog.askdirectory(title="Open uncompressed replay directory...")
    transcripts_dir = tkFileDialog.askdirectory(title="Open directory for transcripts...")

    transcriptify_dir(uncompressed_replays_dir, transcripts_dir)
