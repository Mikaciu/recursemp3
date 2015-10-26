# recursemp3
recurseMP3 will tag the MP3 files according to their tree.
Basically, it can be one of those combinations : 
 * <genre>/<artist>/<album>/<track name>
 * <genre>/<artist>/<album index>.<album>/<track number>.<track name>
 * <genre>/<artist>/<album index>.<album>/<disk number>.<track number>.<track name>

The <track number> will be computed as follows : <current track number>/<number of tracks in medium>.
The <disk number> will be computed as follows : <current disk number>/<number of disks>.

If the artist is "various artists", the "album artist" frame will be set to "various lowercase(<genre>) artists".
If the album is "various albums", the "album" frame will be set to "various lowercase(<album>) albums".
