from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import Subscription, UserModel


admin.site.unregister(Group)


@admin.register(UserModel)
class UserModelAdmin(UserAdmin):
    list_display = ('id', 'username', 'first_name',
                    'last_name', 'email',
                    'is_admin_display', 'subscribers_count')
    list_filter = ('username', 'email')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-is_superuser', '-is_staff', 'username')

    @admin.display(description='Подписчиков у автора')
    def subscribers_count(self, obj):
        return obj.subscribers.count()

    @admin.display(description="Админ")
    def is_admin_display(self, obj):
        return obj.is_admin


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user__username', 'author__username')
    ordering = ('user__username', 'author__username')
