from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutAppTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_urls(self):
        """Тестирование доступности страниц"""
        urls_list = (
            reverse('about:author'),
            reverse('about:tech')
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

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
