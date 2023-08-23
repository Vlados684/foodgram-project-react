from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe,
                     ShoppingCart, Subscribe, Tag)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'in_favorites')
    list_editable = ('name',)
    readonly_fields = ('in_favorites',)
    list_filter = ('author', 'tags')
    search_fields = ('name', 'author__username')
    empty_value_display = '-пусто-'

    @admin.display(description='В избранном')
    def in_favorites(self, obj):
        return obj.favorite_recipe.count()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name', 'slug')
    empty_value_display = '-пусто-'


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author', 'created')
    search_fields = ('user__email', 'author__email')
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name', )


@admin.register(Favorite)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_count')
    empty_value_display = '-пусто-'

    @admin.display(description='Количество рецептов')
    def get_count(self, obj):
        return obj.recipe.count()


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_count')
    empty_value_display = '-пусто-'

    @admin.display(description='Количество рецептов')
    def get_count(self, obj):
        return obj.recipe.count()
