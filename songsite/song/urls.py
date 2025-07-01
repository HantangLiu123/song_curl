from django.urls import path
import song.views as views

urlpatterns = [
    path('songs/', views.SongList.as_view(), name='song_list'),
    path('songs/<int:pk>/', views.SongDetail.as_view(), name='song_detail'),
    path('songs/<int:song_id>/comment/', views.comment, name='song_comment'),
    path('artists/', views.ArtistList.as_view(), name='artist_list'),
    path('artists/<int:pk>/', views.ArtistDetail.as_view(), name='artist_detail'),
]