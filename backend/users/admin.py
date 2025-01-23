from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import UserModel

@admin.register(UserModel)
class UserModelAdmin(UserAdmin):
    list_display = ('username', 'id', 'email', 'first_name', 'last_name',
                    'is_staff')
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    ordering = ('username',)
