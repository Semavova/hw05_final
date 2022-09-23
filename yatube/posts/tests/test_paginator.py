from django.test import Client, TestCase
from django.urls import reverse

from yatube.settings import POSTS_PER_PAGES

from ..models import Follow, Group, Post, User

USERNAME = 'StasBasov'
AUTHOR = 'Author'
GROUP_SLUG = 'test-slug'
INDEX_URL = reverse('posts:index')
GROUP_POSTS_URL = reverse('posts:group_posts', args=(GROUP_SLUG,))
PROFILE_URL = reverse('posts:profile', args=(AUTHOR,))
POST_CREATE_URL = reverse('posts:post_create')
FOLLOW_URL = reverse('posts:follow_index')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.author = User.objects.create_user(username=AUTHOR)
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        Follow.objects.create(user=cls.user, author=cls.author)
        cls.batch_size = POSTS_PER_PAGES + 1
        objs = (Post(
            group=cls.group,
            author=cls.author,
            text='Тестовый пост %s' % i
        ) for i in range(cls.batch_size))
        Post.objects.bulk_create(objs, cls.batch_size)

    def test_paginator_is_working(self):
        """Паджинатор работает."""
        pages = (
            (INDEX_URL, '?page=1', POSTS_PER_PAGES),
            (FOLLOW_URL, '?page=1', POSTS_PER_PAGES),
            (GROUP_POSTS_URL, '?page=1', POSTS_PER_PAGES),
            (PROFILE_URL, '?page=1', POSTS_PER_PAGES),
            (INDEX_URL, '?page=2', self.batch_size - POSTS_PER_PAGES),
            (FOLLOW_URL, '?page=2', self.batch_size - POSTS_PER_PAGES),
            (GROUP_POSTS_URL, '?page=2', self.batch_size - POSTS_PER_PAGES),
            (PROFILE_URL, '?page=2', self.batch_size - POSTS_PER_PAGES),
        )
        for url, page, posts in pages:
            with self.subTest(url=url):
                response = self.user_client.get(url + page)
                self.assertEqual(
                    len(response.context['page_obj']), posts
                )
