from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.author_client = Client()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.author = User.objects.create_user(username='author')
        cls.authorized_client.force_login(cls.user)
        cls.author_client.force_login(PostURLTests.author)
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание'
        )

    def test_unexisting_page(self):
        """Тестирование поведения несуществующей страницы"""
        url = '/unexisting_page/'
        response = self.guest_client.get(url)
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
            'Магия, оказывается, несуществующая '
            'страница доступна пользователям'
        )

    def test_urls_accessible_to_any_user(self):
        """Тестирование страниц, доступных всем пользователям"""
        urls_list = [
            '/', '/group/test-slug/',
            '/profile/author/',
            f'/posts/{PostURLTests.post.pk}/',
        ]
        for url in urls_list:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    'Что-то сломалось, '
                    'код страницы не совпадает с ожидаемым'
                )

    def test_urls_accessible_to_authorized_user(self):
        """Тестирование страниц, доступных авторизованным пользователям"""
        urls_list = ['/create/']
        for url in urls_list:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    'Что-то сломалось, '
                    'код страницы не совпадает с ожидаемым'
                )

    def test_urls_accessible_to_author(self):
        """Тестирование страниц, доступных автору поста"""
        urls_list = [f'/posts/{PostURLTests.post.pk}/edit/']
        for url in urls_list:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    'Что-то сломалось, '
                    'код страницы не совпадает с ожидаемым'
                )

    def test_redirect_anonymous(self):
        """Тестирование редиректов неавторизованных пользователей"""
        urls_list = [f'/posts/{PostURLTests.post.pk}/edit/', '/create/']
        for url in urls_list:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.FOUND,
                    'Что-то сломалось, '
                    'код страницы не совпадает с ожидаемым'
                )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/':
                'posts/index.html',
            '/group/test-slug/':
                'posts/group_list.html',
            '/profile/author/':
                'posts/profile.html',
            f'/posts/{PostURLTests.post.pk}/':
                'posts/post_detail.html',
            f'/posts/{PostURLTests.post.pk}/edit/':
                'posts/create_post.html',
            '/create/':
                'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
