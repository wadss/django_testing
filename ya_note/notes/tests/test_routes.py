from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='note-slug',
            author=cls.author
        )
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

    def test_pages_availability_for_anonymous_user(self):
        """Тест на доступность страниц всем пользователям"""
        urls = (
            ('notes:home'),
            ('users:login'),
            ('users:logout'),
            ('users:signup')

        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_user_availability_pages(self):
        """Тест на доступность страниц авторизованным пользователям"""
        urls = (
            ('notes:list'),
            ('notes:add'),
            ('notes:success')
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.auth_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_different_users(self):
        """
        Тест на доступность страниц для
        авторизованных и анонимных пользователей
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        urls = (
            ('notes:detail'),
            ('notes:edit'),
            ('notes:delete'),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in urls:
                with self.subTest(name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Тест на редирект для анонимных пользователей"""
        login_url = reverse('users:login')
        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
