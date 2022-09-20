from itertools import islice
from django.test import Client, TestCase
from django.urls import reverse

from yatube.settings import POSTS_PER_PAGES

from ..models import Group, Post, User

POSTS_COUNT = 13
USERNAME = 'StasBasov'
GROUP_SLUG = 'test-slug'
INDEX_PAGE = reverse('posts:index')
GROUP_POSTS_PAGE = reverse('posts:group_posts', args=(GROUP_SLUG,))
PROFILE_PAGE = reverse('posts:profile', args=(USERNAME,))
POST_CREATE_PAGE = reverse('posts:post_create')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.batch_size = 13
        objs = (Post(
            group=cls.group,
            author=cls.user,
            text='Тестовый пост %s' % i
        ) for i in range(cls.batch_size))
        while True:
            batch = list(islice(objs, cls.batch_size))
            if not batch:
                break
            Post.objects.bulk_create(batch, cls.batch_size)

    def test_first_index_page_contains_ten_records(self):
        """На первой странице паджинатора index 10 постов."""
        post_count = (
            ('?page=1', POSTS_PER_PAGES),
            ('?page=2', self.batch_size - POSTS_PER_PAGES)
        )
        pages = (
            INDEX_PAGE,
            GROUP_POSTS_PAGE,
            PROFILE_PAGE
        )
        for page in pages:
            with self.subTest(pages=pages):
                for pag, count in post_count:
                    with self.subTest(count=count):
                        response = self.client.get(page + pag)
                        self.assertEqual(
                            len(response.context['page_obj']), count
                        )
