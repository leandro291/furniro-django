import io

import pytest
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.blog.models import Post, PostCategory


def make_test_image():
    buf = io.BytesIO()
    Image.new('RGB', (10, 10), color='green').save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile('test.png', buf.read(), content_type='image/png')


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def staff_user():
    return User.objects.create_user(username='staff', email='staff@example.com', password='x', is_staff=True)


@pytest.fixture
def other_staff():
    return User.objects.create_user(username='staff2', email='staff2@example.com', password='x', is_staff=True)


@pytest.fixture
def customer():
    return User.objects.create_user(username='customer', email='customer@example.com', password='x')


@pytest.fixture
def category():
    return PostCategory.objects.create(title='Novedades')


@pytest.mark.django_db
def test_public_can_list_posts_without_auth(api_client, staff_user, category):
    Post.objects.create(title='Post 1', category=category, author=staff_user, image=make_test_image())

    resp = api_client.get('/api/blog/posts/')

    assert resp.status_code == 200
    assert resp.data['count'] == 1


@pytest.mark.django_db
def test_only_staff_can_create_post(api_client, customer, staff_user, category):
    payload = {'title': 'Nuevo post', 'category': category.id, 'image': make_test_image()}

    resp = api_client.post('/api/blog/posts/', payload, format='multipart')
    assert resp.status_code == 401  # anónimo

    api_client.force_authenticate(user=customer)
    resp = api_client.post('/api/blog/posts/', {**payload, 'image': make_test_image()}, format='multipart')
    assert resp.status_code == 403  # autenticado pero no staff

    api_client.force_authenticate(user=staff_user)
    resp = api_client.post('/api/blog/posts/', {**payload, 'image': make_test_image()}, format='multipart')
    assert resp.status_code == 201


@pytest.mark.django_db
def test_author_is_forced_to_request_user_not_spoofable(api_client, staff_user, other_staff, category):
    api_client.force_authenticate(user=staff_user)

    resp = api_client.post('/api/blog/posts/', {
        'title': 'Post suplantado', 'category': category.id,
        'author': other_staff.id, 'image': make_test_image(),
    }, format='multipart')

    assert resp.status_code == 201
    post = Post.objects.get(id=resp.data['id'])
    assert post.author_id == staff_user.id  # no other_staff.id
