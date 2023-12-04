from django.urls import reverse

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()


class TestHomePage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='note-slug',
            author=cls.author
            )
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)

    def test_pages_contains_form(self):
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        )
        for name, args in urls:
            if args is None:
                with self.subTest(name=name):
                    url = reverse(name)
                    response = self.auth_client.get(url)
                    self.assertIn('form', response.context)
            else:
                with self.subTest(name=name):
                    url = reverse(name, args=args)
                    response = self.auth_client.get(url)
                    self.assertIn('form', response.context)
