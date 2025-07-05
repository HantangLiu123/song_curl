import json
import glob
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from song.models import Song, Artist
import os
import re

class Command(BaseCommand):

    """this command is for loading the songs and artists in the data base and construct their relations"""

    def add_arguments(self, parser: CommandParser) -> None:

        """arguments of this command"""

        # path to the song information folder, required
        parser.add_argument(
            '--song_info_path',
            type=str,
            required=True,
            help="directory of songs' information",
        )

        # path to the artist information folder, required
        parser.add_argument(
            '--artist_info_path',
            type=str,
            required=True,
            help="directory of artists' information",
        )

        # clear all information before adding new songs/artists
        parser.add_argument(
            '--clear',
            action='store_true',
            help="clear all songs and artists",
        )

    def handle(self, *args, **options) -> None: # type: ignore

        """the main function of this command."""

        # get the path of the information
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

        # get the files contain the information
        song_jsons = glob.glob(f"{song_info_dir}/song_intro/*.json") # files of songs
        artist_jsons = glob.glob(f"{artist_info_dir}/artist_intro/*.json") # files of artists
        # files of the song ids of each artist
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

        # loads all songs in
        for song in song_jsons:
            with open(song, "r", encoding='utf-8') as f:
                song_data = json.load(f)
            self.process_song_data(song_data)

        # loads all complete artists (with intro, pirctures, urls, etc.) in
        for artist in artist_jsons:
            with open(artist, "r", encoding='utf-8') as f:
                artist_data = json.load(f)
            self.process_artist_data(artist_data)

        # for each artist, link their songs in the site  
        for relation in artist_songs:
            with open(relation, "r", encoding='utf-8') as f:
                artist_song_relation = json.load(f)
                # since the file name is in the pattern of 'artist{artist_id}songs', we can
                # extract the file_name from the full path and then get the artist_id
                file_name = re.search(r'artist[0-9]+songs', relation).group(0)
                artist_org_id = file_name[len('artist'):len(file_name) - len('songs')]
            self.add_songs_to_artist(artist_song_relation, artist_org_id)

        # for each song, link their artists in the site
        for song in song_jsons:
            with open(song, "r", encoding='utf-8') as f:
                song_data = json.load(f)
            self.add_artists_to_song(song_data)

    def process_song_data(self, song_data: dict) -> None:

        """store the data from the loaded song dictionary into the data base"""

        song_name = song_data['name']
        song_alias = song_data.get('alias') # a song may have no alias, use get method
        org_url = song_data['url']
        lyrics = song_data['lyrics']
        # get rid of the "收起" at the end of the lyrics string
        if re.search(r'收起$', lyrics) is not None:
            lyrics = lyrics[:len(lyrics) - 2]
        lyrics = lyrics.replace('\n', '<br>')
        org_id = str(song_data['id']) # cast original id into string (the type in the Song object)

        # check whether the song is already created, if not, create it
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

        """store the data from the artist dictionary into the data base"""

        artist_name = artist_data['name']
        # an artist may have no alias or multiple alias
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

        # check whether the artist is already created, if not, create it
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

        """add the songs in the list to the corresponding artist.
        
        This function adds songs in the artist_song_relation to the artist whose original id
        is the artist_original id.

        Args:
            artist_song_relation (list[int]): stores the songs' original id correspond to the artist
            artist_org_id (str): the artist's original id
        """

        artist = Artist.objects.get(original_id=artist_org_id)
        for song_id in artist_song_relation:
            song = Song.objects.get(original_id=str(song_id))
            if artist.song_set.filter(pk=song.id).exists():
                # avoid the condition that the song is already added to the artist
                self.stdout.write(f"song{song_id} is already added to artist{artist_org_id}")
            else:
                artist.song_set.add(song)
                self.stdout.write(f"adding song{song_id} to artist{artist_org_id}")

    def add_artists_to_song(self, song_data: dict) -> None:

        """adding artist to the song according to the song_data"""

        song_org_id = str(song_data['id'])
        artist_id_list = song_data['artist id list']
        song = Song.objects.get(original_id=song_org_id)

        # first adding the complete artists (artists with intro, urls, pictures, etc.)
        for artist_id in artist_id_list:
            # the complete artists have all been created, so filtering out the artists that are not in
            # the database now. Then, avoid the condition that the artists are already added to the song
            # by filtering the spng.artist.
            if not song.artist.filter(original_id=str(artist_id)).exists() \
            and Artist.objects.filter(original_id=str(artist_id)).exists():
                artist = Artist.objects.get(original_id=str(artist_id))
                song.artist.add(artist)
                self.stdout.write(f"adding artist{artist_id} to song{song_org_id}")
        artist_name_list = song_data['artist list']
        for artist_name in artist_name_list:
            # if the name of the artist is in the artist name list, but it's still not added to the song,
            # this artist has to be incomplete, so create an Artist object for him/her only with the name,
            # and add to the song
            if not song.artist.filter(name=artist_name).exists():
                artist = Artist.objects.create(name=artist_name)
                artist.save()
                song.artist.add(artist)
                self.stdout.write(f"adding artist{artist_name} to song{song_org_id}")