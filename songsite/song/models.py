from django.db import models

# Create your models here.

class Artist(models.Model):
    name = models.CharField(max_length=50)
    alias = models.CharField(max_length=50, null=True, blank=True)
    original_id = models.CharField(max_length=15, null=True, blank=True) # id in the original website
    intro = models.CharField(max_length=2000, null=True, blank=True)
    history = models.CharField(max_length=10000, null=True, blank=True)
    master_work = models.JSONField(default=list, null=True, blank=True)
    milestones = models.JSONField(default=list, null=True, blank=True)
    original_url = models.CharField(max_length=50, null=True, blank=True)

class Song(models.Model):
    name = models.CharField(max_length=50)
    alias = models.CharField(max_length=50, null=True, blank=True)
    original_id = models.CharField(max_length=15)
    original_url = models.CharField(max_length=50)
    artist = models.ManyToManyField('Artist')
    lyrics = models.CharField(max_length=2000)

class Comment(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    user = models.CharField(max_length=50)
    comment_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('发布时间', auto_now_add=True)