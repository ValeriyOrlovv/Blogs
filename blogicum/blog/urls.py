from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='index'),
    path(
        'posts/<int:post_id>/',
        views.PostDetail.as_view(),
        name='post_detail'),
    path(
        'posts/<int:post_id>/edit/',
        views.PostUpdateView.as_view(),
        name='edit_post'),
    path(
        'posts/<int:post_id>/delete/',
        views.PostDeleteView.as_view(),
        name='delete_post'),
    path(
        'posts/create/',
        views.post_create,
        name='create_post'),
    path(
        'posts/<int:post_id>/comment/',
        views.CommentCreateView.as_view(),
        name='add_comment'),
    path(
        'posts/<int:post_id>/edit_comment/<int:comment_id>/',
        views.CommentUpdateView.as_view(),
        name='edit_comment'),
    path(
        'posts/<int:post_id>/delete_comment/<int:comment_id>/',
        views.CommentDeleteView.as_view(),
        name='delete_comment'),
    path(
        'category/<slug:category_slug>/',
        views.CategoryList.as_view(),
        name='category_posts'
    ),
    path(
        'profile/edit_profile/',
        views.ProfileUpdateView.as_view(),
        name='edit_profile'),
    path(
        'profile/<str:username>/',
        views.ProfileView.as_view(),
        name='profile'),
]
