#!/usr/bin/env python3

import argparse
import fnmatch
import logging
import os
import re
import sys

from mutagen.id3 import ID3, Encoding, TPE1, TALB, TCON, TPE2, TSOA, TRCK, TPOS, TIT2, TSOT, TFLT, ID3NoHeaderError, \
    TDRL

from CoverFetcher import CoverFetcher

mainlogger = logging.getLogger("recursemp3")
mainlogger.setLevel(logging.INFO)
LOGGER_2DO = logging.INFO + 1
logging.addLevelName(LOGGER_2DO, '2DO')


def display_progress(i_number_of_files_processed, i_number_of_files_to_process, i_step=10, last_line=False):
    b_step_reached = bool((i_number_of_files_processed % i_step) == 0)

    if b_step_reached ^ last_line:
        mainlogger.info("Processed " + str(i_number_of_files_processed) + " of " + str(
                i_number_of_files_to_process) + " (" + str(
                round((100 * i_number_of_files_processed) / i_number_of_files_to_process, 2)) + "%).")


def main():
    parser = argparse.ArgumentParser(
            description="Process all MP3 files contained in the argument, "
                        "and tag them <genre>/<artist>/[<albumindex>.]<album>/[<trackindex>.]<trackname>")
    parser.add_argument("-d", "--directory", required=True, help="Set the directory from which parsing all mp3 files")

    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument("-v", "--verbose", required=False, action="store_true",
                                 help="Increase output verbosity")
    verbosity_group.add_argument("-q", "--quiet", required=False, action="store_true", help="Decrease output verbosity")

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
        mainlogger.setLevel(logging.DEBUG)
        mainlogger.debug("args -> " + str(args))

    if args.quiet:
        mainlogger.setLevel(logging.WARNING)

    if not os.path.isdir(args.directory):
        mainlogger.error('the argument supplied (' + args.directory + ') is not a directory.')
        sys.exit(1)

    # INIT #
    p_find_album_index = re.compile('(?P<TSOA>[a-zA-Z]?[0-9]+)\.(?P<TALB>.*)')
    p_find_album_and_year_index = re.compile('(?P<TDRL>\[[0-9]{8}\])(?P<TSOA>[a-zA-Z]?[0-9]+)\.(?P<TALB>.*)')
    p_find_album_year_only = re.compile('(?P<TDRL>\[[0-9]{8}\])\.?(?P<TALB>.*)')
    p_find_track_and_disk_information = re.compile('^(?P<TPOS>[0-9]+)\.(?P<TRCK>[0-9]+)\.(?P<TIT2>.*)')
    p_find_track_only_information = re.compile('^(?P<TRCK>[0-9]+)\.(?P<TIT2>.*)')
    p_find_artist_information = re.compile('.*\((?P<TPE2>[^\)]+)\)$')
    p_is_image_file = re.compile('\.(jpe?g|png)$')
    p_process_date = re.compile('^\[?(?P<year>[0-9]{4})(?P<month>[0-9]{2})(?P<day>[0-9]{2})\]?$')

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
        mainlogger.warn("No files to process")
        sys.exit(0)

    # SEARCH #
    for current_file in l_mp3_files:
        current_root, file_name = os.path.split(current_file)
        filename_without_extension, file_extension = os.path.splitext(file_name)

        s_track_directory = current_root
        l_all_mp3_files_in_current_directory = fnmatch.filter(
                [f for f in os.listdir(s_track_directory) if os.path.isfile(os.path.join(s_track_directory, f))],
                '*.mp3')

        # Genre / Artist / Album / Track
        current_root, s_album_name = os.path.split(current_root)
        current_root, s_artist_name = os.path.split(current_root)
        current_root, s_genre_name = os.path.split(current_root)

        if not args.only_cover:
            mainlogger.log(LOGGER_2DO, "Processing " + file_name)
            s_album_sort = ''
            s_album_date = ''

            m_album_index_and_year_found = re.match(p_find_album_and_year_index, s_album_name)
            m_album_index_found = re.match(p_find_album_index, s_album_name)
            m_album_year_only_found = re.match(p_find_album_year_only, s_album_name)
            if m_album_index_and_year_found:
                s_album_sort = m_album_index_and_year_found.group('TSOA')
                s_album_name = m_album_index_and_year_found.group('TALB')
                s_album_date = m_album_index_and_year_found.group('TDRL')

                m_date_processed = re.match(p_process_date, s_album_date)
                if m_date_processed:
                    s_album_date = '{}-{}-{}'.format(m_date_processed.group('year'), m_date_processed.group('month'), m_date_processed.group('day'))
            elif m_album_index_found:
                s_album_sort = m_album_index_found.group('TSOA')
                s_album_name = m_album_index_found.group('TALB')
            elif m_album_year_only_found:
                s_album_name = m_album_year_only_found.group('TALB')
                s_album_date = m_album_year_only_found.group('TDRL')

                m_date_processed = re.match(p_process_date, s_album_date)
                if m_date_processed:
                    s_album_date = '{}-{}-{}'.format(m_date_processed.group('year'), m_date_processed.group('month'), m_date_processed.group('day'))

                # the sorting index will be the date
                s_album_sort = s_album_date
            elif args.debug:
                mainlogger.warn("Could not find an album index and/or year in " + s_album_name)

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
                    mainlogger.warn("Could not find a matching artist in " + filename_without_extension)
                s_track_number = s_disk_number = '0/0'

            if s_album_name == 'various albums':
                s_album_name = 'various ' + s_genre_name.lower() + ' albums'

            if s_album_name == '' or s_artist_name == '' or s_genre_name == '':
                mainlogger.error('For file ' + current_file + ': cannot extract album <' + s_album_name +
                                 '>, artist <' + s_artist_name + '> or genre <' + s_genre_name + '> information')

            # TAGGING #
            try:
                o_current_tags = ID3(current_file)
            except ID3NoHeaderError:
                # create ID3 tag if not present
                mainlogger.warn("No ID3 header found. Adding ID3 header.")
                o_current_tags = ID3()
            except Exception as err:
                mainlogger.error('For file ' + current_file + ', found exception "' + str(err) + '"')
                continue

            o_tags_to_set = ID3()
            o_tags_to_set.add(TCON(encoding=Encoding.UTF8, text=s_genre_name))  # Genre
            o_tags_to_set.add(TPE1(encoding=Encoding.UTF8, text=s_artist_name))  # Artist
            o_tags_to_set.add(TALB(encoding=Encoding.UTF8, text=s_album_name))  # Album
            o_tags_to_set.add(TDRL(encoding=Encoding.UTF8, text=s_album_date))  # Album
            o_tags_to_set.add(TPE2(encoding=Encoding.UTF8,
                                   text=s_album_artist_name))  # Album artist (in brackets, for VA albums)
            o_tags_to_set.add(TSOA(encoding=Encoding.UTF8, text=s_album_sort))  # Album sort number
            o_tags_to_set.add(TRCK(encoding=Encoding.UTF8, text=s_track_number))
            o_tags_to_set.add(TIT2(encoding=Encoding.UTF8, text=s_track_name))
            o_tags_to_set.add(
                    TSOT(encoding=Encoding.UTF8, text=s_track_number + '.' + s_disk_number))  # Track sort number
            o_tags_to_set.add(TPOS(encoding=Encoding.UTF8, text=s_disk_number))
            o_tags_to_set.add(TFLT(encoding=Encoding.UTF8, text='MPG/3'))

            mainlogger.debug("BGN tag removal")
            if args.remove_tags:

                l_tags_to_remove = [e for e in o_current_tags.keys() if e not in o_tags_to_set.keys()]
                mainlogger.debug("l_tags_to_remove -> " + str(l_tags_to_remove))

                for s_current_tag_to_remove in l_tags_to_remove:
                    # remove all tags not in the o_current_tags list
                    if args.verbose:
                        mainlogger.info("Deleting frame " + s_current_tag_to_remove)
                    o_current_tags.delall(s_current_tag_to_remove)
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

            mainlogger.debug("END tag removal")
            mainlogger.info("Tags removed")

            mainlogger.debug("Setting tags")
            for sCurrentTag in o_tags_to_set:
                o_current_tags.add(o_tags_to_set[sCurrentTag])
            mainlogger.debug("Tags are all set")

            mainlogger.debug("Saving file")
            try:
                o_current_tags.save(filename=current_file, v1=0, v2_version=4)
            except:
                mainlogger.error("Unable to save tags for file {}".format(current_file))

            mainlogger.debug("Save done")

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
                mainlogger.info("adding " + s_track_directory + " for cover search")
                # add the current directory to the list of directories to process for cover art
                dict_missing_cover_directories[s_track_directory] = [s_artist_name, s_album_name]

    display_progress(i_number_of_files_processed, i_number_of_files_to_process, last_line=True)

    if len(dict_missing_cover_directories) > 0:
        mainlogger.info("fetching covers")
        cover_url = CoverFetcher(dict_missing_cover_directories)
        cover_url.set_logger_level(mainlogger.getEffectiveLevel())
        cover_url.go_fetch()


if __name__ == "__main__":
    main()
