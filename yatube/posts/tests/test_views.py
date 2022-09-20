import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
USER = 'NoName'
AUTHOR = 'author'
USERNAME = 'StasBasov'
GROUP_SLUG = 'test-slug'
ANOTHER_GROUP_SLUG = 'another-slug'
INDEX_PAGE = reverse('posts:index')
FOLLOW_PAGE = reverse('posts:follow_index')
GROUP_POSTS_PAGE = reverse('posts:group_posts', args=(GROUP_SLUG,))
ANOTHER_GROUP_SLUG_PAGE = reverse(
    'posts:group_posts', args=(ANOTHER_GROUP_SLUG,)
)
PROFILE_PAGE = reverse('posts:profile', args=(USERNAME,))
PROFILE_FOLLOW = reverse('posts:profile_follow', args=(AUTHOR,))
PROFILE_UNFOLLOW = reverse('posts:profile_unfollow', args=(AUTHOR,))


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
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
        cls.user = User.objects.create_user(USERNAME)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.user_not_author = User.objects.create_user(username=USER)
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user_not_author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            text='Тестовый текст поста',
            image=cls.uploaded
        )
        cls.POST_DETAIL_PAGE = reverse(
            'posts:post_detail', args=(cls.post.id,)
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_index_page_show_correct_context(self):
        """Шаблоны страниц сформированы с правильным контекстом."""
        pages = {
            'index': INDEX_PAGE,
            'group_posts': GROUP_POSTS_PAGE,
            'profile': PROFILE_PAGE,
            'post_detail': self.POST_DETAIL_PAGE
        }
        for name, page in pages.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(
                    response.context.get('user').username, USERNAME
                )
                if name != 'post_detail':
                    self.assertEqual(len(response.context['page_obj']), 1)
                    first_post = response.context['page_obj'][0]
                    post_text_0 = first_post.text
                    post_image_0 = first_post.image
                    post_id_0 = first_post.id
                    post_author_0 = first_post.author.get_full_name
                    post_group_0 = first_post.group.title
                    post_group_slug_0 = first_post.group.slug
                    post_group_description_0 = first_post.group.description
                    self.assertEqual(post_text_0, self.post.text)
                    self.assertEqual(post_image_0, self.post.image)
                    self.assertEqual(post_id_0, self.post.id)
                    self.assertEqual(
                        post_author_0, self.post.author.get_full_name
                    )
                    self.assertEqual(post_group_0, self.group.title)
                    self.assertEqual(post_group_slug_0, self.group.slug)
                    self.assertEqual(
                        post_group_description_0, self.group.description
                    )
                    if name == 'group_posts':
                        self.assertEqual(
                            response.context.get('group'), self.group
                        )
                    if name == 'profile':
                        self.assertEqual(
                            response.context.get('author'), self.user
                        )
                else:
                    self.assertEqual(
                        response.context.get('post').author.get_full_name,
                        self.post.author.get_full_name
                    )
                    self.assertEqual(
                        response.context.get('post').text, self.post.text
                    )
                    self.assertEqual(
                        response.context.get('post').id, self.post.id
                    )
                    self.assertEqual(
                        response.context.get('post').image, self.post.image
                    )

    def test_post_is_not_on_another_group_posts_page(self):
        """Пост не попал на чужую групп-ленту."""
        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)
        Post.objects.create(
            group=self.group,
            author=self.user,
            text='Тестовый текст поста'
        )
        Group.objects.create(
            title='Другая Тестовая группа',
            slug=ANOTHER_GROUP_SLUG,
            description='Тестовое описание',
        )
        response = self.authorized_client.get(ANOTHER_GROUP_SLUG_PAGE)
        self.assertEqual(len(response.context['page_obj']), 0)
        response = self.authorized_client.get(GROUP_POSTS_PAGE)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_index_page_cache(self):
        '''Содержимое страницы index кэшируется'''
        Post.objects.all().delete()
        Post.objects.create(
            text='Временный пост',
            author=self.user,
        )
        response = self.authorized_client.get(INDEX_PAGE)
        Post.objects.all().delete()
        self.assertEqual(
            self.authorized_client.get(INDEX_PAGE).content,
            response.content
        )
        cache.clear()
        self.assertNotEqual(
            self.authorized_client.get(INDEX_PAGE).content,
            response.content
        )

    def test_post_is_not_on_other_subscriptions(self):
        '''Пост не попал на чужую ленту подписок'''
        Post.objects.all().delete()
        author = User.objects.create(username=AUTHOR)
        Follow.objects.create(user=self.user, author=author)
        post = Post.objects.create(author=author, text=self.post.text)
        response = self.authorized_client.get(FOLLOW_PAGE)
        self.assertIn(post, response.context['page_obj'])
        response = self.auth_client.get(FOLLOW_PAGE)
        self.assertNotIn(post, response.context['page_obj'])

    def test_only_authorized_client_can_subscribe(self):
        '''Только авторизованный пользователь может подписаться
        и удалять из подписок'''
        author = User.objects.create(username=AUTHOR)
        self.authorized_client.post(
            PROFILE_FOLLOW,
            {'username': author},
            follow=True,
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=author).exists()
        )
        self.authorized_client.post(
            PROFILE_UNFOLLOW,
            {'username': author},
            follow=True,
        )
        self.assertFalse(
            Follow.objects.filter(user=self.user, author=author).exists()
        )
        pages = (
            (PROFILE_FOLLOW, self.authorized_client, True),
            (PROFILE_UNFOLLOW, self.authorized_client, False),
            (PROFILE_FOLLOW, self.guest_client, False),
        )
        for page, client, bool in pages:
            with self.subTest(page=page):
                client.post(
                    page,
                    {'username': author},
                    follow=True,
                )
                self.assertIs(
                    Follow.objects.filter(
                        user=self.user, author=author
                    ).exists(),
                    bool
                )
