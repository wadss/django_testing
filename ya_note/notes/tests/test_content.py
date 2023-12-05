from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestHomePage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Мимо Крокодил')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='note-slug',
            author=cls.author
        )
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        cls.auth_reader = Client()
        cls.auth_reader.force_login(cls.reader)

    def test_pages_contains_form(self):
        """Тест на проверку наличия формы для создания заметки"""
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.auth_client.get(url)
                self.assertIn('form', response.context)

    def test_note_in_list_for_author(self):
        """Тест на проверку наличия заметки для автора"""
        url = reverse('notes:list')
        response = self.auth_client.get(url)
        object_list = response.context.get('object_list', [])
        self.assertIn(self.note, object_list)

    def test_note_not_in_list_for_another_user(self):
        """
        Тест на проверку отсутствие
        заметки автора для другого пользователя
        """
        url = reverse('notes:list')
        response = self.auth_reader.get(url)
        object_list = response.context.get('object_list', [])
        self.assertNotIn(self.note, object_list)
