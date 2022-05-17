import tempfile
import shutil

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post, User, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='post_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.wrong_group_data = {
            'title': 'Тестовая группа 2',
            'slug': 'test-slug-2',
            'description': 'Тестовое описание'
        }
        cls.create_post_form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.small_img = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded_img = SimpleUploadedFile(
            name='image.jpeg',
            content=self.small_img,
            content_type='image/jpeg'
        )
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group,
            image=self.uploaded_img
        )
        self.pages_templates_names = {
            'index': (
                reverse('posts:index'),
                'posts/index.html',
            ),
            'group_list': (
                reverse(
                    'posts:group_list',
                    kwargs={'group_name': f'{self.group.slug}'}
                ),
                'posts/group_list.html',
            ),
            'profile': (
                reverse('posts:profile', kwargs={'username': f'{self.user}'}),
                'posts/profile.html'
            ),
            'post_detail': (
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': f'{self.post.pk}'}
                ),
                'posts/post_detail.html'
            ),
            'post_create': (
                reverse('posts:post_create'),
                'posts/create_post.html'
            ),
            'post_edit': (
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': f'{self.post.pk}'}
                ),
                'posts/create_post.html',
            ),
        }
        self.edit_form_fields = {
            'text': self.post.text,
            'group_id': self.post.group.pk,
            'image': self.post.image,
        }

    def check_context(self, post_object):
        context_obj_data = {
            'pk': {
                'expected': self.post.pk,
                'received': post_object.pk,
            },
            'text': {
                'expected': self.post.text,
                'received': post_object.text,
            },
            'pub_date': {
                'expected': self.post.pub_date,
                'received': post_object.pub_date,
            },
            'author': {
                'expected': self.post.author,
                'received': post_object.author,
            },
            'group': {
                'expected': self.post.group,
                'received': post_object.group,
            },
            'image': {
                'expected': self.post.image,
                'received': post_object.image,
            }
        }
        for field, values in context_obj_data.items():
            with self.subTest(field=field):
                self.assertEqual(values['received'], values['expected'])
        return True

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """Имена URL-адресов используют соответствующие шаблоны."""
        for page, templates in self.pages_templates_names.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(templates[0])
                self.assertTemplateUsed(response, templates[1])

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post_object = response.context.get('page_obj')[0]
        self.assertIn(self.post, response.context.get('page_obj'))
        self.assertIsInstance(post_object, Post)
        self.assertTrue(self.check_context(post_object))

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'group_name': f'{self.group.slug}'}
            )
        )
        post_object = response.context.get('page_obj')[0]
        self.assertIn(self.post, response.context.get('page_obj'))
        self.assertIsInstance(post_object, Post)
        self.assertTrue(self.check_context(post_object))

    def test_post_not_iclude_in_wrong_group_page(self):
        """
        Созданный пост не попал в группу,
        для которой не был предназначен.
        """
        self.wrong_group = Group.objects.create(**self.wrong_group_data)
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'group_name': f'{self.wrong_group.slug}'}
            )
        )
        objects = response.context.get('page_obj')
        self.assertNotIn(self.post, objects)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.user}'}
            )
        )
        post_object = response.context.get('page_obj')[0]
        self.assertIn(self.post, response.context.get('page_obj'))
        self.assertIsInstance(post_object, Post)
        self.assertTrue(self.check_context(post_object))

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.pk}'}
            )
        )
        post_object = response.context.get('post')
        self.assertIsInstance(post_object, Post)
        self.assertTrue(self.check_context(post_object))

    def test_post_create_page_show_correct_context(self):
        """
        Шаблон post_create для создания нового поста сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.get(reverse('posts:post_create'))
        for field, expected in self.create_post_form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_edit_page_show_correct_context(self):
        """
        Шаблон post_edit для редактирования поста сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.pk}'}
            )
        )
        post_in_context = response.context.get('form').instance
        self.assertIsInstance(post_in_context, Post)
        self.assertEqual(post_in_context.pk, self.post.pk)
        for field, expected in self.edit_form_fields.items():
            with self.subTest(field=field):
                field_value = getattr(post_in_context, field)
                self.assertEqual(field_value, expected)

    def test_cache_index_page(self):
        """Тестирование кэша страницы index"""
        response_initial = self.authorized_client.get('/')
        Post.objects.all().delete()
        response_delete_bd = self.authorized_client.get('/')
        self.assertEqual(response_initial.content, response_delete_bd.content)
        cache.clear()
        response_cache_clear = self.authorized_client.get('/')
        self.assertNotEqual(
            response_cache_clear.content,
            response_initial.content
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author
        )

    def setUp(self):
        cache.clear()
        self.posts = [
            Post.objects.create(
                text=f'TestText{_}',
                author=self.author,
                group=self.group,
            ) for _ in range(13)
        ]
        self.client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_first_page_contains_ten_records(self):
        """
        Количество постов на главной первой странице равно
        settings.POST_AMOUNT
        """
        response = self.client.get(reverse('posts:index'))
        page = response.context['page_obj']
        self.assertEqual(page.number, 1)
        self.assertEqual(
            page.end_index() - page.start_index() + 1,
            settings.POST_AMOUNT
        )

    def test_index_second_page_contains_ten_records(self):
        """
        Количество постов на главной второй странице равно
        settings.POST_AMOUNT
        """
        response = self.client.get(reverse('posts:index') + '?page=2')
        page = response.context['page_obj']
        self.assertEqual(page.number, 2)
        self.assertEqual(page.end_index() - page.start_index() + 1, 3)

    def test_group_list_first_page_contains_ten_records(self):
        """
        Количество постов на первой странице группы равно
        settings.POST_AMOUNT.
        """
        response = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={'group_name': f'{self.group.slug}'}
            )
        )
        page = response.context['page_obj']
        self.assertEqual(page.number, 1)
        self.assertEqual(page.paginator.per_page, settings.POST_AMOUNT)
        self.assertEqual(
            page.end_index() - page.start_index() + 1,
            settings.POST_AMOUNT
        )

    def test_index_second_page_contains_three_records(self):
        """
        Количество постов на второй странице группы равно 3.
        """
        response = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={'group_name': f'{self.group.slug}'}
            ) + '?page=2'
        )
        page = response.context['page_obj']
        self.assertEqual(page.number, 2)
        self.assertEqual(page.end_index() - page.start_index() + 1, 3)

    def test_author_list_first_page_contains_ten_records(self):
        """
        Количество постов на первой странице автора равно 10.
        """
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.author}'}
            )
        )
        page = response.context['page_obj']
        self.assertEqual(page.number, 1)
        self.assertEqual(
            page.end_index() - page.start_index() + 1,
            settings.POST_AMOUNT
        )

    def test_author_second_page_contains_three_records(self):
        """
        Количество постов на второй странице автора равно 3.
        """
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.author}'}
            ) + '?page=2'
        )
        page = response.context['page_obj']
        self.assertEqual(page.number, 2)
        self.assertEqual(page.end_index() - page.start_index() + 1, 3)

    def test_follow_list_first_page_contains_ten_records(self):
        """
        Количество постов на первой странице ленты пользователя равно 10.
        """
        response = self.authorized_client.get(reverse('posts:follow_index'))
        page = response.context['page_obj']
        self.assertEqual(page.number, 1)
        self.assertEqual(
            page.end_index() - page.start_index() + 1,
            settings.POST_AMOUNT
        )

    def test_follow_second_first_page_contains_three_records(self):
        """
        Количество постов на второй странице ленты пользователя равно 3.
        """
        response = self.authorized_client.get(
            reverse('posts:follow_index') + '?page=2'
        )
        page = response.context['page_obj']

        self.assertEqual(page.number, 2)
        self.assertEqual(page.end_index() - page.start_index() + 1, 3)
