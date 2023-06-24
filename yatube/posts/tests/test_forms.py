import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
USERNAME = 'StasBasov'
USER = 'NoName'
GROUP_SLUG = 'test-slug'
PROFILE_URL = reverse('posts:profile', args=(USERNAME,))
POST_CREATE_URL = reverse('posts:post_create')
LOGIN_URL = reverse('users:login')
MEDIA_PATH = Post._meta.get_field('image').upload_to
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


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
        post = Post.objects.first()
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(self.user, post.author)
        self.assertEqual(
            MEDIA_PATH + form_data['image'].name, post.image.name
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
        post = Post.objects.first()
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(self.post.author, post.author)
        self.assertEqual(self.post.id, post.id)
        self.assertEqual(
            MEDIA_PATH + form_data['image'].name, post.image.name
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

    def test_anonymous_can_not_create_post(self):
        """Аноним не может создать или отредактировать пост"""
        posts = Post.objects.all()
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
            'image': self.uploaded.open(),
        }
        self.assertRedirects(
            self.guest_client.post(
                POST_CREATE_URL,
                data=form_data,
                follow=True
            ),
            LOGIN_URL + '?next=' + POST_CREATE_URL
        )
        self.assertQuerysetEqual(
            Post.objects.all(), posts, transform=lambda x: x
        )

    def test_not_author_can_not_edit_post(self):
        """Не-автор не может создать или отредактировать пост"""
        posts = Post.objects.all()
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
            'image': self.uploaded.open(),
        }
        list = (
            (self.guest_client, LOGIN_URL + '?next=' + self.POST_EDIT_URL),
            (self.auth_client, self.POST_DETAIL_URL),
        )
        for client, url in list:
            with self.subTest(client=client):
                self.assertRedirects(
                    client.post(
                        self.POST_EDIT_URL, data=form_data, follow=True
                    ), url
                )
                post = Post.objects.get(id=self.post.id)
                self.assertEqual(self.post.text, post.text)
                self.assertEqual(self.post.group.id, post.group.id)
                self.assertEqual(self.post.author, post.author)
                self.assertEqual(self.post.id, post.id)
                self.assertEqual(self.post.image, post.image)
                self.assertQuerysetEqual(
                    Post.objects.all(), posts, transform=lambda x: x
                )

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
        comment = Comment.objects.all().first()
        self.assertEqual(form_data['text'], comment.text)
        self.assertEqual(self.user, comment.author)
        self.assertEqual(self.post, comment.post)

    def test_anonymous_can_not_leave_comment(self):
        """Аноним не может оставить комментарий"""
        comments = Comment.objects.all()
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
        self.assertQuerysetEqual(
            Comment.objects.all(), comments, transform=lambda x: x
        )

    def test_leave_comment_template_show_correct_context(self):
        '''Шаблон add_comment сформирован с правильным контекстом.'''
        response = self.authorized_client.get(self.POST_DETAIL_URL)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context.get('form'), CommentForm)
        self.assertIsInstance(
            response.context.get('form').fields.get('text'),
            forms.fields.CharField
        )
