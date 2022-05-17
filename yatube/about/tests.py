from http import HTTPStatus
from django.test import TestCase, Client
from django.urls import reverse


class StaticPagesTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адресов статичных страниц"""
        urls = {
            '/about/author/',
            '/about/tech/'
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_url_uses_correct_template(self):
        """
        URL-адреса используют соответствующие шаблоны.
        """
        url_templates_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_pages_uses_correct_template(self):
        """Имена URL-адресов используют соответствующие шаблоны."""
        pages_templates_names = {
            'author': {
                'expected': reverse('about:author'),
                'received': 'about/author.html',
            },
            'tech': {
                'expected': reverse('about:tech'),
                'received': 'about/tech.html',
            },
        }
        for page, templates in pages_templates_names.items():
            with self.subTest(page=page):
                response = self.guest_client.get(templates['expected'])
                self.assertTemplateUsed(response, templates['received'])
