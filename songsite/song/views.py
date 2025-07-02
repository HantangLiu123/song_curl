from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Song, Artist, Comment

# Create your views here.

class SongList(generic.ListView):
    model = Song
    template_name = 'song/songList.html'
    context_object_name = 'all_songs_list'
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Any]:
        return Song.objects.all()
    
def show_song_detail(request, song_id):
    song = get_object_or_404(Song, pk=song_id)
    comments = song.comment_set.order_by('-pub_date')
    return render(
        request,
        'song/songDetail.html',
        {
            'song': song,
            'comments': comments
        },
    )
    
class ArtistList(generic.ListView):
    model = Artist
    template_name = 'song/artistList.html'
    context_object_name = 'all_artists_list'
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Any]:
        return Artist.objects.filter(original_url__isnull=False)

class ArtistDetail(generic.DetailView):
    model = Artist
    template_name = 'song/artistDetail.html'

def comment(request, song_id):
    song = get_object_or_404(Song, pk=song_id)
    data = request.POST
    user = data['user']
    comment_text = data['comment_text']
    comment_obj = Comment(song=song, user=user, comment_text=comment_text)
    comments = song.comment_set.order_by('-pub_date')
    try:
        comment_obj.full_clean()
    except ValidationError:
        return render(
            request,
            'song/songDetail.html',
            {
                'song': song,
                'comments': comments,
                'error_message': '请再次检查您已填入了用户名和评论',
            }
        )
    else:
        comment_obj.save()
        return HttpResponseRedirect(reverse('song:song_detail', args=(song.id, )))
    
def del_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    song_id = int(request.POST['song_id'])
    comment.delete()
    return HttpResponseRedirect(reverse('song:song_detail', args=(song_id, )))
