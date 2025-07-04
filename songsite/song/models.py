from django.db import models

# Create your models here.

class Artist(models.Model):

    """The model of an artist.
    
    This class is the model of artists in this site. There are two types of artists in this site:
    the ones who have a specific page for their introduction, and the ones who just have their 
    names appear in the site because he/she is one of the artists who made contributions in a song
    in this site.  

    Attributes:
        name (CharField): 
            the artist's name. It is the only required attribute because this site shows the name
            of both types of artists
        alias (CharField):
            only occured for the artists who have their intro and has other names
        original_id (CharField):
            the artist's id in the original website (for the many to many relation link)
        intro (CharField):
            the artist's intro, occured only for the artists who have their intro
        history (CharField):
            the artist's hitstory, occured only for the artists who have intro
            in this site and have history part in the original site
        master_work (CharField):
            the artist's master work, occured only for the artists who have intro
            in this site and have master work part in the original site
        milestones (CharField):
            the artist's milestones, occured only for the artists who have intro in
            this site and have milestones part in the original site
        url (CharField):
            the url of the artist's original webpage, occured only for the artists who have
            intro in this site
    """

    name = models.CharField(max_length=50)
    alias = models.CharField(max_length=50, null=True, blank=True)
    original_id = models.CharField(max_length=15, null=True, blank=True)
    intro = models.CharField(max_length=2000, null=True, blank=True)
    history = models.CharField(max_length=10000, null=True, blank=True)
    master_work = models.JSONField(default=list, null=True, blank=True)
    milestones = models.JSONField(default=list, null=True, blank=True)
    original_url = models.CharField(max_length=50, null=True, blank=True)

class Song(models.Model):

    """The model of a song

    This class is the model of songs in this site. Its attributes contain information about the song

    Attributes:
        name (CharField): the song's name
        alias (CharField): the song's other name (if it has one)
        original_id (CharField): the song's id in the original website (for the manytomany relation link)
        original_url (CharField): the song's url in the original website
        artist (ManyToManyField): the artist contributed for the song
        lyrics (CharField): the lyrics of the song
    """

    name = models.CharField(max_length=50)
    alias = models.CharField(max_length=50, null=True, blank=True)
    original_id = models.CharField(max_length=15)
    original_url = models.CharField(max_length=50)
    artist = models.ManyToManyField('Artist')
    lyrics = models.CharField(max_length=2000)

class Comment(models.Model):

    """The model of a comment

    This class is the model of a comment in this site. You can make comments under any song.

    Attributes:
        song (ForeignKey): which song is this comment under
        user (CharField): the user of this comment
        comment_text (CharField): the text in the comment
        pub_date (DateTimeField): the publication date and time of this comment
    """

    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    user = models.CharField(max_length=50)
    comment_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('发布时间', auto_now_add=True)

class SongSegment(models.Model):

    """The song segment model (for the inverted index of songs)

    This model is for all song segments/tokens appear in the song objects of this site.

    Attributes:
        token (CharField): the token for index
        df (PositiveIntegerField): document frequency
    """

    token = models.CharField(max_length=20, unique=True) # setting unique=True for making the index
    df = models.PositiveIntegerField()

class SongIndex(models.Model):

    """The song index model

    This class is the index for recording each token has appeared in what song document with
    how many times. 

    Attributes:
        article_id (PositiveIntegerField): the song document's id
        tf (PositiveIntegerField): term frequency in this document
        song_segment (ForeignKey): the corresponding song segment/token
    """

    article_id = models.PositiveIntegerField()
    tf = models.PositiveIntegerField()
    song_segment = models.ForeignKey(SongSegment, on_delete=models.CASCADE)

class ArtistSegment(models.Model):

    """The artist segment model (for the inverted index of songs)

    This model is for all artist segments/tokens appear in the artist objects of this site.

    Attributes:
        token (CharField): the token for index
        df (PositiveIntegerField): document frequency
    """

    token = models.CharField(max_length=20, unique=True)
    df = models.PositiveIntegerField()

class ArtistIndex(models.Model):

    """The artist index model

    This class is the index for recording each token has appeared in what artist document with
    how many times. 

    Attributes:
        article_id (PositiveIntegerField): the artist document's id
        tf (PositiveIntegerField): term frequency in this document
        song_segment (ForeignKey): the corresponding song segment/token
    """

    article_id = models.PositiveIntegerField()
    tf = models.PositiveIntegerField()
    artist_segment = models.ForeignKey(ArtistSegment, on_delete=models.CASCADE)