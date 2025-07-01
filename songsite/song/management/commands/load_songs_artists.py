import json
import glob
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from song.models import Song, Artist
import os

class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--song_info_path',
            type='str',
            help="directory of songs' information",
        )
        parser.add_argument(
            '--artist_info_path',
            type='str',
            help="directory of artists' information",
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help="clear all songs and artists",
        )

    def handle(self, *args: json.Any, **options: json.Any) -> str | None: # type: ignore
        song_info_dir = options['song_info_dir']
        artist_info_dir = options['artist_info_dir']

        if not os.path.exists(song_info_dir):
            self.stdout.write(
                self.style.ERROR(f"Can't find {song_info_dir}")
            )
        
        if not os.path.exists(artist_info_dir):
            self.stdout.write(
                self.style.ERROR(f"Can't find {artist_info_dir}")
            )

        if options['clear']:
            self.stdout.write('clearing all data')
            Song.objects.all().delete()
            Artist.objects.all().delete()

        song_jsons = glob.glob(f"{song_info_dir}/song_intro/*.json")
        artist_jsons = glob.glob(f"{artist_info_dir}/artist_intro/*.json")
        artist_songs = glob.glob(f"{artist_info_dir}/artist_song_ids/*.json")

        if not song_jsons:
            self.stdout.write(
                self.style.WARNING(f'No jsons in {song_info_dir}/song_intro')
            )
        
        if not artist_jsons:
            self.stdout.write(
                self.style.WARNING(f'No jsons in {artist_info_dir}/artist_intro')
            )

        if not artist_songs:
            self.stdout.write(
                self.style.WARNING(f'No jsons in {artist_info_dir}/artist_song_ids')
            )

        for song in song_jsons:
            with open(song, "r", encoding='utf-8') as f:
                song_data = json.load(f)
            
            song_name = song_data['name']
            if song_data['alias']:
                song_alias = song_data['alias']
            else:
                song_alias = None
            
        