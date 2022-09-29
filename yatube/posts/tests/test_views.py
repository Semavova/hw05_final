import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from yatube.settings import POSTS_PER_PAGE

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
AUTHOR = 'author'
USER = 'StasBasov'
GROUP_SLUG = 'test-slug'
ANOTHER_GROUP_SLUG = 'another-slug'
INDEX_URL = reverse('posts:index')
FOLLOW_URL = reverse('posts:follow_index')
GROUP_POSTS_URL = reverse('posts:group_posts', args=(GROUP_SLUG,))
ANOTHER_GROUP_SLUG_URL = reverse(
    'posts:group_posts', args=(ANOTHER_GROUP_SLUG,)
)
PROFILE_URL = reverse('posts:profile', args=(AUTHOR,))
PROFILE_FOLLOW = reverse('posts:profile_follow', args=(AUTHOR,))
PROFILE_UNFOLLOW = reverse('posts:profile_unfollow', args=(AUTHOR,))
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.guest = Client()
        cls.author = User.objects.create_user(AUTHOR)
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.user = User.objects.create_user(USER)
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.another_group = Group.objects.create(
            title='Другая Тестовая группа',
            slug=ANOTHER_GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        Follow.objects.create(user=cls.user, author=cls.author)
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.author,
            text='Тестовый текст поста',
            image=cls.uploaded
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', args=(cls.post.id,)
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_show_correct_context(self):
        """Шаблоны страниц сформированы с правильным контекстом."""
        pages = {
            'index': INDEX_URL,
            'follow_index': FOLLOW_URL,
            'post_detail': self.POST_DETAIL_URL,
            'profile': PROFILE_URL,
            'group_posts': GROUP_POSTS_URL,
        }
        for name, page in pages.items():
            with self.subTest(page=page):
                response = self.user_client.get(page)
                if name != 'post_detail':
                    self.assertEqual(len(response.context['page_obj']), 1)
                    post = response.context['page_obj'][0]
                else:
                    post = response.context.get('post')
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.image, self.post.image)
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(
                    post.author.get_full_name, self.post.author.get_full_name
                )

    def test_profile_page_show_correct_context(self):
        '''Шаблон страницы profile сформирован с правильным контекстом'''
        response = self.author_client.get(PROFILE_URL)
        self.assertEqual(
            response.context.get('author'), self.author
        )

    def test_group_posts_page_show_correct_context(self):
        '''Шаблон страницы group_posts сформирован с правильным контекстом'''
        response = self.author_client.get(GROUP_POSTS_URL)
        group = response.context.get('group')
        self.assertEqual(group.id, self.group.id)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)

    def test_post_is_not_on_foreign_page(self):
        """Пост не попал на чужую страницу."""
        urls = (
            ANOTHER_GROUP_SLUG_URL,
            FOLLOW_URL,
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertNotIn(self.post, response.context['page_obj'])

    def test_index_page_cache(self):
        '''Содержимое страницы index кэшируется'''
        response = self.guest.get(INDEX_URL)
        Post.objects.all().delete()
        self.assertEqual(
            self.guest.get(INDEX_URL).content,
            response.content
        )
        cache.clear()
        self.assertNotEqual(
            self.guest.get(INDEX_URL).content,
            response.content
        )

    def test_only_authorized_user_can_subscribe(self):
        '''Только авторизованный пользователь может подписаться'''
        Follow.objects.all().delete()
        self.user_client.get(
            PROFILE_FOLLOW,
            follow=True,
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )

    def test_only_authorized_user_can_unsubscribe(self):
        '''Только авторизованный пользователь может удалять из подписок'''
        self.user_client.get(
            PROFILE_UNFOLLOW,
            follow=True,
        )
        self.assertFalse(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )

    def test_paginator_is_working(self):
        '''Работоспособность пагинатора'''
        Post.objects.all().delete()
        batch_size = POSTS_PER_PAGE + 1
        Post.objects.bulk_create(
            Post(
                group=self.group,
                author=self.author,
                text='Тестовый пост %s' % i
            ) for i in range(batch_size)
        )
        pages = (
            (INDEX_URL + '?page=1', POSTS_PER_PAGE),
            (FOLLOW_URL + '?page=1', POSTS_PER_PAGE),
            (GROUP_POSTS_URL + '?page=1', POSTS_PER_PAGE),
            (PROFILE_URL + '?page=1', POSTS_PER_PAGE),
            (INDEX_URL + '?page=2', batch_size - POSTS_PER_PAGE),
            (FOLLOW_URL + '?page=2', batch_size - POSTS_PER_PAGE),
            (GROUP_POSTS_URL + '?page=2', batch_size - POSTS_PER_PAGE),
            (PROFILE_URL + '?page=2', batch_size - POSTS_PER_PAGE),
        )
        for url, posts in pages:
            with self.subTest(url=url):
                response = self.user_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), posts
                )
