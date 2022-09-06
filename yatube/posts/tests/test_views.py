import shutil
import tempfile

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache

from posts.models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.author_client = Client()
        cls.author_client.force_login(PostPagesTests.author)
        cls.user = User.objects.create_user(username='Gribobas')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.group_with_post = Group.objects.create(
            title='Тестовое название',
            slug='slug_group_with_post',
            description='Тестовое описание'
        )
        cls.group_without_post = Group.objects.create(
            title='Тестовое название',
            slug='slug_group_without_post',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group_with_post,
            image=cls.uploaded
        )
        cls.URLS_DIC = {
            'INDEX':
                reverse('posts:index'),
            'GROUP_LIST':
                reverse('posts:group_list',
                        kwargs={'slug': 'slug_group_with_post'}),
            'PROFILE':
                reverse('posts:profile',
                        kwargs={'username': 'author'}),
            'POST_DETAIL':
                reverse('posts:post_detail',
                        kwargs={'post_id': cls.post.pk}),
            'POST_EDIT':
                reverse('posts:post_edit',
                        kwargs={'post_id': cls.post.pk}),
            'POST_CREATE':
                reverse('posts:post_create')
        }

    def setUp(self):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        URLS = self.URLS_DIC
        templates_pages_names = {
            URLS['INDEX']: 'posts/index.html',
            URLS['GROUP_LIST']: 'posts/group_list.html',
            URLS['PROFILE']: 'posts/profile.html',
            URLS['POST_DETAIL']: 'posts/post_detail.html',
            URLS['POST_EDIT']: 'posts/create_post.html',
            URLS['POST_CREATE']: 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_displaying_post_on_different_pages(self):
        """Тестовый пост отображается на нужных страницах"""
        URLS = [self.URLS_DIC['INDEX'],
                self.URLS_DIC['GROUP_LIST'],
                self.URLS_DIC['PROFILE']]
        for url in URLS:
            response = self.authorized_client.get(url)
            response_without_post = self.authorized_client.get(
                reverse(
                    'posts:group_list',
                    kwargs={'slug': 'slug_group_without_post'}
                )
            )
            self.assertContains(response, self.post)
            self.assertNotContains(response_without_post, self.post)

    def test_index_group_list_profile_show_correct_context(self):
        """Шаблоны index, group_list, profile
        сформированы с правильным контекстом."""
        USED_URLS = [self.URLS_DIC['INDEX'],
                     self.URLS_DIC['GROUP_LIST'],
                     self.URLS_DIC['PROFILE']]
        for url in USED_URLS:
            response = self.authorized_client.get(url)
            first_object = response.context['page_obj'][0]
            post_text_0 = first_object.text
            post_author_0 = first_object.author.username
            post_image_0 = first_object.image
            self.assertEqual(post_text_0, 'Тестовый текст')
            self.assertEqual(post_author_0, 'author')
            self.assertEqual(post_image_0, 'posts/small.gif')

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            self.URLS_DIC['POST_DETAIL']
        ))
        self.assertEqual(
            response.context.get('post').text,
            'Тестовый текст'
        )
        self.assertEqual(
            response.context.get('post').author.username,
            'author'
        )
        self.assertEqual(
            response.context.get('post').group.title,
            'Тестовое название'
        )
        self.assertEqual(
            response.context.get('post').image,
            'posts/small.gif'
        )

    def test_post_edit_and_create_page_show_correct_context(self):
        """Шаблоны post_edit и post_create
        сформированы с правильным контекстом."""
        USED_URLS = [self.URLS_DIC['POST_EDIT'],
                     self.URLS_DIC['POST_CREATE']]
        for url in USED_URLS:
            response = self.authorized_client.get(url)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField
            }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='slug',
            description='Тестовое описание'
        )
        cls.posts = Post.objects.bulk_create(
            [Post(
                text='Тестовый текст' + str(i),
                author=cls.author,
                group=cls.group
            ) for i in range(13)]
        )
        cls.URLS_DIC = {
            'INDEX':
                reverse('posts:index'),
            'GROUP_LIST':
                reverse('posts:group_list',
                        kwargs={'slug': 'slug'}),
            'PROFILE':
                reverse('posts:profile',
                        kwargs={'username': 'author'})
        }

    def setUp(self):
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Первая страница index, group_list, profile
        содержит 10 постов"""
        URLS = list(self.URLS_DIC.keys())
        for url in URLS:
            response = self.client.get(
                self.URLS_DIC[url]
            )
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Первая страница index, group_list, profile
        содержит 3 поста"""
        URLS = list(self.URLS_DIC.keys())
        for url in URLS:
            response = self.client.get(
                self.URLS_DIC[url] + '?page=2'
            )
            self.assertEqual(len(response.context['page_obj']), 3)


class CacheViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_user = User.objects.create_user(username='user')
        cls.authorized_user_client = Client()
        cls.authorized_user_client.force_login(cls.authorized_user)

    def test_index_cache(self):
        """Проверка кеширования главной страницы"""
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.authorized_user
        )
        response_before_clear = self.authorized_user_client.get(
            reverse('posts:index')
        )
        post.delete()
        self.assertIn(post.text,
                      response_before_clear.content.decode('utf-8'))
        cache.clear()
        response_after_clear = self.authorized_user_client.get(
            reverse('posts:index')
        )
        self.assertNotIn(post.text,
                         response_after_clear.content.decode('utf-8'))
        self.assertNotEqual(response_before_clear, response_after_clear)
