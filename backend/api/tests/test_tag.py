from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from recipes.models import Tag


class TagAPITests(APITestCase):
    """Тесты для эндпоинтов тегов."""

    def setUp(self):
        """
        Создаем тестовые данные для тегов.
        """
        self.tag1 = Tag.objects.create(
            name='Завтрак',
            slug='breakfast'
        )
        self.tag2 = Tag.objects.create(
            name='Обед',
            slug='lunch'
        )

    def test_list_tags(self):
        """Тест получения списка тегов."""
        url = reverse('tags-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Завтрак')
        self.assertEqual(response.data[1]['name'], 'Обед')

    def test_retrieve_tag(self):
        """Тест получения информации о конкретном теге."""
        url = reverse('tags-detail', args=[self.tag1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Завтрак')
        self.assertEqual(response.data['slug'], 'breakfast')
