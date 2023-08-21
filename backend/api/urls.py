from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    MainUserViewSet, RecipeViewSet,
    TagViewSet, IngredientViewSet
)

app_name = 'api'

router = DefaultRouter()

router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'users', MainUserViewSet, basename='users')
router.register(
    r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
    path(r'auth/', include('djoser.urls.authtoken')),
]
