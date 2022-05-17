from django.test import TestCase, Client
from django.urls import reverse

from ..models import User, Group, Post, Comment


class TestComments(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.guest_client = Client()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый текст',
        )
        cls.form_data = {
            'post': cls.post,
            'author': cls.user,
            'text': 'Тестовый комментарий'
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_authorized_client(self):
        """Авторизованный пользователь может добавить комментарий."""
        post_id_kwargs = {'post_id': f'{self.post.pk}'}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs=post_id_kwargs),
            data=self.form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs=post_id_kwargs),
        )
        self.assertEqual(Comment.objects.count(), 1)
        new_comment = Comment.objects.get()
        self.assertEqual(new_comment.text, self.form_data['text'])
        self.assertEqual(new_comment.post, self.post)
        self.assertEqual(new_comment.author, self.user)

    def test_comment_guest_client(self):
        """Неавторизованный пользователь не может добавить комментарий."""
        comments_count = Comment.objects.count()
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.post.pk}'}
            ),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(comments_count, Comment.objects.count())

    def test_post_detail_page_show_correct_context_with_comment(self):
        """Добавленный комментарий появляется на странице поста"""
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.post.pk}'}
            ),
            data=self.form_data,
            follow=True
        )
        new_comment = response.context.get('comments')[0]
        self.assertIsInstance(new_comment, Comment)
        self.assertEqual(new_comment.text, self.form_data['text'])
        self.assertEqual(new_comment.post, self.post)
        self.assertEqual(new_comment.author, self.user)

    def test_comments_url_redirect_authorized_user_on_post_page(self):
        """
        Страница добавления комментария к посту перенаправляет авторизованного
        пользователя на страницу этого поста
        """
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/comment/'
        )
        self.assertRedirects(response, f'/posts/{self.post.id}/')
