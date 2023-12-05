from http import HTTPStatus

import pytest
from news.forms import BAD_WORDS, WARNING
from news.models import Comment
from pytest_django.asserts import assertFormError, assertRedirects


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, form_data, detail_url):
    """Тест на проверку, что анононимный не может создать комментарий"""
    client.post(detail_url, data=form_data)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_can_create_comment(
    author_client, detail_url, form_data, news, author
):
    """
    Тест на возможность авторизованного
    пользователя создавать комментарии
    """
    response = author_client.post(detail_url, data=form_data)
    assertRedirects(response, f'{detail_url}#comments')
    comments_count = Comment.objects.count()
    assert comments_count == 1
    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_user_cant_use_bad_words(author_client, detail_url, comment):
    """Тест на проверку плохих слов в тексте комментария"""
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(detail_url, data=bad_words_data)
    assertFormError(response,
                    form='form',
                    field='text',
                    errors=WARNING)
    comments_count = Comment.objects.count()
    assert comments_count == 1


@pytest.mark.django_db
def test_author_can_delete_comment(
    delete_url, author_client, url_to_comments, comment
):
    """Тест на проверку возможности удаления комментария автором"""
    response = author_client.delete(delete_url)
    assertRedirects(response, url_to_comments)
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(
    admin_client, delete_url, comment
):
    """
    Тест на проверку, что другой пользователь
    не может удалить комментарии автора
    """
    response = admin_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1


@pytest.mark.django_db
def test_author_can_edit_comment(
    author_client, edit_url, form_data, comment, url_to_comments
):
    """Тест на проверку возможности автора изменять комментарий"""
    response = author_client.post(edit_url, data=form_data)
    assertRedirects(response, url_to_comments)
    comment.refresh_from_db()
    assert comment.text == form_data['text']


@pytest.mark.django_db
def test_user_cant_edit_comment_of_another_user(
    admin_client, edit_url, form_data, comment
):
    """
    Тест на проверку, что другой пользователь
    не отредактировать комментарий автора
    """
    comment_text = comment.text
    response = admin_client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == comment_text
