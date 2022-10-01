from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

USER = 'StasBasov'
AUTHOR = 'author'
GROUP_SLUG = 'test-slug'
NOT_EXIST_SLUG = '100'
INDEX_URL = reverse('posts:index')
FOLLOW_INDEX_URL = reverse('posts:follow_index')
GROUP_POSTS_URL = reverse('posts:group_posts', args=(GROUP_SLUG,))
PROFILE_URL = reverse('posts:profile', args=(AUTHOR,))
POST_CREATE_URL = reverse('posts:post_create')
LOGIN_URL = reverse('users:login')
GROUP_POSTS_404 = reverse('posts:group_posts', args=(NOT_EXIST_SLUG,))
PROFILE_URL_404 = reverse('posts:profile', args=(NOT_EXIST_SLUG,))
FOLLOW_URL = reverse('posts:profile_follow', args=(AUTHOR,))
UNFOLLOW_URL = reverse('posts:profile_unfollow', args=(AUTHOR,))
POST_CREATE_REDIRECT = f'{LOGIN_URL}?next={POST_CREATE_URL}'
FOLLOW_INDEX_REDIRECT = f'{LOGIN_URL}?next={FOLLOW_INDEX_URL}'
FOLLOW_REDIRECT = f'{LOGIN_URL}?next={FOLLOW_URL}'
UNFOLLOW_REDIRECT = f'{LOGIN_URL}?next={UNFOLLOW_URL}'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest = Client()
        cls.author = User.objects.create_user(AUTHOR)
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.user = User.objects.create_user(USER)
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', args=(cls.post.id,)
        )
        cls.POST_DETAIL_404 = reverse(
            'posts:post_detail', args=(NOT_EXIST_SLUG,)
        )
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=(cls.post.id,))
        cls.POST_EDIT_REDIRECT = f'{LOGIN_URL}?next={cls.POST_EDIT_URL}'

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            (INDEX_URL, 'posts/index.html'),
            (POST_CREATE_URL, 'posts/create_post.html'),
            (GROUP_POSTS_URL, 'posts/group_list.html'),
            (self.POST_DETAIL_URL, 'posts/post_detail.html'),
            (PROFILE_URL, 'posts/profile.html'),
            (self.POST_EDIT_URL, 'posts/create_post.html'),
            (FOLLOW_INDEX_URL, 'posts/follow.html'),
            (GROUP_POSTS_404, 'core/404.html'),
        )
        for address, template in templates_url_names:
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.author_client.get(address),
                    template
                )

    def test_url_redirects(self):
        """Тестирование перенаправлений"""
        url_redirects_list = (
            (self.guest, POST_CREATE_URL, POST_CREATE_REDIRECT),
            (self.guest, self.POST_EDIT_URL, self.POST_EDIT_REDIRECT),
            (self.user_client, self.POST_EDIT_URL, self.POST_DETAIL_URL),
            (self.guest, FOLLOW_INDEX_URL, FOLLOW_INDEX_REDIRECT,),
            (self.guest, FOLLOW_URL, FOLLOW_REDIRECT,),
            (self.guest, UNFOLLOW_URL, UNFOLLOW_REDIRECT,),
            (self.author_client, FOLLOW_URL, PROFILE_URL,),
            (self.user_client, FOLLOW_URL, PROFILE_URL,),
            (self.user_client, UNFOLLOW_URL, PROFILE_URL,),
        )
        for client, url, redirect in url_redirects_list:
            with self.subTest(
                url=url, client=client, redirect=redirect
            ):
                self.assertRedirects(
                    client.get(url, follow=True), (redirect)
                )

    def test_pages_HTTP_status(self):
        """Запрос к страницам вернет нужные статусы"""
        NOT_FOUND = HTTPStatus.NOT_FOUND
        OK = HTTPStatus.OK
        FOUND = HTTPStatus.FOUND
        pages = (
            (GROUP_POSTS_404, self.guest, NOT_FOUND),
            (PROFILE_URL_404, self.guest, NOT_FOUND),
            (self.POST_DETAIL_404, self.guest, NOT_FOUND),
            (self.POST_DETAIL_URL, self.guest, OK),
            (self.POST_EDIT_URL, self.author_client, OK),
            (self.POST_EDIT_URL, self.guest, FOUND),
            (INDEX_URL, self.guest, OK),
            (POST_CREATE_URL, self.user_client, OK),
            (POST_CREATE_URL, self.guest, FOUND),
            (GROUP_POSTS_URL, self.guest, OK),
            (PROFILE_URL, self.guest, OK),
            (FOLLOW_URL, self.author_client, FOUND),
            (FOLLOW_URL, self.guest, FOUND),
            (FOLLOW_URL, self.user_client, FOUND),
            (UNFOLLOW_URL, self.user_client, FOUND),
            (UNFOLLOW_URL, self.guest, FOUND),
            (UNFOLLOW_URL, self.author_client, NOT_FOUND),
            (FOLLOW_INDEX_URL, self.guest, FOUND),
            (FOLLOW_INDEX_URL, self.user_client, OK),
        )
        for page, client, status in pages:
            with self.subTest(page=page, client=client, status=status):
                self.assertEqual(client.get(page).status_code, status)
