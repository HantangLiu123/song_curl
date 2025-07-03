from typing import Any
from django.core.management.base import BaseCommand, CommandParser
from song.models import Song, Artist, SongSegment, SongIndex, ArtistSegment, ArtistIndex
import jieba

class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--clear',
            action="store_true",
            help="clear all existing indexes"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if options['clear']:
            self.stdout.write('clearing existing indexes')
            SongSegment.objects.all().delete()
            ArtistSegment.objects.all().delete()

        
    def create_song_segments(self):
        songs = Song.objects.all()
        for song in songs:
            song_segments = self.segments_in_song(song)
            song_segments_info = self.analyze_segments(song_segments)
            for segment in song_segments_info:
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

                seg_obj.songindex_set.create(article_id=song.id, tf=song_segments_info[segment])

    def segments_in_song(self, song: Song) -> list[str]:
        segments = []
        segments.extend(self.segments_in_str(song.name))
        if song.alias is not None:
            segments.extend(self.segments_in_str(song.alias))
        segments.extend(self.segments_in_str(song.lyrics))
        for artist in song.artist.all():
            segments.extend(self.segments_in_str(artist.name))
        return segments

    def segments_in_str(self, in_str: str) -> list[str]:
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
        segment_data = {}
        for segment in segments:
            if segment in segment_data:
                segment_data[segment] += 1
            else:
                segment_data[segment] = 1
        return segment_data
    
    def create_artist_segments(self):
        artists = Artist.objects.filter(original_url__isnull=False)
        for artist in artists:
            artist_segments = self.segments_in_artist(artist)
            artist_segments_info = self.analyze_segments(artist_segments)
            for segment in artist_segments_info:
                sej_obj, created = ArtistSegment.objects.get_or_create(
                    token=segment,
                    defaults={'df': 1}
                )
                if created:
                    self.stdout.write(f"new artist segment {segment} created")
                else:
                    self.stdout.write(f"adding df for artist segment {segment}")
                    sej_obj.df += 1
                    sej_obj.save()

                sej_obj.artistindex_set.create(article_id=artist.id, tf=artist_segments_info[segment])

    def segments_in_artist(self, artist: Artist) -> list[str]:
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