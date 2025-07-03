from django.contrib import admin
from .models import Song, Artist, Comment, SongSegment, SongIndex, ArtistSegment, ArtistIndex

# Register your models here.

admin.site.register(Song)
admin.site.register(Artist)
admin.site.register(Comment)
admin.site.register(SongSegment)
admin.site.register(SongIndex)
admin.site.register(ArtistSegment)
admin.site.register(ArtistIndex)