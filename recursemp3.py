#!/usr/bin/env python3

import argparse
import os
import sys
import fnmatch
import re

import colorama
from mutagen.id3 import ID3, Encoding, TPE1, TALB, TCON, TPE2, TSOA, TRCK, TPOS, TIT2, TSOT, TFLT, ID3NoHeaderError

from CoverFetcher import CoverFetcher


def display_progress(i_number_of_files_processed, i_number_of_files_to_process, i_step=10, last_line=False):
    b_step_reached = bool((i_number_of_files_processed % i_step) == 0)

    if b_step_reached ^ last_line:
        print(colorama.Fore.GREEN + "OUT: Processed " + str(i_number_of_files_processed) + " of " + str(
            i_number_of_files_to_process) + " (" + str(
            round((100 * i_number_of_files_processed) / i_number_of_files_to_process, 2)) + "%).")


def main():
    # Automatically send a RESET color at the end of every print
    colorama.init(autoreset=True)

    parser = argparse.ArgumentParser(
        description="Process all MP3 files contained in the argument, "
                    "and tag them <genre>/<artist>/[<albumindex>.]<album>/[<trackindex>.]<trackname>")
    parser.add_argument("-d", "--directory", required=True, help="Set the directory from which parsing all mp3 files")
    parser.add_argument("-v", "--verbose", required=False, action="store_true", help="Increase output verbosity")
    parser.add_argument("-r", "--remove-tags", action="store_true", default=False,
                        help="Remove existing tags before applying new tags")
    parser.add_argument("--debug", action="store_true", default=False,
                        help="Insanely huge amount of output. Do not use on large trees")

    cover_group = parser.add_mutually_exclusive_group()
    cover_group.add_argument("-n", "--no-cover", action="store_true", default=False,
                             help="Do not try to fetch the album art (way much faster)")
    cover_group.add_argument("-c", "--only-cover", action="store_true", default=False,
                             help="Only fetch the album art (needs an Internet connection)")

    args = parser.parse_args()

    if args.debug:
        args.verbose = True

    if args.debug:
        print(colorama.Fore.MAGENTA + "DBG: args -> " + str(args))

    if not os.path.isdir(args.directory):
        print(colorama.Fore.RED + 'ERR: the argument supplied (' + args.directory + ') is not a directory.')
        sys.exit(1)

    # INIT #
    p_find_album_index = re.compile('(?P<TSOA>[a-zA-Z]?[0-9]+)\.(?P<TALB>.*)')
    p_find_track_and_disk_information = re.compile('^(?P<TPOS>[0-9]+)\.(?P<TRCK>[0-9]+)\.(?P<TIT2>.*)')
    p_find_track_only_information = re.compile('^(?P<TRCK>[0-9]+)\.(?P<TIT2>.*)')
    p_find_artist_information = re.compile('.*\((?P<TPE2>[^\)]+)\)$')
    p_is_image_file = re.compile('\.(jpe?g|png)$')

    s_absolute_root_directory = os.path.abspath(args.directory)
    l_mp3_files = [os.path.join(dirpath, f)
                   for dirpath, dirnames, files in os.walk(s_absolute_root_directory)
                   for f in fnmatch.filter(files, '*.mp3')]

    # history of parsed directories for cover art (do not process the same directory twice)
    dict_missing_cover_directories = dict()

    i_number_of_files_processed = 0
    i_number_of_files_to_process = len(l_mp3_files)
    display_progress(i_number_of_files_processed, i_number_of_files_to_process)
    if i_number_of_files_to_process == 0:
        print(colorama.Fore.YELLOW + "WRN: No files to process")
        sys.exit(0)

    # SEARCH #
    for current_file in l_mp3_files:
        current_root, file_name = os.path.split(current_file)
        filename_without_extension, file_extension = os.path.splitext(file_name)

        s_track_directory = current_root
        l_all_mp3_files_in_current_directory = fnmatch.filter(
            [f for f in os.listdir(s_track_directory) if os.path.isfile(os.path.join(s_track_directory, f))], '*.mp3')

        # Genre / Artist / Album / Track
        current_root, s_album_name = os.path.split(current_root)
        current_root, s_artist_name = os.path.split(current_root)
        current_root, s_genre_name = os.path.split(current_root)

        if not args.only_cover:
            print(colorama.Fore.BLUE + "2DO: tagging " + file_name)
            s_album_sort = ''

            m_album_index_found = re.match(p_find_album_index, s_album_name)
            if m_album_index_found:
                s_album_sort = m_album_index_found.group('TSOA')
                s_album_name = m_album_index_found.group('TALB')
            elif args.debug:
                print(colorama.Fore.YELLOW + "WRN: Could not find an album index in " + s_album_name)

            # TPOS / TRCK : track and disk number
            m_track_and_disk_index_found = re.match(p_find_track_and_disk_information, filename_without_extension)
            m_track_only_index_found = re.match(p_find_track_only_information, filename_without_extension)
            if m_track_and_disk_index_found:
                # Disk number initialisation with what was found in the regex
                s_disk_number = m_track_and_disk_index_found.group('TPOS')

                # Number of tracks : the number of elements in the current directory matching the disk number
                s_track_number = str(int(m_track_and_disk_index_found.group('TRCK'))) + '/' + str(
                    len([e for e in l_all_mp3_files_in_current_directory if e.startswith(s_disk_number + '.')]))

                # Number of disks : the length of the set containing all first two characters of track names
                s_disk_number = str(int(s_disk_number)) + '/' + str(
                    len({e[:2] for e in l_all_mp3_files_in_current_directory}))

                # The track name comes directly from the regex
                s_track_name = m_track_and_disk_index_found.group('TIT2')
            elif m_track_only_index_found:
                # the number of elements in the current directory
                s_track_number = str(int(m_track_only_index_found.group('TRCK'))) + '/' + str(
                    len(l_all_mp3_files_in_current_directory))
                s_disk_number = ''
                s_track_name = m_track_only_index_found.group('TIT2')
            else:
                s_track_number = s_disk_number = '0/0'
                s_track_name = filename_without_extension

            s_album_artist_name = s_artist_name
            if s_album_artist_name == 'various artists':
                s_album_artist_name = 'various ' + s_genre_name.lower() + ' artists'
                m_artist_found = re.match(p_find_artist_information, filename_without_extension)
                if m_artist_found:
                    s_artist_name = m_artist_found.group('TPE2')
                    # remove the artist name from the track name, now that we will tag it onto the artist name
                    s_track_name = s_track_name.replace('(' + s_artist_name + ')', '')
                else:
                    print(
                        colorama.Fore.YELLOW + "WRN: Could not find a matching artist in " + filename_without_extension)
                s_track_number = s_disk_number = '0/0'

            if s_album_name == 'various albums':
                s_album_name = 'various ' + s_genre_name.lower() + ' albums'

            if s_album_name == '' or s_artist_name == '' or s_genre_name == '':
                print(
                    colorama.Fore.RED + 'ERR: For file ' + current_file + ': cannot extract album <' + s_album_name +
                    '>, artist <' + s_artist_name + '> or genre <' + s_genre_name + '> information')

            # TAGGING #
            # create ID3 tag if not present
            try:
                o_current_tags = ID3(current_file)
            except ID3NoHeaderError:
                print(colorama.Fore.YELLOW + "WRN: No ID3 header found. Adding ID3 header.")
                o_current_tags = ID3()
            except Exception as err:
                print(colorama.Fore.RED + 'ERR: For file ' + current_file + ', found exception "' + str(err) + '"')
                continue

            o_tags_to_set = ID3()
            o_tags_to_set.add(TCON(encoding=Encoding.UTF8, text=s_genre_name))  # Genre
            o_tags_to_set.add(TPE1(encoding=Encoding.UTF8, text=s_artist_name))  # Artist
            o_tags_to_set.add(TALB(encoding=Encoding.UTF8, text=s_album_name))  # Album
            o_tags_to_set.add(TPE2(encoding=Encoding.UTF8,
                                   text=s_album_artist_name))  # Album artist (in brackets, for VA albums)
            o_tags_to_set.add(TSOA(encoding=Encoding.UTF8, text=s_album_sort))  # Album sort number
            o_tags_to_set.add(TRCK(encoding=Encoding.UTF8, text=s_track_number))
            o_tags_to_set.add(TIT2(encoding=Encoding.UTF8, text=s_track_name))
            o_tags_to_set.add(
                TSOT(encoding=Encoding.UTF8, text=s_track_number + '.' + s_disk_number))  # Track sort number
            o_tags_to_set.add(TPOS(encoding=Encoding.UTF8, text=s_disk_number))
            o_tags_to_set.add(TFLT(encoding=Encoding.UTF8, text='MPG/3'))

            if args.remove_tags:
                l_tags_to_remove = []
                # iterate through all tags found in file
                for s_current_tag_key in o_current_tags.keys():
                    if not s_current_tag_key in o_tags_to_set.keys():
                        # append to the list of tags to remove
                        l_tags_to_remove.append(s_current_tag_key)

                for s_current_tag_to_remove in l_tags_to_remove:
                    # remove all tags not in the o_current_tags list
                    if args.verbose:
                        print(colorama.Fore.GREEN + "OUT: Deleting frame " + s_current_tag_key)
                    o_current_tags.delall(s_current_tag_key)
            elif o_current_tags is not None:
                # do not remove all tags, but still remove some
                for sFrameToRemove in [
                    "APIC",  # Attached picture (will mess up with the downloaded cover art)
                    "COMM",  # Comments
                    "TDEN",  # Encoding time
                    "TDOR",  # Original release time
                    "TDRC",  # Recording time
                    "TDRL",  # Release time
                    "TDTG"  # Tagging time
                    "USLT",  # Unsynchronized lyric/text transcription
                ]:
                    o_current_tags.delall(sFrameToRemove)

            for sCurrentTag in o_tags_to_set:
                o_current_tags.add(o_tags_to_set[sCurrentTag])

            o_current_tags.save(filename=current_file, v1=0, v2_version=4)

        i_number_of_files_processed += 1
        display_progress(i_number_of_files_processed, i_number_of_files_to_process)

        # COVER #
        # check for the cover only once per directory
        if (not args.no_cover or args.only_cover) and s_track_directory not in dict_missing_cover_directories.keys():

            # no image file in the current directory
            b_cover_art_present = len([f for f in os.listdir(s_track_directory)
                                       if os.path.isfile(os.path.join(s_track_directory, f)) and
                                       p_is_image_file.search(f)]) > 0
            if not b_cover_art_present:
                print(colorama.Fore.BLUE + "OUT: adding " + s_track_directory + " for cover search")
                # add the current directory to the list of directories to process for cover art
                dict_missing_cover_directories[s_track_directory] = [s_artist_name, s_album_name]

    display_progress(i_number_of_files_processed, i_number_of_files_to_process, last_line=True)

    if len(dict_missing_cover_directories) > 0:
        print(colorama.Fore.GREEN + "OUT: fetching covers")
        cover_url = CoverFetcher(dict_missing_cover_directories)
        cover_url.go_fetch()


if __name__ == "__main__":
    main()
