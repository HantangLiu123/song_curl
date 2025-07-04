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

    """The class for the song list view.

    This class, inherited from ListView, constructs the view for the song list.

    Attributes:
        model (class): the model used by this view
        template_name (str): the name of the template used by this view
        context_object_name (str):
            the name of the context object that contains the returns from
            the get_queryset function
        paginate_by (int): how many songs should appear in each page
        get_queryset (QuerySet[Any]): returns the list that would be shown in the view
    """

    model = Song
    template_name = 'song/songList.html'
    context_object_name = 'all_songs_list'
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Any]:
        return Song.objects.all()
    
def show_song_detail(request, song_id):

    """Function of the song detail's view

    This function constructs the view of a song's detail, which contains the information
    of the song and the comments under it

    Args:
        request: the request to the site
        song_id: the id of the song in this site
    """

    song = get_object_or_404(Song, pk=song_id)
    comments = song.comment_set.order_by('-pub_date') # order by publication time from new to old
    return render(
        request,
        'song/songDetail.html',
        {
            'song': song,
            'comments': comments
        },
    )
    
class ArtistList(generic.ListView):

    """The class for the artist list view.

    This class, inherited from ListView, constructs the view for the artist list.

    Attributes:
        model (class): the model used by this view
        template_name (str): the name of the template used by this view
        context_object_name (str):
            the name of the context object that contains the returns from
            the get_queryset function
        paginate_by (int): how many songs should appear in each page
        get_queryset (QuerySet[Any]):
            returns the list that would be shown in the view. In this function, the artist without
            original url is filtered out because all Artist objects that only names in this site,
            which should not be in the list, do not have original_url.
    """

    model = Artist
    template_name = 'song/artistList.html'
    context_object_name = 'all_artists_list'
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Any]:
        return Artist.objects.filter(original_url__isnull=False)

class ArtistDetail(generic.DetailView):

    """The class for the artist detail.

    This class constructs the view of an artist's detail.

    Attributes:
        model (class): the model used in this view
        template (str): the name of the template needed to be rendered
    """

    model = Artist
    template_name = 'song/artistDetail.html'

def comment(request, song_id):

    """The function for making comments

    This function enables users to make comments under songs. In the post request, it will get
    the username and text from the user. If there are missing information, it will show an error
    message on the page that prompt the user to input all needed information. Then, after getting
    full information, it will show the comments under the song.

    Args:
        request:
            the post request to the website. In this function, a complete request contains username
            ('user') and text ('comment_text')
        song_id: the id of the song that will be commented
    """

    song = get_object_or_404(Song, pk=song_id)
    data = request.POST
    user = data['user']
    comment_text = data['comment_text']
    comment_obj = Comment(song=song, user=user, comment_text=comment_text)
    comments = song.comment_set.order_by('-pub_date') # order by publication time from new to old
    try:
        # try to check if the comment object is complete
        comment_obj.full_clean()
    except ValidationError:
        # if not, render the same song page with the error message
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
        # redirect to the song page with the new comment
        comment_obj.save()
        return HttpResponseRedirect(reverse('song:song_detail', args=(song.id, )))
    
def del_comment(request, comment_id):

    """The delete comment function.

    This function enables users to delete any comment seen under a song. After
    deleting the comment object, it will redirect to the song page again without
    the deleted comment.

    Args:
        request: the request to the website
        comment_id: the id of the comment will be deleted
    """

    comment = get_object_or_404(Comment, pk=comment_id)
    song_id = int(request.POST['song_id']) # get which song that the deleted comment is under
    comment.delete()
    return HttpResponseRedirect(reverse('song:song_detail', args=(song_id, )))

