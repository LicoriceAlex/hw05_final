# Cоциальная сеть Yatube
### Описание
Проект Yatube - блог платформа. Позволяет создавать, редактировать, комментировать посты, подписываться и следить за авторами. 
### Технологии
Django 2.2.16
mixer 7.1.2
Pillow 8.3.1
pytest 6.2.4
pytest-django 4.4.0
pytest-pythonpath 0.7.3
requests 2.26.0
six 1.16.0
sorl-thumbnail 12.7.0
Faker 12.0.1
Bootstrap 5
### Запуск проекта в dev-режиме
Cоздать и активировать виртуальное окружение:
```
python3 -m venv env
```
```
source env/bin/activate
```
Установить зависимости из файла requirements.txt:
```
python3 -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```
Выполнить миграции:
```
python3 manage.py migrate
```
Запустить проект:
```
python3 manage.py runserver
```
### Стек технологий
Python, Django framework, HTML, CSS, Bootstrap 
### Авторы
 Саша Савин
