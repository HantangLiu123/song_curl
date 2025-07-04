from typing import Any
from django.core.management.base import BaseCommand, CommandParser
from song.models import Song, Artist, SongSegment, SongIndex, ArtistSegment, ArtistIndex
import jieba

class Command(BaseCommand):

    """This command is for building the inverted index for the search/check function"""

    def add_arguments(self, parser: CommandParser) -> None:

        """arguments of the command"""

        # an argument for clearing the existing index before making new indexes
        parser.add_argument(
            '--clear',
            action="store_true",
            help="clear all existing indexes"
        )

    def handle(self, *args: Any, **options: Any) -> None:

        """the main function of this command"""

        if options['clear']:
            self.stdout.write('clearing existing indexes')
            SongSegment.objects.all().delete()
            ArtistSegment.objects.all().delete()
        self.create_song_segments()
        self.create_artist_segments()
        
    def create_song_segments(self):

        """creating index for song docs"""

        songs = Song.objects.all()
        for song in songs:
            # extract all segments from the song, and put them in a dict where the key is
            # the token and the item is the number of appearance
            song_segments = self.segments_in_song(song)
            song_segments_info = self.analyze_segments(song_segments)
            for segment in song_segments_info:
                # if the segment index has not been created, create a new one; if
                # it's been created, add its df value.
                seg_obj, created = SongSegment.objects.get_or_create(
                    token=segment,
                    defaults={'df': 1}
                )
                if created:
                    self.stdout.write(f"new song segment {segment} created")
                else:
                    self.stdout.write(f"adding df for song segment {segment}")
                    seg_obj.df += 1
                    seg_obj.save()

                #adding the doc index for this segment
                seg_obj.songindex_set.create(article_id=song.id, tf=song_segments_info[segment])

    def segments_in_song(self, song: Song) -> list[str]:

        """extracting a list of tokens from a song.
        
        This function extracts a list of tokens from a song object, including from its
        name, alias, lyrics, and artists about it.

        Args:
            song (Song): the song that will be analyzed

        Returns:
            segments (list[str]): the list of tokens extracted
        """

        segments = []
        segments.extend(self.segments_in_str(song.name))
        if song.alias is not None:
            segments.extend(self.segments_in_str(song.alias))
        segments.extend(self.segments_in_str(song.lyrics))
        for artist in song.artist.all():
            segments.extend(self.segments_in_str(artist.name))
        return segments

    def segments_in_str(self, in_str: str) -> list[str]:

        """extract tokens from a string.
        
        This function extract tokens (except the too common onse) from the input string.

        Args:
            in_str (str): the input string
        
        Returns:
            tokens/segments_list (list[str]): the list of tokens
        """

        seg_list = jieba.cut_for_search(in_str)
        segments = []
        for segment in seg_list:
            if len(segment.strip()) > 1:
                segments.append(segment.strip())

        common_chars = {',', ' ', '.', '"', "'", '，', '‘', '’', '“', '”', '。', ':', '：', '\n', '?', 
                        '？', '!', '！', '(', ')', '（', '）', '-', '——', ';', '；'}
        for char in in_str:
            if char not in common_chars:
                segments.append(char)
        return segments
    
    def analyze_segments(self, segments: list[str]) -> dict[str, int]:

        """Converts the list of tokens in to a dict recording the frequency of each token.

        This function makes a dict that records the frequency of each token appeared in the segments/tokens
        list. 

        Args:
            segments (list[str]): the segments/tokens list of a doc

        Returns:
            segment_data (dict[str, int]): the frequency of appearance of each token in the input list
        """

        segment_data = {}
        for segment in segments:
            if segment in segment_data:
                segment_data[segment] += 1
            else:
                segment_data[segment] = 1
        return segment_data
    
    def create_artist_segments(self):

        """creating index for artist docs"""

        # should only considers the artist with complete information
        artists = Artist.objects.filter(original_url__isnull=False)
        for artist in artists:
            # extract all segments from the artist, and put them in a dict where the key is
            # the token and the item is the number of appearance
            artist_segments = self.segments_in_artist(artist)
            artist_segments_info = self.analyze_segments(artist_segments)
            for segment in artist_segments_info:
                # if the segment index has not been created, create a new one; if
                # it's been created, add its df value.
                seg_obj, created = ArtistSegment.objects.get_or_create(
                    token=segment,
                    defaults={'df': 1}
                )
                if created:
                    self.stdout.write(f"new artist segment {segment} created")
                else:
                    self.stdout.write(f"adding df for artist segment {segment}")
                    seg_obj.df += 1
                    seg_obj.save()

                #adding the doc index for this segment
                seg_obj.artistindex_set.create(article_id=artist.id, tf=artist_segments_info[segment])

    def segments_in_artist(self, artist: Artist) -> list[str]:

        """Extracting a list of tokens from an artist.
        
        This function extracts a list of tokens from an artist object, including from its 
        name, alias, intro, history, master work, and milestones.

        Args:
            artist (Artist): the artist that will be analyzed

        Returns:
            segments (list[str]): the list of tokens extracted
        """

        segments = []
        segments.extend(self.segments_in_str(artist.name))
        if artist.alias is not None:
            segments.extend(self.segments_in_str(artist.alias))
        if artist.intro is not None:
            segments.extend(self.segments_in_str(artist.intro))
        if artist.history is not None:
            segments.extend(self.segments_in_str(artist.history))
        if artist.master_work is not None:
            for work in artist.master_work:
                segments.extend(self.segments_in_str(work))
        if artist.milestones is not None:
            for milestone in artist.milestones:
                segments.extend(self.segments_in_str(milestone))
        return segments