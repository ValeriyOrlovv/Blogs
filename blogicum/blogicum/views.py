from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView


from blog.models import User


class RegistrationVIew(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/registration_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        user = User.objects.get(username=username)
        login(self.request, user)
        return response

    def get_success_url(self):
        username = self.request.POST.get('username')
        if not username:
            raise Http404
        return reverse_lazy('blog:profile', kwargs={'username': username})
