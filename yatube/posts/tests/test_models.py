from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()
NUM_OF_CHAR = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post_str = PostModelTest.post.__str__()
        group_str = PostModelTest.group.__str__()
        expected_post_str = PostModelTest.post.text[:NUM_OF_CHAR]
        expected_group_str = PostModelTest.group.title
        self.assertEquals(
            post_str,
            expected_post_str,
            (
                'Значение поля __str__ в объекте'
                'модели Post отображается неправильно'
            )
        )
        self.assertEquals(
            group_str,
            expected_group_str,
            (
                'Значение поля __str__ в объекте'
                'модели Group отображается неправильно'
            )
        )

    def test_post_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name,
                    expected,
                    'verbose_name в полях модели Post не совпадает с ожидаемым'
                )

    def test_post_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)
