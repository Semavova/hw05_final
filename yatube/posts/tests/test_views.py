import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.settings import SMALL_GIF

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
                self.assertEqual(
                    response.context.get('user').username, USER
                )
                if name != 'post_detail':
                    self.assertEqual(len(response.context['page_obj']), 1)
                    first_post = response.context['page_obj'][0]
                else:
                    first_post = response.context.get('post')
                post_text = first_post.text
                post_image = first_post.image
                post_id = first_post.id
                post_author = first_post.author.get_full_name
                post_pub_date = first_post.pub_date
                post_group = first_post.group.title
                post_group_slug = first_post.group.slug
                post_group_description = first_post.group.description
                self.assertEqual(post_text, self.post.text)
                self.assertEqual(post_image, self.post.image)
                self.assertEqual(post_id, self.post.id)
                self.assertEqual(post_author, self.post.author.get_full_name)
                self.assertEqual(post_pub_date, self.post.pub_date)
                self.assertEqual(post_group, self.group.title)
                self.assertEqual(post_group_slug, self.group.slug)
                self.assertEqual(
                    post_group_description, self.group.description
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
        self.assertEqual(
            response.context.get('group'), self.group
        )
        self.assertEqual(
            response.context.get('group').id, self.group.id
        )
        self.assertEqual(
            response.context.get('group').slug, self.group.slug
        )
        self.assertEqual(
            response.context.get('group').title, self.group.title
        )
        self.assertEqual(
            response.context.get('group').description, self.group.description
        )

    def test_post_is_not_on_another_group_or_subscriptions_page(self):
        """Пост не попал на чужую групп-ленту или ленту подписок."""
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

    def test_post_is_not_on_other_subscriptions(self):
        '''Пост не попал на чужую ленту подписок'''
        response = self.author_client.get(FOLLOW_URL)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_only_authorized_user_can_subscribe(self):
        '''Только авторизованный пользователь может подписаться'''
        Follow.objects.all().delete()
        self.user_client.get(
            PROFILE_FOLLOW,
            {'username': self.author},
            follow=True,
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )

    def test_only_authorized_user_can_subscribe(self):
        '''Только авторизованный пользователь может удалять из подписок'''
        self.user_client.get(
            PROFILE_UNFOLLOW,
            {'username': self.author},
            follow=True,
        )
        self.assertFalse(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )
