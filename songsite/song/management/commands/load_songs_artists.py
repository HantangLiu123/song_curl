import json
import glob
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from song.models import Song, Artist
import os
import re

class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--song_info_path',
            type=str,
            required=True,
            help="directory of songs' information",
        )
        parser.add_argument(
            '--artist_info_path',
            type=str,
            required=True,
            help="directory of artists' information",
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help="clear all songs and artists",
        )

    def handle(self, *args, **options) -> None: # type: ignore
        song_info_dir = options['song_info_path']
        artist_info_dir = options['artist_info_path']

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
            self.process_song_data(song_data)

        for artist in artist_jsons:
            with open(artist, "r", encoding='utf-8') as f:
                artist_data = json.load(f)
            self.process_artist_data(artist_data)
            
        for relation in artist_songs:
            with open(relation, "r", encoding='utf-8') as f:
                artist_song_relation = json.load(f)
                file_name = re.search(r'artist[0-9]+songs', relation).group(0)
                artist_org_id = file_name[len('artist'):len(file_name) - len('songs')]
            self.add_songs_to_artist(artist_song_relation, artist_org_id)

        for song in song_jsons:
            with open(song, "r", encoding='utf-8') as f:
                song_data = json.load(f)
            self.add_artists_to_song(song_data)

    def process_song_data(self, song_data: dict) -> None:
        song_name = song_data['name']
        song_alias = song_data.get('alias')
        org_url = song_data['url']
        lyrics = song_data['lyrics']
        if re.search(r'收起$', lyrics) is not None:
            lyrics = lyrics[:len(lyrics) - 2]
        lyrics = lyrics.replace('\n', '<br>')
        org_id = str(song_data['id'])
        song_to_create, created = Song.objects.get_or_create(
            original_id=org_id,
            defaults={
                'name': song_name,
                'alias': song_alias,
                'original_url': org_url,
                'lyrics': lyrics,
            }
        )
        if created:
            self.stdout.write(f"successfully created song{org_id}")
        else:
            self.stdout.write(f"song{org_id} already created")

    def process_artist_data(self, artist_data: dict) -> None:
        artist_name = artist_data['name']
        if 'alias' in artist_data:
            artist_alias = '，'.join(artist_data['alias'])
        else:
            artist_alias = None
        org_url = artist_data['url']
        org_id = str(artist_data['id'])
        artist_intro_block = artist_data['intro']
        artist_intro = artist_intro_block['intro']
        artist_history = artist_intro_block.get('history')
        artist_master_work = artist_intro_block.get('master work')
        artist_milestones = artist_intro_block.get('milestones')
        artist_to_create, created = Artist.objects.get_or_create(
            original_id=org_id,
            defaults={
                'name': artist_name,
                'alias': artist_alias,
                'original_url': org_url,
                'intro': artist_intro,
                'history': artist_history,
                'master_work': artist_master_work,
                'milestones': artist_milestones,
            }
        )
        if created:
            self.stdout.write(f"successfully created artist{org_id}")
        else:
            self.stdout.write(f"artist{org_id} already created")

    def add_songs_to_artist(self, artist_song_relation: list, artist_org_id: str) -> None:
        artist = Artist.objects.get(original_id=artist_org_id)
        for song_id in artist_song_relation:
            song = Song.objects.get(original_id=str(song_id))
            if artist.song_set.filter(pk=song.id).exists():
                self.stdout.write(f"song{song_id} is already added to artist{artist_org_id}")
            else:
                artist.song_set.add(song)
                self.stdout.write(f"adding song{song_id} to artist{artist_org_id}")

    def add_artists_to_song(self, song_data: dict) -> None:
        song_org_id = str(song_data['id'])
        artist_id_list = song_data['artist id list']
        song = Song.objects.get(original_id=song_org_id)
        for artist_id in artist_id_list:
            if not song.artist.filter(original_id=str(artist_id)).exists() \
            and Artist.objects.filter(original_id=str(artist_id)).exists():
                artist = Artist.objects.get(original_id=str(artist_id))
                song.artist.add(artist)
                self.stdout.write(f"adding artist{artist_id} to song{song_org_id}")
        artist_name_list = song_data['artist list']
        for artist_name in artist_name_list:
            if not song.artist.filter(name=artist_name).exists():
                artist = Artist.objects.create(name=artist_name)
                artist.save()
                song.artist.add(artist)
                self.stdout.write(f"adding artist{artist_name} to song{song_org_id}")