import os
import csv

from foodgram import settings
from django.core.management import BaseCommand
from recipes.models import Ingredient

from progress.bar import IncrementalBar


class Command(BaseCommand):
    help = "Загрузка ингредиентов из data/ingredients.csv"

    def create_ingredients(self, row):
        name, measurement = row
        Ingredient.objects.get_or_create(name=name,
                                         measurement=measurement)

    def load_ingredients(self, *args, **options):
        path = os.path.join(settings.BASE_DIR, 'ingredients.csv')
        row_count = 0
        with open(path, 'r', encoding='utf-8') as file:
            for _ in file:
                row_count += 1
        with open(path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            bar = IncrementalBar('Загрузка...'.ljust(30), max=row_count)
            next(reader)
            for row in reader:
                self.create_ingredients(row)
                bar.next()
            bar.finish()
        self.stdout.write(
            self.style.SUCCESS("Все ингредиенты успешно загружены!")
        )
