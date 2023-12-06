from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.form_data = {'title': 'Новый аголовок',
                         'text': 'Текст новыой заметки',
                         'slug': 'note-slug-new'}
        cls.notes_add = 'notes:add'

    def test_user_can_create_note(self):
        """Тест что пользователь может создать заметку"""
        Note.objects.all().delete()
        url = reverse(self.notes_add)
        response = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.last()
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Тест что анонимный пользователь не может создать заметку"""
        all_notes = Note.objects.count()
        url = reverse(self.notes_add)
        response = self.client.post(url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), all_notes)

    def test_empty_slug(self):
        """Тест на отсутствие пустого слага"""
        Note.objects.all().delete()
        url = reverse(self.notes_add)
        self.form_data.pop('slug')
        response = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        assert Note.objects.count() == 1
        new_note = Note.objects.last()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDeleteAndSlug(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Мимо Крокодил')
        cls.auth_reader = Client()
        cls.auth_reader.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='note-slug',
            author=cls.author
        )
        cls.form_data = {'title': 'Новый аголовок',
                         'text': 'Текст новыой заметки',
                         'slug': 'note-slug-new'}

    def test_not_unique_slug(self):
        """Тест на отсутствие двух заметок с одинаковым слагом"""
        all_notes = Note.objects.count()
        url = reverse('notes:add')
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(url, data=self.form_data)
        self.assertFormError(response,
                             'form',
                             'slug',
                             errors=(self.note.slug + WARNING))
        self.assertEqual(Note.objects.count(), all_notes)

    def test_author_can_edit_note(self):
        """Тест на возможность автора изменять заметку"""
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_client.post(url, self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        """Тест на возможность изменять чужую заметку другим пользователем"""
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.auth_reader.post(url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        """Тест на возможность удаление заметки автором"""
        all_notes = Note.objects.count()
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertLess(Note.objects.count(), all_notes)

    def test_other_user_cant_delete_note(self):
        """Тест на возможность удаления чужой заметки другим пользователем"""
        all_notes = Note.objects.count()
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.auth_reader.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), all_notes)
