import csv
import os

from django.core.management.base import BaseCommand
from foodgram_backend.settings import BASE_DIR
from recipes.models import Ingredient, Tag


def ingredient_create(row):
    Ingredient.objects.get_or_create(
        name=row[0],
        measurement_unit=row[1],
    )


def tag_create(row):
    """Создаёт тег из строки CSV."""
    Tag.objects.get_or_create(
        name=row[0],
        slug=row[1],
    )


action = {
    'ingredients.csv': ingredient_create,
    'tags.csv': tag_create,
}


class Command(BaseCommand):
    help = 'Загружает данные из CSV-файлов (ингредиенты и теги).'

    def handle(self, *args, **options):
        """Загружает все CSV файлы"""
        data_dir = os.path.join(BASE_DIR, 'data')
        for filename, process_function in action.items():
            file_path = os.path.join(data_dir, filename)

            if not os.path.exists(file_path):
                self.stdout.write(self.style.WARNING(
                    f"Файл {filename} не найден, пропускаем."
                ))
                continue

            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    process_function(row)

            self.stdout.write(self.style.SUCCESS(
                f"Файл {filename} успешно загружен!"
            ))
