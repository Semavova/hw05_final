from django.test import TestCase
from django.urls import reverse

USERNAME = 'StasBasov'
GROUP_SLUG = 'test-slug'
POST_ID = 1
URL_ADDRESS_LIST = (
    ('/', 'index', None),
    ('/create/', 'post_create', None),
    (f'/posts/{POST_ID}/', 'post_detail', (POST_ID,)),
    (f'/profile/{USERNAME}/', 'profile', (USERNAME,)),
    (f'/posts/{POST_ID}/edit/', 'post_edit', (POST_ID,)),
    (f'/group/{GROUP_SLUG}/', 'group_posts', (GROUP_SLUG,))
)


class PostPagesTests(TestCase):

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, address, args in URL_ADDRESS_LIST:
            with self.subTest(url=url):
                self.assertEqual(reverse('posts:' + address, args=args), url)
