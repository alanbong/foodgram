`Python` `Django` `Django Rest Framework` `Docker` `Gunicorn` `NGINX` `PostgreSQL`

# Foodgram

Foodgram

## Описание

Foodgram — это продуктовый помощник, который позволяет пользователям делиться рецептами, подписываться на других авторов, добавлять рецепты в избранное, формировать список покупок и загружать его в удобном формате.

Проект предоставляет API-интерфейс для удобного взаимодействия с приложением и интеграции с другими сервисами.

### Основные возможности

- Создание, просмотр, редактирование и удаление рецептов
- Фильтрация рецептов по тегам
- Работа с избранными рецептами
- Система подписок на авторов
- Формирование списка покупок на основе выбранных рецептов
- Поиск по ингредиентам

## Установка
1. Создать директорию foodgram, в ней пустой файл .env и папку infra:
    ```
    foodgram/
    │── infra/
    │── .env

    ```
1. Скопировать файлы из репозитория в папке infra в foodgram/infra:
    - docker-compose.yml
    - nginx.conf
    ```
    foodgram/
    │── infra/
    │   │── docker-compose.yml
    │   │── nginx.conf
    │── .env
    ```
2. Заполнить .env следующими данными(для примера можно воспользоваться .env.example в корне проекта):
    ```
    SECRET_KEY=<КЛЮЧ>
    DEBUG=True(если на процессе отладки)
    ALLOWED_HOSTS=123.123.123.123,yoursite.com,localhost,127.0.0.1

    POSTGRES_DB=foodgram
    DATABASE_USER=ия пользователя бд
    DATABASE_PASSWORD=пароль бд
    DB_NAME=имя бд
    DB_HOST=db
    DB_PORT=5432
    ```
3. Перейти в папку infra и выполнить команды::
    ```
    docker-compose up -d
    docker-compose exec backend python manage.py makemigrations
    docker-compose exec backend python manage.py migrate
    docker-compose exec backend python manage.py collectstatic --no-input
    # опциональная команда для загрузки тестовых данных ingredients.csv и tags.csv из папки data
    docker-compose exec backend python manage.py import_csv
    ```
4. Создайте суперпользователя выполнив команду и следуя инструкции в терминале:
    ```
    docker-compose exec backend python manage.py createsuperuser
    ```
5. Запустите проект:
    ```
    python backend/manage.py runserver
    ```
6. Опционально. После запуска сервера полная версия документации API доступна будет доступна [здесь](http://127.0.0.1:8000/api/redoc/)


### Авторизация:
Для авторизованных запросов необходимо передавать токен в заголовке:
```
Authorization: Token <токен>
```

### Примеры запросов
1. ## Получение списка пользователей
```
GET /api/users/
```
**Ответ:**
```json
{
  "count": 123,
  "next": "http://foodgram.example.org/api/users/?page=4",
  "previous": "http://foodgram.example.org/api/users/?page=2",
  "results": [
    {
      "email": "vpupkin@yandex.ru",
      "id": 1,
      "username": "vasya.pupkin",
      "first_name": "Вася",
      "last_name": "Иванов",
      "is_subscribed": false,
      "avatar": "http://foodgram.example.org/media/users/image.png"
    }
  ]
}
```

2. **Регистрация пользователя**
```
POST /api/users/
```
**Ответ:**
```json
{
  "email": "vpupkin@yandex.ru",
  "id": 1,
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Иванов"
}
```
3. **Получение информации о пользователе**
```
GET /api/users/{id}/
```
**Ответ:**
```json
{
  "email": "vpupkin@yandex.ru",
  "id": 1,
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Иванов",
  "is_subscribed": false,
  "avatar": "http://foodgram.example.org/media/users/image.png"
}
```
4. **Список тегов**
```
GET /api/tags/
```
**Ответ:**
```json
[
  {
    "id": 1,
    "name": "Завтрак",
    "slug": "breakfast"
  }
]
```
5. **Создание рецепта**
```
POST /api/recipes/
```
**Ответ:**
```json
{
  "id": 42,
  "tags": [{"id": 1, "name": "Завтрак", "slug": "breakfast"}],
  "author": {
    "email": "vpupkin@yandex.ru",
    "id": 1,
    "username": "vasya.pupkin",
    "first_name": "Вася",
    "last_name": "Иванов"
  },
  "ingredients": [
    {
      "id": 1123,
      "name": "Картофель отварной",
      "measurement_unit": "г",
      "amount": 10
    }
  ],
  "is_favorited": false,
  "is_in_shopping_cart": false,
  "name": "Омлет с картофелем",
  "image": "http://foodgram.example.org/media/recipes/images/image.png",
  "text": "Описание рецепта",
  "cooking_time": 30
}
```
6. **Скачать список покупок**
```
GET /api/recipes/download_shopping_cart/
```
**Ответ:**
```
Список покупок:
- Картофель отварной: 10 г
- Яйца: 2 шт
```
7. **Добавить рецепт в избранное**
```
POST /api/recipes/{id}/favorite/
```
**Ответ:**
```json
{
  "id": 42,
  "name": "Омлет с картофелем",
  "image": "http://foodgram.example.org/media/recipes/images/image.png",
  "cooking_time": 30
}
```
8. **Изменение пароля**
```
POST /api/users/set_password/
```
**Ответ:**  
```json
{}
```
(Статус-код 204)
9. **Получение токена авторизации**
```
POST /api/auth/token/login/
```
**Ответ:**
```json
{
  "auth_token": "string"
}
```
10. **Получение ингредиента**
```
GET /api/ingredients/{id}/
```
**Ответ:**
```json
{
  "id": 5,
  "name": "Молоко",
  "measurement_unit": "л"
}
```


## Авторы
Backand:
- [alanbong](https://github.com/alanbong)
Frontend:
- [yandex-praktikum](https://github.com/yandex-praktikum)