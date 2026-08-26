import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Address, User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_register_creates_user_with_email_login(api_client):
    resp = api_client.post('/api/accounts/register/', {
        'username': 'lena',
        'email': 'lena@example.com',
        'password': 'a-strong-password-123',
    })
    assert resp.status_code == 201
    user = User.objects.get(email='lena@example.com')
    assert user.check_password('a-strong-password-123')
    assert user.is_staff is False


@pytest.mark.django_db
def test_register_rejects_duplicate_email(api_client):
    User.objects.create_user(username='u1', email='dup@example.com', password='x')
    resp = api_client.post('/api/accounts/register/', {
        'username': 'u2',
        'email': 'dup@example.com',
        'password': 'a-strong-password-123',
    })
    assert resp.status_code == 400


@pytest.mark.django_db
def test_user_cannot_see_another_users_address(api_client):
    owner = User.objects.create_user(username='owner', email='owner@example.com', password='x')
    other = User.objects.create_user(username='other', email='other@example.com', password='x')
    address = Address.objects.create(
        user=owner, first_name='A', last_name='B', street='Main 1',
        city='CABA', province='BA', phone='123', email='owner@example.com',
    )

    api_client.force_authenticate(user=other)
    resp = api_client.get('/api/accounts/addresses/')
    assert resp.status_code == 200
    assert resp.data['count'] == 0

    resp = api_client.get(f'/api/accounts/addresses/{address.id}/')
    assert resp.status_code == 404
