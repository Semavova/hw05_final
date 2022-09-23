import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.settings import SMALL_GIF

from ..forms import CommentForm, PostForm
from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
USERNAME = 'StasBasov'
USER = 'NoName'
GROUP_SLUG = 'test-slug'
PROFILE_URL = reverse('posts:profile', args=(USERNAME,))
POST_CREATE_URL = reverse('posts:post_create')
LOGIN_URL = reverse('users:login')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user_not_author = User.objects.create_user(username=USER)
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user_not_author)
        cls.user = User.objects.create_user(username=USERNAME)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.newgroup = Group.objects.create(
            title='Новая тестовая группа',
            slug='new-test-slug'
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            text='Тестовый пост',
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', args=(cls.post.id,)
        )
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=(cls.post.id,))
        cls.COMMENT_URL = reverse('posts:add_comment', args=(cls.post.id,))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        Post.objects.all().delete()
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(Post.objects.count(), 1)
        new_post = Post.objects.first()
        self.assertEqual(form_data.get('text'), new_post.text)
        self.assertEqual(
            form_data.get('group'), new_post.group.id
        )
        self.assertEqual(self.user, new_post.author)
        self.assertEqual(
            'posts/' + form_data.get('image').name, new_post.image.name
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст',
            'group': self.newgroup.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, self.POST_DETAIL_URL
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(Post.objects.count(), 1)
        edited_post = Post.objects.first()
        self.assertEqual(form_data.get('text'), edited_post.text)
        self.assertEqual(
            form_data.get('group'), edited_post.group.id
        )
        self.assertEqual(self.post.author, edited_post.author)
        self.assertEqual(self.post.id, edited_post.id)
        self.assertEqual(
            'posts/' + form_data.get('image').name, edited_post.image.name
        )

    def test_create_post_template_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        reverse_names = (
            POST_CREATE_URL,
            self.POST_EDIT_URL
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for name in reverse_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context.get('form'), PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value
                        )
                        self.assertIsInstance(form_field, expected)

    def test_anonymous_can_not_create_or_edit_post(self):
        """Аноним не может создать или отредактировать пост"""
        posts_count = Post.objects.count()
        posts = Post.objects
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
            'image': self.uploaded.open(),
        }
        urls = (
            POST_CREATE_URL,
            self.POST_EDIT_URL,
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.post(
                    url,
                    data=form_data,
                    follow=True
                )
                self.assertRedirects(
                    response, LOGIN_URL + '?next=' + url
                )
                self.assertEqual(Post.objects.count(), posts_count)
                self.assertEqual(Post.objects, posts)

    def test_not_author_can_not_edit_post(self):
        '''Не автор не может отредактировать пост'''
        posts_count = Post.objects.count()
        posts = Post.objects
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.auth_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, self.POST_DETAIL_URL
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(Post.objects, posts)

    def test_leave_comment(self):
        """Валидная форма оставляет комментарий к посту."""
        Comment.objects.all().delete()
        form_data = {
            'text': 'Комментарий',
        }
        response = self.authorized_client.post(
            self.COMMENT_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertEqual(Comment.objects.count(), 1)
        new_comment = Comment.objects.all().first()
        self.assertEqual(form_data.get('text'), new_comment.text)
        self.assertEqual(self.user, new_comment.author)
        self.assertEqual(self.post, new_comment.post)

    def test_anonymous_can_not_leave_comment(self):
        """Аноним не может оставить комментарий"""
        comments = Comment.objects
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Новый пост',
        }
        response = self.guest_client.post(
            self.COMMENT_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, LOGIN_URL + '?next=' + self.COMMENT_URL
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertEqual(Comment.objects, comments)

    def test_leave_comment_template_show_correct_context(self):
        '''Шаблон add_comment сформирован с правильным контекстом.'''
        response = self.authorized_client.get(self.POST_DETAIL_URL)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context.get('form'), CommentForm)
        self.assertIsInstance(
            response.context.get('form').fields.get('text'),
            forms.fields.CharField
        )
