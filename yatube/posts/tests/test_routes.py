from django.test import TestCase
from django.urls import reverse

USERNAME = 'StasBasov'
GROUP_SLUG = 'test-slug'
POST_ID = 1
ROUTE_ADDRESS_LIST = (
    ('/', reverse('posts:index')),
    ('/create/', reverse('posts:post_create')),
    (f'/posts/{POST_ID}/', reverse('posts:post_detail', args=(POST_ID,))),
    (f'/profile/{USERNAME}/', reverse('posts:profile', args=(USERNAME,))),
    (f'/posts/{POST_ID}/edit/', reverse('posts:post_edit', args=(POST_ID,))),
    (f'/group/{GROUP_SLUG}/', reverse('posts:group_posts', args=(GROUP_SLUG,)))
)


class PostPagesTests(TestCase):

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for route, address in ROUTE_ADDRESS_LIST:
            with self.subTest(address=address):
                self.assertEqual(address, route)
