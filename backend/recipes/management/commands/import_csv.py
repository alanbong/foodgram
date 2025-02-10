import csv
import os

from foodgram_backend.settings import BASE_DIR
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


def ingredient_create(row):
    Ingredient.objects.get_or_create(
        name=row[0],
        measurement_unit=row[1],
    )


action = {
    'ingredients.csv': ingredient_create,
}


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='?',
                            default='ingredients.csv', type=str)

    def handle(self, *args, **options):
        filename = options['filename']
        path = os.path.join(BASE_DIR.parent, 'data', filename)
        with open(path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                action[filename](row)

        # Создание тегов после загрузки CSV для тестов
        from recipes.models import Tag
        tags = ['test_tag1', 'test_tag2', 'test_tag3']
        for tag_name in tags:
            Tag.objects.get_or_create(name=tag_name, slug=tag_name.lower())

        self.stdout.write(self.style.SUCCESS(
            f"Файл {filename} успешно загружен!"
        ))
