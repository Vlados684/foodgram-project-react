from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        'Название ингредиента',
        max_length=200)
    measurement = models.CharField(
        'Единица измерения ингредиента',
        max_length=200)

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement}.'


class Tag(models.Model):
    name = models.CharField(
        'Название тега',
        max_length=200,
        unique=True)
    color = models.CharField(
        'Цвет',
        max_length=7,
        unique=True)
    slug = models.SlugField(
        'Ссылка',
        max_length=200,
        unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        'Название',
        max_length=255)
    image = models.ImageField(
        'Изображение рецепта',
        upload_to='recipes/',
        blank=True,
        null=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Автор')
    text = models.TextField(
        'Описание')
    cooking_time = models.IntegerField(
        'Время приготовления',
        validators=[MinValueValidator(1)]
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredients')
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes')
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', )

    def __str__(self):
        return f'{self.author.email}, {self.name}'


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Рецепт')
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='Ингредиент')
    amount = models.IntegerField(
        'Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'Количество ингредиента в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient')]


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор')
    created = models.DateTimeField(
        'Дата подписки',
        auto_now_add=True)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription')]

    def __str__(self):
        return f'Пользователь {self.user} -> автор {self.author}'


class Favorite(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='favorite_user',
        verbose_name='Пользователь добавил в избранное')
    recipe = models.ManyToManyField(
        Recipe,
        related_name='favorite_recipe',
        verbose_name='Избранный рецепт')

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        list_ = [item['name'] for item in self.recipe.values('name')]
        return f'Пользователь {self.user} добавил {list_} в избранные.'

    @receiver(post_save, sender=User)
    def create_favorite_recipe(
            self, instance, created, **kwargs):
        if created:
            return Favorite.objects.create(user=instance)


class ShoppingCart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        null=True,
        verbose_name='Добавил в корзину')
    recipe = models.ManyToManyField(
        Recipe,
        related_name='shopping_cart',
        verbose_name='Рецепт в корзине')

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        ordering = ['-id']

    def __str__(self):
        list_ = [item['name'] for item in self.recipe.values('name')]
        return f'Пользователь {self.user} добавил {list_} в покупки.'

    @receiver(post_save, sender=User)
    def create_shopping_cart(
            self, instance, created, **kwargs):
        if created:
            return ShoppingCart.objects.create(user=instance)
