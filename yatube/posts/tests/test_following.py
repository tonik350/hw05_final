from django.test import TestCase, Client
from django.urls import reverse

from ..models import User, Group, Post, Follow


class TestFollowing(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
        cls.follower = User.objects.create(username='follower')
        cls.no_follower = User.objects.create(username='no_follower')
        cls.authorized_author_client = Client()
        cls.authorized_follower_client = Client()
        cls.guest_client = Client()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый текст',
        )

    def setUp(self):
        self.authorized_follower_client.force_login(self.follower)

    def test_auth_user_can_follow_author(self):
        """
        Авторизованный пользователь может подписываться на других
        пользователей
        """
        response = self.authorized_follower_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.author}),
        )
        self.assertTrue(Follow.objects.filter(
            user=self.follower, author=self.author
        ).exists())

    def test_auth_user_can_follow_author(self):
        """
        Авторизованный пользователь может отписываться от других
        пользователей
        """
        response = self.authorized_follower_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author}
            ),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.author}),
        )
        self.assertFalse(Follow.objects.filter(
            user=self.follower, author=self.author
        ).exists())

    def test_adding_subscriptions_feed(self):
        """
        Новая запись автора появляется в ленте подписанных на него
        пользователей
        """
        self.authorized_follower_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}),
            follow=True
        )
        new_post = Post.objects.create(
            text='Новый пост в ленте',
            author=self.author,
        )
        response = self.authorized_followe_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(new_post, response.context['page_obj'])

    def test_adding_subscriptions_feed(self):
        """
        Новая запись автора не появляется в ленте неподписанных на него
        пользователей
        """
        self.authorized_no_follower_client = Client()
        self.authorized_no_follower_client.force_login(self.no_follower)
        self.authorized_follower_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}),
            follow=True
        )
        new_post = Post.objects.create(
            text='Новый пост в ленте',
            author=self.author,
        )
        response = self.authorized_no_follower_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(new_post, response.context['page_obj'])
