from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class CustomErrorPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_custom_page_404(self):
        """Страница 404 использует кастомный шаблон"""
        url = '/unexisting_page/'
        template = 'core/404.html'
        response = self.guest_client.get(url)
        self.assertTemplateUsed(response, template)
