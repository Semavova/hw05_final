from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

USERNAME = 'StasBasov'
USER = 'NoName'
GROUP_SLUG = 'test-slug'
NOT_EXIST_SLUG = '100'
INDEX_URL = reverse('posts:index')
FOLLOW_URL = reverse('posts:follow_index')
GROUP_POSTS_URL = reverse('posts:group_posts', args=(GROUP_SLUG,))
PROFILE_URL = reverse('posts:profile', args=(USERNAME,))
POST_CREATE_URL = reverse('posts:post_create')
LOGIN_URL = reverse('users:login')
GROUP_POSTS_404 = reverse('posts:group_posts', args=(NOT_EXIST_SLUG,))
PROFILE_URL_404 = reverse('posts:profile', args=(NOT_EXIST_SLUG,))
PROFILE_FOLLOW = reverse('posts:profile_follow', args=(USERNAME,))
PROFILE_UNFOLLOW = reverse('posts:profile_unfollow', args=(USERNAME,))


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest = Client()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user_not_author = User.objects.create_user(username=USER)
        cls.another = Client()
        cls.another.force_login(cls.user_not_author)
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', args=(cls.post.id,)
        )
        cls.POST_DETAIL_404 = reverse(
            'posts:post_detail', args=(NOT_EXIST_SLUG,)
        )
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=(cls.post.id,))
        cls.COMMENT_URL = reverse('posts:add_comment', args=(cls.post.id,))

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            (INDEX_URL, 'posts/index.html'),
            (POST_CREATE_URL, 'posts/create_post.html'),
            (GROUP_POSTS_URL, 'posts/group_list.html'),
            (self.POST_DETAIL_URL, 'posts/post_detail.html'),
            (PROFILE_URL, 'posts/profile.html'),
            (self.POST_EDIT_URL, 'posts/create_post.html'),
            (FOLLOW_URL, 'posts/follow.html'),
            (GROUP_POSTS_404, 'core/404.html'),
        )
        for address, template in templates_url_names:
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.author.get(address),
                    template
                )

    def test_url_redirect_anonymous_on_login_page(self):
        """Страницы перенаправят анонимного пользователя на страницу логина.
        """
        url_redirects_list = (
            (
                self.guest,
                POST_CREATE_URL,
                LOGIN_URL + '?next=' + POST_CREATE_URL
            ),
            (
                self.guest,
                self.POST_EDIT_URL,
                LOGIN_URL + '?next=' + self.POST_EDIT_URL
            ),
            (
                self.another,
                self.POST_EDIT_URL,
                self.POST_DETAIL_URL
            ),
            (
                self.guest,
                FOLLOW_URL,
                LOGIN_URL + '?next=' + FOLLOW_URL,
            ),
            (
                self.guest,
                PROFILE_FOLLOW,
                LOGIN_URL + '?next=' + PROFILE_FOLLOW,
            ),
            (
                self.guest,
                PROFILE_UNFOLLOW,
                LOGIN_URL + '?next=' + PROFILE_UNFOLLOW,
            ),
            (
                self.guest,
                self.COMMENT_URL,
                LOGIN_URL + '?next=' + self.COMMENT_URL,
            ),
            (
                self.author,
                PROFILE_FOLLOW,
                PROFILE_URL,
            ),
        )
        for client, address, redirect in url_redirects_list:
            with self.subTest(
                address=address, client=client, redirect=redirect
            ):
                response = client.get(address, follow=True)
                self.assertRedirects(
                    response, (redirect)
                )

    def test_pages_HTTP_status(self):
        """Запрос к страницам вернет нужные статусы"""
        not_found = HTTPStatus.NOT_FOUND
        ok = HTTPStatus.OK
        found = HTTPStatus.FOUND
        pages = (
            (GROUP_POSTS_404, self.guest, not_found),
            (PROFILE_URL_404, self.guest, not_found),
            (self.POST_DETAIL_404, self.guest, not_found),
            (self.POST_DETAIL_URL, self.guest, ok),
            (self.POST_EDIT_URL, self.author, ok),
            (self.POST_EDIT_URL, self.guest, found),
            (INDEX_URL, self.guest, ok),
            (POST_CREATE_URL, self.author, ok),
            (POST_CREATE_URL, self.guest, found),
            (GROUP_POSTS_URL, self.guest, ok),
            (PROFILE_URL, self.guest, ok),
            (PROFILE_FOLLOW, self.another, found),
            (PROFILE_UNFOLLOW, self.another, found),
            (FOLLOW_URL, self.author, ok),
            (self.COMMENT_URL, self.author, found),
            (PROFILE_FOLLOW, self.guest, found),
            (PROFILE_UNFOLLOW, self.guest, found),
            (FOLLOW_URL, self.guest, found),
            (self.COMMENT_URL, self.guest, found),
        )
        for page, client, status in pages:
            with self.subTest(page=page, client=client, status=status):
                response = client.get(page)
                self.assertEqual(response.status_code, status)
