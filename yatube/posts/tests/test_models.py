from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_has_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        self.assertEqual(
            f'{self.post.text} '
            f'{self.post.author.username} '
            f'{self.post.pub_date} '
            f'{self.post.group} ',
            str(self.post)
        )
        self.assertEqual(self.group.title, str(self.group))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_post_verboses = {
            'text': 'Текст',
            'author': 'Автор',
            'group': 'Группа',
            'pub_date': 'Дата публикации',
        }
        field_group_verboses = {
            'title': 'Заголовок',
            'slug': 'Идентификатор группы',
            'description': 'Описание',
        }
        for field, expected_value in field_post_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).verbose_name, expected_value)
        for field, expected_value in field_group_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Group._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относится пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).help_text, expected_value)
