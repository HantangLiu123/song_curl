from typing import Any
from django.db.models.query import QuerySet
from django.db.models import Case, When
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Song, Artist, Comment, SongSegment, SongIndex, ArtistSegment, ArtistIndex
import jieba
import math
import time

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

def check(request):
    query = request.GET.get('query')
    class_ = request.GET.get('class_')
    start_time = time.time()
    if query is None and class_ is None:
        return render(request, 'song/check.html')
    elif query is None:
        return render(
            request,
            'song/check.html',
            {
                'error_message': '请输入您的问题'
            }
        )
    elif class_ is None:
        return render(
            request,
            'song/check.html',
            {
                'error_message': '请输入您想要查找的类别（歌曲/歌手）'
            }
        )
    else:
        query_seg = jieba.cut_for_search(query)
        found_doc = False
        tfidf_list = []

        def get_score(tfidf_list: list[dict[int, float]]) -> dict[int, float]:
            score = {}
            for tfidf in tfidf_list:
                for doc_id in tfidf:
                    if doc_id in score:
                        score[doc_id] += tfidf[doc_id]
                    else:
                        score[doc_id] = tfidf[doc_id]
            return score

        if class_ == 'song':
            N = Song.objects.count()
            for seg in query_seg:
                try:
                    song_seg = SongSegment.objects.get(token=seg)
                except SongSegment.DoesNotExist:
                    continue
                else:
                    if not found_doc:
                        found_doc = True
                    index_set = song_seg.songindex_set.all()
                    idf = math.log(N / song_seg.df)
                    tfidf = {}
                    for index in index_set:
                        tfidf[index.article_id] = index.tf * idf
                    tfidf_list.append(tfidf)
        else:
            N = Artist.objects.filter(original_url__isnull=False).count()
            for seg in query_seg:
                try:
                    artist_seg = ArtistSegment.objects.get(token=seg)
                except ArtistSegment.DoesNotExist:
                    continue
                else:
                    if not found_doc:
                        found_doc = True
                    index_set = artist_seg.artistindex_set.all()
                    idf = math.log(N / artist_seg.df)
                    tfidf = {}
                    for index in index_set:
                        tfidf[index.article_id] = index.tf * idf
                    tfidf_list.append(tfidf)

        if not found_doc:
            return render(
                request,
                'song/check.html',
                {
                    'error_message': "没有结果符合您的问题"
                }
            )
        
        def get_doc_list(cls, doc_id_list: list[int]) -> Any:
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(doc_id_list)])
            return cls.objects.filter(id__in=doc_id_list).order_by(preserved)
        
        score = get_score(tfidf_list)
        doc_id_list = sorted(score, key=lambda x: score[x], reverse=True)
        if class_ == 'song':
            doc_list = get_doc_list(Song, doc_id_list)
        else:
            doc_list = get_doc_list(Artist, doc_id_list)
        end_time = time.time()
        elapsed_time = end_time - start_time

        return render(
            request,
            'song/check.html',
            {
                'doc_list': doc_list,
                'elapsed_time': f"{elapsed_time:.3f}",
                'cls': class_
            }
        )
