from django.db.models import Count
from django.shortcuts import redirect
from django.utils import timezone
from django.urls import reverse

from blog.constants import POSTS_ON_PAGE
from blog.models import Comment, Post


class PostsMixin:

    model = Post
    paginate_by = POSTS_ON_PAGE

    def get_queryset(self):
        return Post.objects.select_related('category').filter(
            is_published=True,
            category__is_published=True,
            pub_date__date__lte=timezone.now()
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')


class CommentAuthorMixin:

    def dispatch(self, request, *args, **kwargs):
        comment = super().get_object()
        if comment.author != self.request.user:
            return redirect(
                'blog:post_detail',
                post_id=comment.post_id
            )
        return super().dispatch(request, *args, **kwargs)


class CommentsMixin:

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.object.pk]
        )
