from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import User, Profile
from django.utils.html import format_html

@admin.register(User)
class CustomAdminClass(ModelAdmin):
    list_display = ('id', 'email', 'name', 'preview_user_image', 'check_is_superuser')
    list_display_links = ('id', 'email', 'name', 'preview_user_image', 'check_is_superuser')
    search_fields = ('email', 'name')


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(id=1)


    def name(self, obj):
        return obj.profile.name if hasattr(obj, 'profile') else ''


    def preview_user_image(self, obj):
        if obj.profile.avatar:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.profile.avatar.url)
        return "No Image"
    
    def check_is_superuser(self, obj):
        return 'YES' if obj.is_superuser else 'NO'
    
@admin.register(Profile)
class UserProfileAdmin(ModelAdmin):
    list_display = ('id', 'user', 'name', 'avatar', 'dob')
    list_display_links = ('id', 'user', 'name')
    search_fields = ('user__email', 'name')