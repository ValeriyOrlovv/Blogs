from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.views.generic.edit import FormMixin
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from blog.forms import CommentForm, PostForm, UserProfileForm
from blog.models import Post, Category, User, Comment


class PostListView(ListView):
    """Отображение списка публикаций на главной странице"""

    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(
            is_published=True,
            category__is_published=True,
            pub_date__date__lte=timezone.now())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = context['post_list']
        for post in posts:
            post.comment_count = Comment.objects.filter(post=post).count()
        return context


class PostDetail(DetailView, FormMixin):
    """Отображение отдельной публикации"""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'
    form_class = CommentForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.is_published is False:
            if self.object.author == self.request.user:
                return super().get(request, *args, **kwargs)
            else:
                raise Http404
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post_id = self.kwargs.get('post_id')
        comments = Comment.objects.filter(post_id=post_id)
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
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.pk})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    fields = ('text',)

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=self.kwargs['comment_id'])
        if comment.author != self.request.user:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        comment = self.get_object()
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': comment.post_id})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=self.kwargs['comment_id'])
        if comment.author != self.request.user:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        comment = self.get_object()
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': comment.post_id})


class CategoryList(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        return Post.objects.filter(
            is_published=True,
            pub_date__date__lt=timezone.now(),
            category__slug=category_slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get('category_slug')
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True)
        context['category'] = category
        return context


class ProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    slug_url_kwarg = 'username'
    slug_field = 'username'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        slug = self.kwargs.get(self.slug_url_kwarg)
        if slug:
            queryset = queryset.filter(**{self.slug_field: slug})
        else:
            queryset = queryset.filter(username=self.kwargs.get('username'))
        return get_object_or_404(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = context.get(self.context_object_name)
        if not user_profile:
            username = self.kwargs.get('username')
            user_profile = get_object_or_404(User, username=username)
        posts = Post.objects.filter(author=user_profile).annotate(
            comment_count=Count('comments')).order_by('-pub_date')
        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        context['posts'] = page_obj.object_list
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    form_class = UserProfileForm

    def get_object(self, queryset=None):
        username = self.request.user.username
        return get_object_or_404(User, username=username)

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        if not username:
            raise Http404
        return super().form_valid(form)

    def get_success_url(self):
        username = self.request.POST.get('username')
        if not username:
            raise Http404('User does not exist')
        return reverse_lazy('blog:profile', kwargs={'username': username})


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None)
    context = {'form': form}
    if form.is_valid():
        instance = form.save(commit=False)
        instance.author = request.user
        instance.created_at = timezone.now()
        instance.save()
        username = request.user.username
        return redirect(reverse(
            'blog:profile',
            kwargs={'username': username}))
    return render(request, 'blog/create.html', context)


class PostUpdateView(UpdateView):
    """Редактирование существующей публикации"""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    form_class = PostForm

    def form_valid(self, form):
        if self.request.user.is_authenticated and form.instance.author == self.request.user:
            return super().form_valid(form)
        else:
            return redirect(reverse(
                'blog:post_detail',
                kwargs={'post_id': self.kwargs.get('post_id')}
            ))

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление существующей публикации"""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author == self.request.user or self.request.user.is_staff:
            return super().delete(request, *args, **kwargs)
        else:
            raise Http404

    def get_success_url(self):
        return reverse_lazy('blog:index')
