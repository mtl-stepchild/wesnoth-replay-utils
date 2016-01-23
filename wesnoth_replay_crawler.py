# -*- coding: utf-8 -*-
"""
Created on Sat Jan 16 23:53:42 2016

@author: Ginger
"""

import bs4
import bz2
import itertools
import os
import requests
import re
import zlib

REPLAY_DIRECTORY = "replays"
UNCOMPRESSED_REPLAY_DIRECTORY = os.path.join(REPLAY_DIRECTORY, "uncompressed")
COMPRESSED_REPLAY_DIRECTORY = os.path.join(REPLAY_DIRECTORY, "compressed")
REPLAY_SERVER_URL = "http://replays.wesnoth.org/"
REPLAY_URL_FILE_NAME = "URLs.txt"
# PLAYERS = ["Talkative", "angerpersonified", "CenetaurmanE52", "Kagar", "Yarghenforgen", "GiantAngrySeaSerpe"]
PLAYERS = ["Talkative", "angerpersonified"]

def cell_to_href(cell):
    return cell.find("a")["href"]


def extract_directories_from_table(url):
    """
    Create URLs from <table> tag at the given page
    Structure: <table><tr><a href="URL">
    """
    replay_page = requests.get(url)
    replay_soup = bs4.BeautifulSoup(replay_page.text)
    cells = replay_soup.find("table").findAll("tr")
    return [cell_to_href(cell) for cell in cells if
            cell.find("a") and
            cell.find("img")["alt"] == "[DIR]"]


def replay_page_to_cells_with_players(url, player_list, predicate=any):
    print("Pulling replay page {0}...".format(url))
    html = requests.get(url)
    soup = bs4.BeautifulSoup(html.text)
    cells = soup.find('table').findAll('tr')
    def contains_name(cell):
        try:
            description = str(cell.findAll("td")[-1])
        except IndexError:
            return False
        players = description[description.find("players"):]
        return predicate([player in players for player in player_list])


    return filter(contains_name, cells)


def replay_page_to_ids(url):
    replay_cells = replay_page_to_cells_with_players(url, player_list=PLAYERS, predicate=all)
    return [cell_to_href(match) for match in replay_cells]


def attempt_timestamp_extraction_and_formatting(url):
    formatted_timestamp = "0000-00-00"
    try:
        game_timestamp = url.split("/")[-2]
        if re.match("\\d{8}", game_timestamp):
            formatted_timestamp = "{0}-{1}-{2}".format(game_timestamp[:4],
                                                      game_timestamp[4:6],
                                                      game_timestamp[6:8])
    except IndexError:
        pass

    return formatted_timestamp


def get_valid_filename(s):
    return s.strip().replace(' ', '_').replace(':', '_')


def extract_game_url_to_disk(url):
    print("Pulling game url {0}...".format(url))
    # Create descriptive filename for sorting
    game_id = url.split("/")[-1]
    formatted_game_timestamp = attempt_timestamp_extraction_and_formatting(url)
    formatted_game_id = get_valid_filename(game_id)
    game_filename = "{0}_{1}".format(formatted_game_timestamp, formatted_game_id)

    compressed_replay = requests.get(url)
    if compressed_replay.status_code == 200:
        with open(os.path.join(COMPRESSED_REPLAY_DIRECTORY, game_filename), 'wb') as game_file:
            # Special cases for decompressing
            if url.endswith(".gz"):
                decompressed = zlib.decompress(compressed_replay.content, 16 + zlib.MAX_WBITS)
                with open(os.path.join(UNCOMPRESSED_REPLAY_DIRECTORY,
                                       game_filename[:-3] + ".txt"), 'w') as dcmp_game_file:
                    dcmp_game_file.write(decompressed)
            elif url.endswith(".bz2"):
                decompressed = bz2.decompress(compressed_replay.content)
                with open(os.path.join(UNCOMPRESSED_REPLAY_DIRECTORY,
                                       game_filename[:-4] +  ".txt"), 'w') as dcmp_game_file:
                    dcmp_game_file.write(decompressed)

            print("Saving to {0}.".format(game_filename))
            # Save compressed file-- .content is empty after this copy operation
            game_file.write(compressed_replay.content)

    else:
        print("Request failed.")


def check_dir(d):
    # Create a results directory
    if not os.path.exists(d):
        os.makedirs(d)


def extract_game_urls_to_disk(urls):
    # Create a results directory
    check_dir(UNCOMPRESSED_REPLAY_DIRECTORY)
    check_dir(COMPRESSED_REPLAY_DIRECTORY)

    # Save the URLs to disk
    with open(os.path.join(REPLAY_DIRECTORY, REPLAY_URL_FILE_NAME), 'w') as urls_file:
        urls_file.write("\n".join(urls))

    # Pull games and write to disk
    for url in urls:
        extract_game_url_to_disk(url)


def get_game_urls():
    if not os.path.exists(os.path.join(REPLAY_DIRECTORY, REPLAY_URL_FILE_NAME)):
        major_version_urls = ["{0}{1}".format(REPLAY_SERVER_URL, d)
                              for d in extract_directories_from_table(REPLAY_SERVER_URL)]
        print(major_version_urls)

        date_urls = list(itertools.chain.from_iterable(
                         [["{0}{1}".format(url, tbl_dir) for tbl_dir in extract_directories_from_table(url)]
                           for url in major_version_urls]
                         ))
        print("Date URLs: {0}".format(len(date_urls)))

        game_id_urls = list(itertools.chain.from_iterable(
                            [["{0}{1}".format(url, game_id) for game_id in replay_page_to_ids(url)]
                              for url in date_urls]
                            ))
    else:
        with open(os.path.join(REPLAY_DIRECTORY, REPLAY_URL_FILE_NAME)) as urls_file:
            game_id_urls = [url.strip() for url in urls_file.readlines()]

    print("Game ID URLs: {0}".format(len(game_id_urls)))
    return game_id_urls


if __name__ == "__main__":
    extract_game_urls_to_disk(get_game_urls())
