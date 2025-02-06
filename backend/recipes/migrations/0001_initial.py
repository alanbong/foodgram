# Generated by Django 3.2.16 on 2025-01-20 14:52

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Введите название ингредиента', max_length=128, unique=True, verbose_name='Название ингредиента')),
                ('measurement_unit', models.CharField(help_text='Единица измерения', max_length=64, verbose_name='Единица измерения')),
            ],
            options={
                'verbose_name': 'Ингредиент',
                'verbose_name_plural': 'Ингредиенты',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Название рецепта', max_length=256, verbose_name='Название рецепта')),
                ('image', models.ImageField(upload_to='media/recipe/', verbose_name='Картинка рецепта')),
                ('text', models.TextField(help_text='Описание рецепта', verbose_name='Описание рецепта')),
                ('cooking_time', models.PositiveSmallIntegerField(help_text='Время приготовления рецепта в минутах', validators=[django.core.validators.MinValueValidator(1, 'Минимальное время готовки - 1 мин')], verbose_name='Время приготовления')),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')),
                ('author', models.ForeignKey(help_text='Автор рецепта', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Автор рецепта')),
            ],
            options={
                'verbose_name': 'Рецепт',
                'verbose_name_plural': 'Рецепты',
                'ordering': ['-pub_date'],
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, unique=True, verbose_name='Название тега')),
                ('slug', models.SlugField(max_length=32, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_slug', message='Slug может содержать только                     буквы, цифры, дефисы и подчёркивания.', regex='^[a-zA-Z0-9_-]+$')], verbose_name='Идентификатор')),
            ],
            options={
                'verbose_name': 'Тег',
                'verbose_name_plural': 'Теги',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='RecipeIngredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1, 'Минимальное количество ингридиентов - 1 шт')])),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.ingredient', verbose_name='Ингридиент')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.recipe', verbose_name='Название рецепта')),
            ],
            options={
                'verbose_name': 'Ингридиент в рецепте',
                'verbose_name_plural': 'Ингридиенты в рецепте',
                'ordering': ['id'],
            },
        ),
        migrations.AddField(
            model_name='recipe',
            name='ingredients',
            field=models.ManyToManyField(through='recipes.RecipeIngredient', to='recipes.Ingredient', verbose_name='Ингредиент'),
        ),
        migrations.AddField(
            model_name='recipe',
            name='tags',
            field=models.ManyToManyField(to='recipes.Tag', verbose_name='Тег'),
        ),
        migrations.AddConstraint(
            model_name='recipeingredient',
            constraint=models.UniqueConstraint(fields=('recipe', 'ingredient'), name='unique_recipe_ingredient'),
        ),
        migrations.AddConstraint(
            model_name='recipe',
            constraint=models.UniqueConstraint(fields=('name', 'author'), name='unique_name_author'),
        ),
    ]
