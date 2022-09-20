from http import HTTPStatus
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post, User

USERNAME = 'StasBasov'
USER = 'NoName'
GROUP_SLUG = 'test-slug'
NOT_EXIST_SLUG = '100'
INDEX_PAGE = reverse('posts:index')
GROUP_POSTS_PAGE = reverse('posts:group_posts', args=(GROUP_SLUG,))
PROFILE_PAGE = reverse('posts:profile', args=(USERNAME,))
POST_CREATE_PAGE = reverse('posts:post_create')
LOGIN_PAGE = reverse('users:login')
GROUP_POSTS_404 = reverse('posts:group_posts', args=(NOT_EXIST_SLUG,))
PROFILE_PAGE_404 = reverse('posts:profile', args=(NOT_EXIST_SLUG,))


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user_not_author = User.objects.create_user(username=USER)
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user_not_author)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.POST_DETAIL_PAGE = reverse(
            'posts:post_detail', args=(cls.post.id,)
        )
        cls.POST_DETAIL_404 = reverse(
            'posts:post_detail', args=(NOT_EXIST_SLUG,)
        )
        cls.POST_EDIT_PAGE = reverse('posts:post_edit', args=(cls.post.id,))

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            (INDEX_PAGE, 'posts/index.html'),
            (POST_CREATE_PAGE, 'posts/create_post.html'),
            (GROUP_POSTS_PAGE, 'posts/group_list.html'),
            (self.POST_DETAIL_PAGE, 'posts/post_detail.html'),
            (PROFILE_PAGE, 'posts/profile.html'),
            (self.POST_EDIT_PAGE, 'posts/create_post.html'),
            (GROUP_POSTS_404, 'core/404.html')
        )
        for address, template in templates_url_names:
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.authorized_client.get(address),
                    template
                )

    def test_post_create_url_redirect_anonymous_on_admin_login(self):
        """Страницы создания и редактирования поста
        перенаправят анонимного пользователя на страницу логина.
        """
        url_redirects_list = (
            (
                self.guest_client,
                POST_CREATE_PAGE,
                LOGIN_PAGE + '?next=' + POST_CREATE_PAGE
            ),
            (
                self.guest_client,
                self.POST_EDIT_PAGE,
                LOGIN_PAGE + '?next=' + self.POST_EDIT_PAGE
            ),
            (
                self.auth_client,
                self.POST_EDIT_PAGE,
                self.POST_DETAIL_PAGE
            )
        )
        for client, address, redirect in url_redirects_list:
            with self.subTest(address=address):

                response = client.get(address, follow=True)
                self.assertRedirects(
                    response, (redirect)
                )

    def test_pages_HTTP_status(self):
        """Запрос к страницам вернет нужные статусы"""
        pages = (
            (GROUP_POSTS_404, self.authorized_client, HTTPStatus.NOT_FOUND),
            (GROUP_POSTS_404, self.guest_client, HTTPStatus.NOT_FOUND),
            (PROFILE_PAGE_404, self.authorized_client, HTTPStatus.NOT_FOUND),
            (PROFILE_PAGE_404, self.guest_client, HTTPStatus.NOT_FOUND),
            (self.POST_DETAIL_404, self.authorized_client,
             HTTPStatus.NOT_FOUND),
            (self.POST_DETAIL_404, self.guest_client, HTTPStatus.NOT_FOUND),
            (self.POST_DETAIL_PAGE, self.authorized_client, HTTPStatus.OK),
            (self.POST_DETAIL_PAGE, self.guest_client, HTTPStatus.OK),
            (self.POST_EDIT_PAGE, self.authorized_client, HTTPStatus.OK),
            (self.POST_EDIT_PAGE, self.guest_client, HTTPStatus.FOUND),
            (INDEX_PAGE, self.authorized_client, HTTPStatus.OK),
            (INDEX_PAGE, self.guest_client, HTTPStatus.OK),
            (POST_CREATE_PAGE, self.authorized_client, HTTPStatus.OK),
            (POST_CREATE_PAGE, self.guest_client, HTTPStatus.FOUND),
            (GROUP_POSTS_PAGE, self.authorized_client, HTTPStatus.OK),
            (GROUP_POSTS_PAGE, self.guest_client, HTTPStatus.OK),
            (PROFILE_PAGE, self.authorized_client, HTTPStatus.OK),
            (PROFILE_PAGE, self.guest_client, HTTPStatus.OK)
        )
        for page, client, status in pages:
            with self.subTest(page=page):
                response = client.get(page)
                self.assertEqual(response.status_code, status)
