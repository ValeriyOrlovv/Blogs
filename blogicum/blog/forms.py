from django.forms import ModelForm


from blog.models import Comment, Post, User


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)


class PostForm(ModelForm):
    class Meta:
        model = Post
        exclude = ('created_at', 'author',)


class UserProfileForm(ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',)
