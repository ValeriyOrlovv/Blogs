from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.views.generic.edit import FormMixin

from blog.constants import POSTS_ON_PAGE
from blog.forms import CommentForm, PostForm, UserProfileForm
from blog.models import Category, Comment, Post, User


class PostsMixin:

    model = Post
    paginate_by = POSTS_ON_PAGE

    def get_queryset(self):
        return Post.objects.filter(
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


class PostListView(PostsMixin, ListView):
    """Отображение списка публикаций на главной странице."""

    template_name = 'blog/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PostDetail(DetailView, FormMixin):
    """Отображение отдельной публикации."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'
    form_class = CommentForm

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, pk=self.kwargs.get(self.pk_url_kwarg))
        if self.request.user != post.author:
            post = get_object_or_404(
                Post, pk=self.kwargs.get(self.pk_url_kwarg),
                pub_date__lte=timezone.now(),
                is_published=True
            )
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = self.get_object()
        comments = (
            posts.comments.select_related('author').order_by('created_at')
        )
        context['comments'] = comments
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.object.post_id]
        )


class CommentUpdateView(LoginRequiredMixin, CommentAuthorMixin, UpdateView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    form_class = CommentForm

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.object.pk]
        )


class CommentDeleteView(LoginRequiredMixin, CommentAuthorMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.object.pk]
        )


class CategoryList(PostsMixin, ListView):

    template_name = 'blog/category.html'

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        return (
            super()
            .get_queryset()
            .filter(category__slug=category_slug)
            .select_related('category')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get('category_slug')
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True)
        context['category'] = category
        return context


class ProfileView(PostsMixin, ListView):

    template_name = 'blog/profile.html'

    def get_queryset(self):
        username = self.kwargs.get('username')
        if self.request.user.username != username:
            return super().get_queryset().filter(author__username=username)
        return Post.objects.filter(author__username=username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.kwargs['username']
        profile = get_object_or_404(User, username=username)
        context['profile'] = profile
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    form_class = UserProfileForm

    def get_object(self, queryset=None):
        user = self.request.user
        return user

    def get_success_url(self):
        username = self.request.POST.get('username')
        return reverse('blog:profile', args=[username])


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    context = {'form': form}
    if form.is_valid():
        instance = form.save(commit=False)
        instance.author = request.user
        instance.created_at = timezone.now()
        instance.save()
        username = request.user.username
        return redirect('blog:profile', username=username)
    return render(request, 'blog/create.html', context)


class PostUpdateView(UpdateView):
    """Редактирование существующей публикации."""

    # Не очень понятно, зачем использовать LoginRequiredMixin:
    # судя по тесту, неавторизованный пользователь должен при отправке формы
    # перенаправляться на страницу публикации. Если использовать миксин, то
    # пользователь не получит доступ на страницу публикации, и из-за этого
    # тест будет падать.

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    form_class = PostForm

    def form_valid(self, form):
        if (
            self.request.user.is_authenticated
            and form.instance.author == self.request.user
        ):
            return super().form_valid(form)
        else:
            return redirect(reverse(
                'blog:post_detail',
                kwargs={'post_id': self.kwargs.get('post_id')}
            ))

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.object.pk])


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление существующей публикации"""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author == self.request.user:
            return super().delete(request, *args, **kwargs)
        else:
            raise Http404

    def get_success_url(self):
        return reverse('blog:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        form = PostForm(instance=post)
        context['form'] = form
        return context
