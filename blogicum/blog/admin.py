from django.contrib import admin

from .models import Category, Comment, Location, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    list_filter = ('category', 'author', 'location',)
    list_display = ('text', 'category', 'author', 'location')


admin.site.register(Location)
admin.site.register(Category)
admin.site.register(Comment)
