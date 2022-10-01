from django.test import TestCase
from django.urls import reverse

from posts.urls import app_name

USERNAME = 'StasBasov'
GROUP_SLUG = 'test-slug'
POST_ID = 1
CASES = (
    ('/', 'index', None),
    ('/create/', 'post_create', None),
    ('/follow/', 'follow_index', None),
    (f'/posts/{POST_ID}/', 'post_detail', (POST_ID,)),
    (f'/profile/{USERNAME}/', 'profile', (USERNAME,)),
    (f'/posts/{POST_ID}/edit/', 'post_edit', (POST_ID,)),
    (f'/group/{GROUP_SLUG}/', 'group_posts', (GROUP_SLUG,)),
    (f'/posts/{POST_ID}/comment/', 'add_comment', (POST_ID,)),
    (f'/profile/{USERNAME}/follow/', 'profile_follow', (USERNAME,)),
    (f'/profile/{USERNAME}/unfollow/', 'profile_unfollow', (USERNAME,)),
)


class PostPagesTests(TestCase):

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, address, args in CASES:
            with self.subTest(url=url):
                self.assertEqual(
                    reverse(f'{app_name}:' + address, args=args), url
                )
