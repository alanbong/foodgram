from django.contrib import admin

from .models import (Recipe, Tag, Ingredient,
                     RecipeIngredient, Favorite, ShoppingCart)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count')
    list_filter = ('tags', 'author', 'pub_date')
    search_fields = ('name', 'author__username')
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('pub_date', 'favorites_count')

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj.favorite.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
