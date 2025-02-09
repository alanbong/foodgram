from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from recipes.models import Ingredient


class IngredientAPITests(APITestCase):
    """Тесты для эндпоинтов ингредиентов."""

    def setUp(self):
        """
        Создаем тестовые данные для ингредиентов.
        """
        self.ingredient1 = Ingredient.objects.create(
            name='Капуста', measurement_unit='кг'
        )
        self.ingredient2 = Ingredient.objects.create(
            name='Картошка', measurement_unit='шт'
        )
        self.ingredient3 = Ingredient.objects.create(
            name='Карамель', measurement_unit='г'
        )
        self.ingredient4 = Ingredient.objects.create(
            name='Макароны', measurement_unit='г'
        )
        self.ingredient5 = Ingredient.objects.create(
            name='Морковь', measurement_unit='шт'
        )

    def test_filter_ingredients_starts_with(self):
        """Тест фильтрации ингредиентов по началу имени."""
        url = reverse('ingredients-list')
        response = self.client.get(url, {'name': 'кар'})

        actual_names = [item["name"] for item in response.data]

        expected_starts_with = ["Карамель", "Картошка"]
        expected_contains = ["Макароны"]

        self.assertTrue(
            all(name in actual_names for name in expected_starts_with),
            "Ожидалось, что в списке будут ингредиенты, начинающиеся с 'кар'"
        )
        self.assertTrue(
            all(name in actual_names for name in expected_contains),
            "Ожидалось, что в списке будут ингредиенты, содержащие 'кар'"
        )
        self.assertEqual(actual_names, sorted(actual_names))

    def test_empty_search(self):
        """Тест на пустой запрос (должны вернуться все записи)."""
        url = reverse('ingredients-list')
        response = self.client.get(url, {'name': ''})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_no_results(self):
        """Тест на случай, когда ничего не найдено."""
        url = reverse('ingredients-list')
        response = self.client.get(url, {'name': 'вааываыфва'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_ingredients(self):
        """Тест получения списка ингредиентов."""
        url = reverse('ingredients-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_retrieve_ingredient(self):
        """Тест получения информации о конкретном ингредиенте."""
        url = reverse('ingredients-detail', args=[self.ingredient1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Капуста')
        self.assertEqual(response.data['measurement_unit'], 'кг')
