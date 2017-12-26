# recursemp3

# REQUIREMENTS
recursemp3 has been developed under Python 3.4. It will require the following python libraries to work:
 * mutagen (edition of audio file metainformation)
 * urllib3 (used in fetching the cover art)
 * certifi (also used in fetching the cover art)
 * argparse (for argument handling)
 * colorama (for pretty output)
 * colorlog (for pretty logging output)
 * tqdm (for the progress bar)

# USAGE
```
usage: recursemp3.py [-h] [-v | -q | -d] [-r] [-n | -c]
                     [directories [directories ...]]

Process all MP3 files contained in the argument, and tag them
<genre>/<artist>/[<albumindex>.]<album>/[<trackindex>.]<trackname>

positional arguments:
  directories        The list of directories to process. If none is chosen,
                     the current directory will be used instead.

optional arguments:
  -h, --help         show this help message and exit
  -v, --verbose      Increase output verbosity
  -q, --quiet        Decrease output verbosity
  -d, --debug        Insanely huge amount of output. Do not use on large trees
  -r, --remove-tags  Remove existing tags before applying new tags
  -n, --no-cover     Do not try to fetch the album art (way much faster)
  -c, --only-cover   Only fetch the album art (needs an Internet connection)
```

# What does it do ?
## Tagging
recurseMP3 will tag the MP3 files according to their tree.
Basically, it can be one of those combinations :
 * `<genre>/<artist>/<album>/<track name>`
 * `<genre>/<artist>/<album index>.<album>/<track number>.<track name>`
 * `<genre>/<artist>/<album index>.<album>/<disk number>.<track number>.<track name>`

The `<track number>` field will be computed as follows : `<current track number>/<number of tracks in medium>`.
The `<disk number>` field will be computed as follows : `<current disk number>/<number of disks>`.

If the artist is "various artists", the "album artist" frame will be set to "various lowercase(`<genre>`) artists".
If the album is "various albums", the "album" frame will be set to "various lowercase(`<album>`) albums".

## Cover retrieval
Unless the parameter --no-cover has been set, for each mp3 directory found, recursemp3 will try to fetch the cover art from `last.fm`, in format "extralarge". To do so, it will send both artist name and album name to the `last.fm` API, and save the file in the mp3 file directory as `cover.<ext>`.

This process is multithreaded, and done after the path parsing (`os.walk`) has been done. It's using an HTTP pool of 5 simultaneous connections, and thus 5 threads are used.
