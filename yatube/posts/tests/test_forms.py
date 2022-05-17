import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import User, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='post_author')
        cls.test_group_data = {
            'title': 'Тестовая группа',
            'slug': 'test-slug',
            'description': 'Тестовое описание'
        }
        cls.group = Group.objects.create(**cls.test_group_data)
        cls.post_form_data = {
            'text': 'Тестовый текст 2',
            'group': cls.group.id,
            'image': cls.create_image('image2')
        }
        cls.post_create_data = {
            'text': 'Тестовый текст',
            'group': cls.group,
            'author': cls.user,
            'image': cls.create_image('image')
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_form_data['image'].seek(0)
        self.post_create_data['image'].seek(0)

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @staticmethod
    def create_image(filename):
        small_img = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded_img = SimpleUploadedFile(
            name=f'{filename}.jpeg',
            content=small_img,
            content_type='image/jpeg'
        )
        return uploaded_img

    def test_create_post_form_make_new_object_in_db(self):
        """
        При отправке валидной формы со страницы создания поста
        создаётся новая запись в базе данных.
        """
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.post_form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            f'/profile/{self.user}/'
        )
        self.assertEqual(Post.objects.count(), 1)
        new_post = Post.objects.get()
        self.assertEqual(new_post.text, self.post_form_data['text'])
        self.assertEqual(new_post.group.id, self.post_form_data['group'])
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(
            new_post.image.name,
            f"posts/{self.post_form_data['image'].name}"
        )

    def test_edit_post_form_change_this_post(self):
        """
        При отправке валидной формы со страницы редактирования поста
        происходит изменение этого поста в базе данных.
        """
        post = Post.objects.create(**self.post_create_data)
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': f'{post.pk}'}),
            data=self.post_form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            f'/posts/{post.id}/'
        )
        self.assertEqual(Post.objects.count(), 1)
        post.refresh_from_db()
        self.assertEqual(post.text, self.post_form_data['text'])
        self.assertEqual(post.group.id, self.post_form_data['group'])
        self.assertEqual(
            post.image.name,
            f"posts/{self.post_form_data['image'].name}"
        )
