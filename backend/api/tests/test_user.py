from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from PIL import Image
from io import BytesIO

User = get_user_model()


class UserAPITests(APITestCase):
    """Тесты для эндпоинтов, связанных с пользователями."""
    def setUp(self):
        """Создаем тестового пользователя."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )

    def test_get_users_list(self):
        """Тест получения списка пользователей."""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_register_user(self):
        """Тест регистрации нового пользователя."""
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post('/api/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(response.data['email'], data['email'])

    def test_get_user_profile(self):
        """Тест получения профиля пользователя."""
        response = self.client.get(f'/api/users/{self.user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)

    def test_get_nonexistent_user_profile(self):
        """Тест получения несуществующего пользователя."""
        response = self.client.get('/api/users/999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_current_user(self):
        """Тест получения данных текущего пользователя."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)

    def test_get_current_user_unauthorized(self):
        """Тест получения данных текущего пользователя без авторизации."""
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_set_password(self):
        """Тест изменения пароля."""
        self.client.force_authenticate(user=self.user)
        data = {
            'current_password': 'testpassword123',
            'new_password': 'newpassword123'
        }
        response = self.client.post(
            '/api/users/set_password/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_set_password_invalid_current_password(self):
        """Тест изменения пароля с неверным текущим паролем."""
        self.client.force_authenticate(user=self.user)
        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123'
        }
        response = self.client.post(
            '/api/users/set_password/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_avatar(self):
        """Тест удаления аватара."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete('/api/users/me/avatar/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_set_avatar(self):
        """Тест добавления аватара."""
        self.client.force_authenticate(user=self.user)

        # Создаем временное изображение
        image = Image.new('RGB', (100, 100), color='red')
        file = BytesIO()
        image.save(file, 'PNG')
        file.name = 'test_image.png'
        file.seek(0)

        # Отправляем запрос с изображением
        response = self.client.put('/api/users/me/avatar/', {'avatar': file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('avatar', response.data)


class AdminAPITests(APITestCase):
    """Тесты для функциональности администратора."""

    def setUp(self):
        """
        Создаем тестового пользователя и администратора.
        """
        # Обычный пользователь
        self.user = User.objects.create_user(
            email='user@example.com',
            username='testuser',
            password='userpassword123',
            first_name='Test',
            last_name='User',
            role='user'
        )

        # Администратор
        self.admin = User.objects.create_user(
            email='admin@example.com',
            username='adminuser',
            password='adminpassword123',
            first_name='Admin',
            last_name='User',
            role='admin'
        )

    def test_admin_change_user_password(self):
        """Тест изменения пароля пользователя администратором."""
        self.client.force_authenticate(user=self.admin)

        data = {
            'user_id': self.user.id,
            'new_password': 'newsecurepassword'
        }

        response = self.client.put('/api/users/set_password/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(data['new_password']))

    def test_admin_can_delete_user(self):
        """Тест, что администратор может удалить пользователя."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f'/api/users/{self.user.pk}/admin-delete/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    def test_admin_cannot_delete_self(self):
        """Тест, что администратор не может удалить сам себя."""
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            f'/api/users/{self.admin.pk}/admin-delete/'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_cannot_delete_superuser(self):
        """Тест, что администратор не может удалить суперпользователя."""
        superuser = User.objects.create_superuser(
            email='super@example.com',
            username='superadmin',
            password='superpassword123'
        )

        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            f'/api/users/{superuser.pk}/admin-delete/'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_admin_cannot_delete_user(self):
        """Тест, что неадминистратор не может удалить пользователя."""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            f'/api/users/{self.admin.pk}/admin-delete/'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
