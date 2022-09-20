from django.test import TestCase
from django.urls import reverse

from ..models import Group, Post, User

USERNAME = 'StasBasov'
GROUP_SLUG = 'test-slug'
INDEX_PAGE = reverse('posts:index')
GROUP_POSTS_PAGE = reverse('posts:group_posts', args=(GROUP_SLUG,))
PROFILE_PAGE = reverse('posts:profile', args=(USERNAME,))
POST_CREATE_PAGE = reverse('posts:post_create')
LOGIN_PAGE = reverse('users:login')


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(USERNAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            text='Тестовый текст поста'
        )
        cls.POST_DETAIL_PAGE = reverse(
            'posts:post_detail', args=(cls.post.id,)
        )
        cls.POST_EDIT_PAGE = reverse('posts:post_edit', args=(cls.post.id,))

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        route_address_list = (
            ('/', INDEX_PAGE),
            ('/create/', POST_CREATE_PAGE),
            (f'/group/{GROUP_SLUG}/', GROUP_POSTS_PAGE),
            (f'/posts/{self.post.id}/', self.POST_DETAIL_PAGE),
            (f'/profile/{USERNAME}/', PROFILE_PAGE),
            (f'/posts/{self.post.id}/edit/', self.POST_EDIT_PAGE),
        )
        for route, address in route_address_list:
            with self.subTest(address=address):
                self.assertEqual(address, route)
