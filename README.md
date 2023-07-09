# Проект Нфегиу: подписки на авторов

### hw05_final - Проект спринта: подписки на авторов, Яндекс.Практикум.

Покрытие тестами проекта Yatube. Реализована система подписок/отписок на авторов постов.

Стек:

- Python 3.10.5
- Django==2.2.28

### Настройка и запуск на ПК

Клонируем проект:

```bash
git clone https://github.com/semavova/hw05_final.git
```

или

```bash
git clone git@github.com:semavova/hw05_final.git
```

Переходим в папку с проектом:

```bash
cd hw05_final
```

Устанавливаем виртуальное окружение:

```bash
python -m venv venv
```

Активируем виртуальное окружение:

```bash
source venv/Scripts/activate
```

Устанавливаем зависимости:

```bash
python -m pip install --upgrade pip
```
```bash
pip install -r requirements.txt
```

Применяем миграции:

```bash
python yatube/manage.py makemigrations
python yatube/manage.py migrate
```

Создаем супер пользователя:

```bash
python yatube/manage.py createsuperuser
```

При желании делаем коллекцию статики (часть статики уже загружена в репозиторий в виде исключения):

```bash
python yatube/manage.py collectstatic
```

В папку с проектом, где файл settings.py добавляем файл .env куда прописываем ваши параметры:

```bash
SECRET_KEY='Ваш секретный ключ'
ALLOWED_HOSTS='127.0.0.1, localhost'
DEBUG=True
```

Не забываем добавить в .gitingore файлы:

```bash
.env
.venv
```

Запускаем проект:

```bash
python yatube/manage.py runserver localhost:80
```

После чего проект будет доступен по адресу http://localhost/

Заходим в http://localhost/admin и создаем группы и записи.
После чего записи и группы появятся на главной странице.

Автор: [Владимир Семочкин](https://github.com/Semavova)
