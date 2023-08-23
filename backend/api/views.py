from django.contrib.auth import get_user_model
from django.db.models.aggregates import Sum
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from djoser.views import UserViewSet
from rest_framework import status, viewsets, filters, permissions, decorators
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.filters import RecipeFilters
from foodgram.settings import FILE_NAME
from api.permissions import IsAuthorOrAdminOrReadOnly
from recipes.models import (Favorite, Ingredient, Recipe, ShoppingCart,
                            Subscribe, Tag, RecipeIngredients)
from users.models import Subscriber

from api.serializers import (IngredientSerializer, RecipeReadSerializer,
                             SubscribeAuthorSerializer,
                             CustomUserCreateSerializer,
                             SubscriptionsSerializer, TagSerializer,
                             RecipeCreateSerializer)
from api.pagination import LimitPageNumberPagination

User = get_user_model()


class MainUserViewSet(UserViewSet):
    """Кастомная модель пользователя."""
    queryset = User.objects.all()
    serializer_class = CustomUserCreateSerializer
    pagination_class = LimitPageNumberPagination

    @decorators.action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribing__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(page, many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    @decorators.action(
        detail=False,
        methods=['GET'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = SubscribeAuthorSerializer(
                author, data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            Subscribe.objects.create(user=request.user, author=author)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(Subscriber, user=request.user,
                              author=author).delete()
            return Response({'detail': 'Вы отписались!'},
                            status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Отображение тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Отображение ингредиентов."""

    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (filters.SearchFilter, )
    search_fields = ('^name', )


class RecipeViewSet(viewsets.ModelViewSet):
    """Отображение рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    serializer_class = RecipeReadSerializer
    filter_class = RecipeFilters
    pagination_class = LimitPageNumberPagination

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return RecipeCreateSerializer
        return RecipeReadSerializer

    @decorators.action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = RecipeReadSerializer(recipe, data=request.data,
                                              context={"request": request})
            serializer.is_valid(raise_exception=True)
            if not Favorite.objects.filter(user=request.user,
                                           recipe=recipe).exists():
                Favorite.objects.create(user=request.user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Рецепт уже добавлен в избранном!'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            get_object_or_404(Favorite, user=request.user,
                              recipe=recipe).delete()
            return Response({'detail': 'Рецепт удален из избранного!'},
                            status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        """Добавляем или удаляем рецепт из корзины"""
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            serializer = RecipeReadSerializer(recipe, data=request.data,
                                              context={"request": request})
            serializer.is_valid(raise_exception=True)
            if not ShoppingCart.objects.filter(user=request.user,
                                               recipe=recipe).exists():
                ShoppingCart.objects.create(user=request.user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Рецепт уже в списке покупок!'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            get_object_or_404(ShoppingCart, user=request.user,
                              recipe=recipe).delete()
            return Response(
                {'detail': 'Рецепт удален из списка покупок!'},
                status=status.HTTP_204_NO_CONTENT
            )

    @decorators.action(
        detail=False,
        methods=['GET'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        ingredients = RecipeIngredients.objects.filter(
            recipe__shopping_cart__user=self.request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement'
        ).order_by('ingredient__name').annotate(amount=Sum('amount'))
        shop_list = []
        [shop_list.append(
            '{} - {} {}.'.format(
                ingredient['ingredient__name'],
                ingredient['amount'],
                ingredient['ingredient__measurement']
            )
        ) for ingredient in ingredients]
        file_content = 'Список покупок:\n' + '\n'.join(shop_list)
        file = HttpResponse(file_content, content_type='text/plain')
        file['Content-Disposition'] = f'attachment; filename={FILE_NAME}'
        return file
