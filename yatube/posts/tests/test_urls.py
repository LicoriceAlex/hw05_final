from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

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
        cls.author_client.force_login(cls.author)
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание'
        )

    def setUp(self):
        cache.clear()

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
        urls_list = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.author.username}),
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk}),
        )
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
        urls_list = (reverse('posts:post_create'),
                     reverse('posts:follow_index'))
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
        urls_list = [reverse('posts:post_edit',
                             kwargs={'post_id': self.post.pk})]
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
        urls_list = (reverse('posts:post_edit',
                     kwargs={'post_id': self.post.pk}),
                     reverse('posts:post_create'),
                     reverse('posts:follow_index'))
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
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.author.username}):
                'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk}):
                'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}):
                'posts/create_post.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            reverse('posts:follow_index'):
                'posts/follow.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_custom_page_404(self):
        """Страница 404 использует кастомный шаблон"""
        url = '/unexisting_page/'
        template = 'core/404.html'
        response = self.guest_client.get(url)
        self.assertTemplateUsed(response, template)
