# recursemp3

# REQUIREMENTS
recursemp3 has been developed under Python 3.4. It will require the following python libraries to work: 
 * mutagen (edition of audio file metainformation)
 * urllib2 (used in fetching the cover art)

# USAGE
`recursemp3 -d <directory name> [-v|--verbose] [--debug] [-r|--remove] [-c|--cover-only] [-n|--no-cover]`

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
Unless the parameter ### has been set, for each mp3 directory found, recursemp3 will try to fetch the cover art from `last.fm`, in format "extralarge". To do so, it will send both artist name and album name to the `last.fm` API, and save the file in the mp3 file directory as `cover.<ext>`.

This process is multithreaded, and done after the path parsing (`os.walk`) has been done. It's using an HTTP pool of 5 simultaneous connections, and thus 5 threads are used.