def check(request):

    """The search/check function.

    This function enables users to search/check on songs/artists by entering a query. Then, 
    this query will be cut in to tokens by the jiaba package, and each token will have a tfidf
    score for each doct. Lastly, each doc's score on each token will be added together, and the 
    function will give a found_doc list to the render function ordered by the score from high
    to low. This function will also record the time for the whole search process.

    Args:
        request:
            the get request to the site. In this function, a complete request contains the query
            and the which set of doc (song/artist) does the user wants to search in ('class_')
    """

    query = request.GET.get('query')
    class_ = request.GET.get('class_')
    start_time = time.time() # record the start time
    if query is None and class_ is None:
        # this happens when the user first goes to the search url, so no information is sent to 
        # the render function
        return render(request, 'song/check.html')
    elif query is None or query.strip() == "":
        # the query is empty, prompt the user for query
        return render(
            request,
            'song/check.html',
            {
                'error_message': '请输入您的问题'
            }
        )
    elif class_ is None:
        # the class is empty, prompt the user for the class (song/artist)
        return render(
            request,
            'song/check.html',
            {
                'error_message': '请输入您想要查找的类别（歌曲/歌手）'
            }
        )
    else:
        # the request is complete
        query_seg = jieba.cut_for_search(query)
        found_doc = False # a flag for whether there is doc found
        tfidf_list = [] # the tfidf for each token in each doc

        def get_score(tfidf_list: list[dict[int, float]]) -> dict[int, float]:

            """the tfidf to doc score convert function.

            This function converts the tfidf for each token in each doc into the scores of
            each doc got on this query.

            Args:
                tfidf_list (list[dict[int, float]]):
                    the tfidf for each token in each doc. The list is for each token. In each dictionary,
                    the int part is the doc_num, and the float part is the tfidf value.

            Returns:
                score (dict[int, float]): the score of each_doc on this query.
            """

            score = {}
            # adding the score of each doc on all tokens together
            for tfidf in tfidf_list:
                for doc_id in tfidf:
                    if doc_id in score:
                        score[doc_id] += tfidf[doc_id]
                    else:
                        score[doc_id] = tfidf[doc_id]
            return score

        if class_ == 'song':
            # client chose to search on songs, the total number should be the total number
            # of songs.
            N = Song.objects.count()
            for seg in query_seg:
                try:
                    song_seg = SongSegment.objects.get(token=seg)
                except SongSegment.DoesNotExist:
                    # the segment is not in the index, continue to next
                    continue
                else:
                    # found the segment, calculate the tfidf for this segment/token in each
                    # document, and append this dict to the tfidf_list
                    if not found_doc:
                        found_doc = True
                    index_set = song_seg.songindex_set.all()
                    idf = math.log(N / song_seg.df)
                    tfidf = {}
                    for index in index_set:
                        tfidf[index.article_id] = index.tf * idf
                    tfidf_list.append(tfidf)
        else:
            # the client chose to search on artists, the total number of doc should be the 
            # total number of complete artists (who have intros, urls...)
            N = Artist.objects.filter(original_url__isnull=False).count()
            for seg in query_seg:
                try:
                    artist_seg = ArtistSegment.objects.get(token=seg)
                except ArtistSegment.DoesNotExist:
                    # the segment is not in the index, continue to next
                    continue
                else:
                    # found the segment, calculate the tfidf for this segment/token in each
                    # document, and append this dict to the tfidf_list
                    if not found_doc:
                        found_doc = True
                    index_set = artist_seg.artistindex_set.all()
                    idf = math.log(N / artist_seg.df)
                    tfidf = {}
                    for index in index_set:
                        tfidf[index.article_id] = index.tf * idf
                    tfidf_list.append(tfidf)

        # if no doc is found by this query, return a page with an error message
        if not found_doc:
            return render(
                request,
                'song/check.html',
                {
                    'error_message': "没有结果符合您的问题"
                }
            )
        
        def get_doc_list(cls, doc_id_list: list[int]) -> Any:

            """the function getting the result doc list by the doc id list.

            This function returns a doc list according to the input doc id list ordered by the 
            importance score.

            Args:
                cls (class): witch type of doc should be got (Song/Artist)
                doc_id_list (list[int]): the ordered list of doc ids

            Returns:
                doc_list
            """

            # create an ordering index using enumerate, and switch the posistion of the index with
            # When() function so that the order_by can use it to make the order according to the 
            # doc_id_list
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(doc_id_list)])
            return cls.objects.filter(id__in=doc_id_list).order_by(preserved)
        
        # get the score, then the doc_id_list, then the doc_list, and lastly the time used of the
        # search process
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
