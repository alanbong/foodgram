from urllib.parse import urlparse

from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from recipes.models import Recipe, Ingredient, Tag

User = get_user_model()


BASE_RECIPE_DATA = {
    'name': 'New Recipe',
    'text': 'Описание рецепта',
    'cooking_time': 15,
    'ingredients': [
        {'id': None, 'amount': 100},
        {'id': None, 'amount': 200}
    ],
    'tags': [],
    'image': (
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAA'
        'BAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7'
        'EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg=='
    )
}


class RecipeAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass'
        )
        self.client.force_authenticate(user=self.user)
        self.recipe = Recipe.objects.create(
            name='Test Recipe',
            author=self.user,
            cooking_time=10)

        # Создание тестовых ингредиентов
        self.ingredient1 = Ingredient.objects.create(
            name='Ингредиент 1', measurement_unit='г'
        )
        self.ingredient2 = Ingredient.objects.create(
            name='Ингредиент 2', measurement_unit='мл'
        )

        # Создание тестовых тегов
        self.tag1 = Tag.objects.create(name='Завтрак', slug='tag1')
        self.tag2 = Tag.objects.create(name='Острое', slug='tag2')

        self.recipe_list_url = '/api/recipes/'
        self.recipe_detail_url = f'/api/recipes/{self.recipe.pk}/'
        self.recipe_get_link_url = f'/api/recipes/{self.recipe.pk}/get-link/'

    def test_get_recipe_short_link(self):
        """Тест получения короткой ссылки."""
        response = self.client.get(self.recipe_get_link_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('short-link', response.data)

        # Проверяем формат короткой ссылки
        short_link = response.data['short-link']
        self.assertTrue(short_link.startswith('http'))

    def test_redirect_short_link(self):
        """Тест переадресации по короткой ссылке."""
        # Получаем короткую ссылку
        response = self.client.get(self.recipe_get_link_url)
        parsed_url = urlparse(response.data['short-link'])
        short_path = parsed_url.path.split('/')[-1]
        # Переходим по короткой ссылке
        redirect_url = reverse(
            'redirect-short-link', kwargs={'short_link': short_path})
        response = self.client.get(redirect_url)
        self.assertRedirects(
            response, f'/recipes/{self.recipe.id}',
            fetch_redirect_response=False)

    def test_get_recipe_list(self):
        response = self.client.get(self.recipe_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_recipe_detail(self):
        response = self.client.get(self.recipe_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.recipe.name)

    def test_create_recipe(self):
        """Тест создания нового рецепта."""
        data = BASE_RECIPE_DATA.copy()
        data['ingredients'][0]['id'] = self.ingredient1.pk
        data['ingredients'][1]['id'] = self.ingredient2.pk
        data['tags'] = [self.tag1.pk, self.tag2.pk]

        response = self.client.post(self.recipe_list_url, data, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data['name'], 'New Recipe')

    def test_create_recipe_without_ingredients(self):
        """Тест создания рецепта без ингредиентов."""
        data = BASE_RECIPE_DATA.copy()
        data['ingredients'] = []  # Удаляем ингредиенты
        data['tags'] = [self.tag1.pk, self.tag2.pk]

        response = self.client.post(self.recipe_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ingredients', response.data)
        self.assertEqual(
            response.data['ingredients'][0],
            'Добавьте хотя бы один ингредиент!'
        )

    def test_create_recipe_with_duplicate_ingredients(self):
        """Тест создания рецепта с повторяющимися ингредиентами."""
        data = BASE_RECIPE_DATA.copy()
        data['ingredients'][0]['id'] = self.ingredient1.pk
        data['ingredients'][1]['id'] = self.ingredient1.pk
        data['tags'] = [self.tag1.pk, self.tag2.pk]

        response = self.client.post(self.recipe_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ingredients', response.data)
        self.assertEqual(
            response.data['ingredients'][0],
            'Ингредиенты не должны повторяться.'
        )

    def test_update_recipe(self):
        data = {'name': 'Updated Recipe'}
        response = self.client.patch(
            self.recipe_detail_url, data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Recipe')

    def test_delete_recipe(self):
        response = self.client.delete(self.recipe_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=self.recipe.id).exists())
