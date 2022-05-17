from http import HTTPStatus

from django.core.cache import cache
from django.test import TestCase, Client

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='post_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.test_url_templates_names_data = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        cls.test_urls_in_desired_locations_data = {
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.user.username}/',
            f'/posts/{cls.post.id}/'
        }
        cls.test_urls_redirect_anonymous_data = {
            '/create/',
            f'/posts/{cls.post.id}/edit/',
            f'/posts/{cls.post.id}/comment/',
            '/follow/',
            f'/profile/{cls.user}/follow/',
            f'/profile/{cls.user}/unfollow/'
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_public_urls_exist_at_desired_location(self):
        """Общедоступные страницы доступны любому пользователю."""
        for url in self.test_urls_in_desired_locations_data:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_users_urls_exist_at_desired_location(self):
        """
        Страницы для авторизованных пользователей доступны авторизованным
        пользователям.
        """
        urls = {
            '/create/',
            f'/posts/{self.post.id}/edit/',
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_url_exists_at_desired_location_author(self):
        """Страница редактирования поста доступна автору поста."""
        url = f'/posts/{self.post.id}/edit/'
        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_url_redirect_no_author_on_post_detail(self):
        """
        Страница редактирования поста перенаправит зарегистрированного
        пользователя (не автора) на страницу поста.
        """
        self.user1 = User.objects.create_user(username='no_post_author')
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)
        url = f'/posts/{self.post.id}/edit/'
        response = self.authorized_client1.get(url)
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_urls_use_correct_template(self):
        """
        URL-адреса используют соответствующие шаблоны.
        """
        for address, template in self.test_url_templates_names_data.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_private_urls_redirect_anonymous_on_admin_login(self):
        """
        Страницы, недоступные для анонимного пользователя перенаправляет
        анонимного пользователя на страницу регистрации.
        """
        for url in self.test_urls_redirect_anonymous_data:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, f'/auth/login/?next={url}')

    def test_unexisting_page(self):
        """
        Запрос к несуществующей странице возвращает ошибку 404
        """
        response = self.guest_client.get('/unexisting_page.')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
