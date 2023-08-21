from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredients,
                            ShoppingCart, Tag)
from rest_framework import serializers
from users.models import Subscribe, User
from django.db import transaction


from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError


class CustomUserReadSerializer(serializers.ModelSerializer):
    """Список пользователей с дополнительными данными."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        if self.context.get('request') and not self.context['request'].user.is_anonymous:
            return Subscribe.objects.filter(user=self.context['request'].user, author=obj).exists()
        return False


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """Создание нового пользователя с дополнительными проверками."""
    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'password')
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
        }

    def validate(self, attrs):
        invalid_usernames = ['me', 'set_password', 'subscriptions', 'subscribe']
        if attrs.get('username') in invalid_usernames:
            raise serializers.ValidationError({'username': 'Вы не можете использовать это имя.'})
        return attrs


class SetPasswordSerializer(serializers.Serializer):
    """Изменение пароля с дополнительными проверками."""
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, attrs):
        try:
            password_validation.validate_password(attrs['new_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})
        return super().validate(attrs)

    def update(self, instance, validated_data):
        if not instance.check_password(validated_data['current_password']):
            raise serializers.ValidationError({'current_password': 'Неправильный пароль.'})
        if validated_data['current_password'] == validated_data['new_password']:
            raise serializers.ValidationError({'new_password': 'Новый пароль должен отличаться.'})
        instance.set_password(validated_data['new_password'])
        instance.save()
        return validated_data


class CustomRecipeSerializer(serializers.ModelSerializer):
    """Список рецептов."""
    image = serializers.ImageField(read_only=True)
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionsSerializer(serializers.ModelSerializer):
    """Список подписок на пользователей."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        return self.context.get('request').user.is_authenticated and Subscribe.objects.filter(user=self.context['request'].user, author=obj).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = CustomRecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


class SubscribeAuthorSerializer(serializers.ModelSerializer):
    """Подписка и отписка на авторов."""
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = CustomRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def validate(self, attrs):
        if self.context['request'].user == attrs:
            raise serializers.ValidationError({'errors': 'Ошибка подписки.'})
        return attrs

    def get_is_subscribed(self, obj):
        return self.context.get('request').user.is_authenticated and Subscribe.objects.filter(user=self.context['request'].user, author=obj).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class IngredientSerializer(serializers.ModelSerializer):
    """Список ингредиентов."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Список тегов."""
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Список ингредиентов для рецепта."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Список рецептов с дополнительными данными."""
    author = CustomUserReadSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(many=True, read_only=True, source='recipes')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited', 'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        return self.context.get('request').user.is_authenticated and Favorite.objects.filter(user=self.context['request'].user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        return self.context.get('request').user.is_authenticated and ShoppingCart.objects.filter(user=self.context['request'].user, recipe=obj).exists()


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Количество ингредиентов для создания рецепта."""
    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Создание, изменение и удаление рецепта."""
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    author = CustomUserReadSerializer(read_only=True)
    id = serializers.ReadOnlyField()
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time', 'author')
        extra_kwargs = {
            'ingredients': {'required': True, 'allow_blank': False},
            'tags': {'required': True, 'allow_blank': False},
            'name': {'required': True, 'allow_blank': False},
            'text': {'required': True, 'allow_blank': False},
            'image': {'required': True, 'allow_blank': False},
            'cooking_time': {'required': True},
        }

    def validate(self, attrs):
        for field in ['name', 'text', 'cooking_time']:
            if not attrs.get(field):
                raise serializers.ValidationError(f'{field} - Обязательное поле.')
        if not attrs.get('tags'):
            raise serializers.ValidationError('Нужно указать минимум 1 тег.')
        if not attrs.get('ingredients'):
            raise serializers.ValidationError('Нужно указать минимум 1 ингредиент.')
        ingredient_id_list = [item['id'] for item in attrs.get('ingredients')]
        unique_ingredient_id_list = set(ingredient_id_list)
        if len(ingredient_id_list) != len(unique_ingredient_id_list):
            raise serializers.ValidationError('Ингредиенты должны быть уникальны.')
        return attrs

    @transaction.atomic
    def tags_and_ingredients_set(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        RecipeIngredients.objects.bulk_create([
            RecipeIngredients(
                recipe=recipe,
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=self.context['request'].user, **validated_data)
        self.tags_and_ingredients_set(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        RecipeIngredients.objects.filter(recipe=instance, ingredient__in=instance.ingredients.all()).delete()
        self.tags_and_ingredients_set(instance, tags, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data
