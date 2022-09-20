import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..forms import PostForm, CommentForm

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
USERNAME = 'StasBasov'
GROUP_SLUG = 'test-slug'
INDEX_PAGE = reverse('posts:index')
GROUP_POSTS_PAGE = reverse('posts:group_posts', args=(GROUP_SLUG,))
PROFILE_PAGE = reverse('posts:profile', args=(USERNAME,))
POST_CREATE_PAGE = reverse('posts:post_create')
LOGIN_PAGE = reverse('users:login')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.guest_client = Client()
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
        cls.POST_DETAIL_PAGE = reverse(
            'posts:post_detail', args=(cls.post.id,)
        )
        cls.POST_EDIT_PAGE = reverse('posts:post_edit', args=(cls.post.id,))
        cls.COMMENT_PAGE = reverse('posts:add_comment', args=(cls.post.id,))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_Post(self):
        """Валидная форма создает запись в Post."""
        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)
        Posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            POST_CREATE_PAGE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, PROFILE_PAGE)
        self.assertEqual(Post.objects.count(), Posts_count + 1)
        new_post = Post.objects.first()
        self.assertEqual(form_data.get('text'), new_post.text)
        self.assertEqual(
            form_data.get('group'), new_post.group.id
        )
        self.assertEqual(self.user, new_post.author)

    def test_edit_Post(self):
        """Валидная форма изменяет запись в Post."""
        Posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст',
            'group': self.newgroup.id,
        }
        response = self.authorized_client.post(
            self.POST_EDIT_PAGE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, self.POST_DETAIL_PAGE
        )
        self.assertEqual(Post.objects.count(), Posts_count)
        self.assertEqual(Post.objects.count(), 1)
        edited_post = Post.objects.first()
        self.assertEqual(form_data.get('text'), edited_post.text)
        self.assertEqual(
            form_data.get('group'), edited_post.group.id
        )
        self.assertEqual(self.post.author, edited_post.author)
        self.assertEqual(self.post.id, edited_post.id)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        reverse_names = (
            POST_CREATE_PAGE,
            self.POST_EDIT_PAGE
        )
        for name in reverse_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                    'image': forms.fields.ImageField,
                }
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context.get('form'), PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value
                        )
                        self.assertIsInstance(form_field, expected)

    def test_anonymous_can_not_create_post(self):
        """Аноним не может создать пост"""
        Posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            POST_CREATE_PAGE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, LOGIN_PAGE + '?next=' + POST_CREATE_PAGE
        )
        self.assertEqual(Post.objects.count(), Posts_count)

    def test_leave_comment(self):
        """Валидная форма оставляет комментарий к посту."""
        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)
        Comment_count = Comment.objects.count()
        form_data = {
            'text': 'Комментарий',
        }
        response = self.authorized_client.post(
            self.COMMENT_PAGE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL_PAGE)
        self.assertEqual(Comment.objects.count(), Comment_count + 1)
        new_comment = Comment.objects.filter(post=self.post).first()
        self.assertEqual(form_data.get('text'), new_comment.text)
        self.assertEqual(self.user, new_comment.author)
        self.assertEqual(self.post, new_comment.post)

    def test_anonymous_can_not_leave_comment(self):
        """Аноним не может оставить комментарий"""
        Comment_count = Comment.objects.count()
        form_data = {
            'text': 'Новый пост',
        }
        response = self.guest_client.post(
            self.COMMENT_PAGE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, LOGIN_PAGE + '?next=' + self.COMMENT_PAGE
        )
        self.assertEqual(Comment.objects.count(), Comment_count)

    def test_leave_comment_page_show_correct_context(self):
        '''Шаблон add_comment сформирован с правильным контекстом.'''
        response = self.authorized_client.get(self.POST_DETAIL_PAGE)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context.get('form'), CommentForm)
        self.assertIsInstance(
            response.context.get('form').fields.get('text'),
            forms.fields.CharField
        )
