import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()
login_url = reverse('users:login')
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.guest = User.objects.create_user(username='guest')
        cls.guest_client = Client()

        cls.author2 = User.objects.create_user(username='author2')
        cls.author2_client = Client()
        cls.author2_client.force_login(cls.author2)

        cls.authorized = User.objects.create_user(username='authorized')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.authorized)

        cls.second_group = Group.objects.create(
            title='Тестовое название',
            slug='slug2',
            description='Тестовое описание'
        )
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
        )

    def setUp(self):
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'

        )
        cache.clear()

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create(self):
        """Валидная форма создает запись в Post.
        Невалидная форма ничего не создает и ничего не ломает"""
        group_id = self.group.pk
        posts_count = Post.objects.count()
        valid_form_data = {
            'text': 'Тестовый текст',
            'group': group_id,
            'image': self.uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=valid_form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': 'author'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(text='Тестовый текст',
                                group=group_id,
                                image='posts/small.gif').exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        posts_count = Post.objects.count()
        invalid_form_data = {
            'text': '',
            'image': self.uploaded,
        }
        invalid_response = self.author_client.post(
            reverse('posts:post_create'),
            data=invalid_form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFormError(
            invalid_response,
            'form',
            'text',
            'Обязательное поле.'
        )
        self.assertEqual(invalid_response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        """При отправке валидной формы со страницы редактирования поста
        происходит изменение поста в базе данных."""
        post_id = self.post.pk
        group_id = self.second_group.pk
        post_edit_url = reverse('posts:post_edit',
                                kwargs={'post_id': post_id})
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Измененный тестовый текст',
            'group': group_id,
            'image': self.uploaded,
        }
        response = self.author_client.post(
            post_edit_url,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': post_id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(text='Измененный тестовый текст',
                                group=group_id,
                                image='posts/small.gif').exists()
        )

    def test_another_author_abilities(self):
        """Авторизованный пользователь не может редактировать
        не свой пост"""
        post_id = self.post.pk
        post_edit_url = reverse('posts:post_edit',
                                kwargs={'post_id': post_id})
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Измененный тестовый текст',
        }
        response = self.author2_client.post(
            post_edit_url,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': post_id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(text='Измененный тестовый текст').exists()
        )

    def test_guest_user_create_post(self):
        """Неавторизованный пользователь не может создавать посты"""
        post_create_url = reverse('posts:post_create')
        redirect_url = f'{login_url}?next={post_create_url}'
        posts_count = Post.objects.count()
        form_data_create = {
            'text': 'Tестовый текст',
        }
        response_create = self.guest_client.post(
            post_create_url,
            data=form_data_create,
            follow=True
        )
        self.assertRedirects(response_create, redirect_url)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(text='Tестовый текст').exists()
        )

    def test_guest_user_edit_post(self):
        """Неавторизованный пользователь не может редактировать посты"""
        post_id = self.post.pk
        post_edit_url = reverse('posts:post_edit',
                                kwargs={'post_id': post_id})
        redirect_url = f'{login_url}?next={post_edit_url}'
        posts_count = Post.objects.count()
        form_data_edit = {
            'text': 'Измененный тестовый текст',
        }
        response_edit = self.guest_client.post(
            post_edit_url,
            data=form_data_edit,
            follow=True
        )
        self.assertRedirects(response_edit, redirect_url)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(text='Измененный тестовый текст').exists()
        )

    def test_comment_in_post_detail(self):
        """Комментировать может только авторизованный пользователь.
        После успешной отправке поста добавляется запись в базе данных"""
        post_id = self.post.pk
        add_comment_url = reverse('posts:add_comment',
                                  kwargs={'post_id': post_id})
        guest_redirect_url = f'{login_url}?next={add_comment_url}'
        comments_count = self.post.comments.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        guest_response = self.guest_client.post(
            add_comment_url,
            data=form_data,
            follow=True
        )
        self.assertRedirects(guest_response, guest_redirect_url)
        self.assertEqual(self.post.comments.count(), comments_count)
        self.assertFalse(
            self.post.comments.filter(
                text='Тестовый комментарий').exists()
        )

        redirect_url = reverse('posts:post_detail',
                               kwargs={'post_id': post_id})
        comments_count = self.post.comments.count()
        authorized_response = self.authorized_client.post(
            add_comment_url,
            data=form_data,
            follow=True
        )
        self.assertRedirects(authorized_response, redirect_url)
        self.assertEqual(self.post.comments.count(), comments_count + 1)
        self.assertTrue(
            self.post.comments.filter(
                text='Тестовый комментарий').exists()
        )

    def test_comment_shows_in_post_detail(self):
        """После добавления комментраия он отображается на странице поста"""
        post_id = self.post.pk
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_id})
        )
        self.assertEqual(len(response.context['comments']), 1)
