import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(username='lena', email='lena@example.com', password='a-strong-password-123')


@pytest.mark.django_db
def test_login_returns_access_and_refresh_tokens(api_client, user):
    resp = api_client.post('/api/auth/token/', {
        'email': 'lena@example.com',
        'password': 'a-strong-password-123',
    })

    assert resp.status_code == 200
    assert 'access' in resp.data
    assert 'refresh' in resp.data


@pytest.mark.django_db
def test_blacklisted_refresh_token_cannot_be_reused(api_client, user):
    tokens = api_client.post('/api/auth/token/', {
        'email': 'lena@example.com',
        'password': 'a-strong-password-123',
    }).data

    resp = api_client.post('/api/auth/logout/', {'refresh': tokens['refresh']})
    assert resp.status_code == 200

    resp = api_client.post('/api/auth/token/refresh/', {'refresh': tokens['refresh']})
    assert resp.status_code == 401
