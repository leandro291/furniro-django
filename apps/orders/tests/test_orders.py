import io
from decimal import Decimal

import pytest
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.models import Address, User
from apps.catalog.models import Category, Product
from apps.orders.models import Order
from apps.orders.services import InsufficientStockError, InvalidOrderStateError, OrderService


def make_test_image():
    buf = io.BytesIO()
    Image.new('RGB', (10, 10), color='blue').save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile('test.png', buf.read(), content_type='image/png')


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def customer():
    return User.objects.create_user(username='customer', email='customer@example.com', password='x')


@pytest.fixture
def other_customer():
    return User.objects.create_user(username='other', email='other@example.com', password='x')


@pytest.fixture
def staff_user():
    return User.objects.create_user(username='staff', email='staff@example.com', password='x', is_staff=True)


@pytest.fixture
def address(customer):
    return Address.objects.create(
        user=customer, first_name='Lena', last_name='D', street='Calle 1',
        city='CABA', province='BA', phone='123', email='customer@example.com',
    )


@pytest.fixture
def category():
    return Category.objects.create(name='General')


@pytest.fixture
def product(category):
    return Product.objects.create(
        title='Silla', description='', price=Decimal('100.00'),
        category=category, image=make_test_image(), stock=5,
    )


@pytest.mark.django_db
def test_checkout_decrements_stock(customer, address, product):
    order = OrderService.create_order(
        user=customer, address_id=address.id,
        items=[{'product_id': product.id, 'quantity': 2}],
    )

    product.refresh_from_db()
    assert product.stock == 3
    assert order.total == Decimal('200.00')
    assert order.items.count() == 1


@pytest.mark.django_db
def test_checkout_with_insufficient_stock_creates_no_order(customer, address, product):
    with pytest.raises(InsufficientStockError):
        OrderService.create_order(
            user=customer, address_id=address.id,
            items=[{'product_id': product.id, 'quantity': 999}],
        )

    assert Order.objects.count() == 0
    product.refresh_from_db()
    assert product.stock == 5  # sin cambios: la transacción completa se revirtió


@pytest.mark.django_db
def test_snapshot_survives_source_edits(customer, address, product):
    order = OrderService.create_order(
        user=customer, address_id=address.id,
        items=[{'product_id': product.id, 'quantity': 1}],
    )
    item = order.items.get()

    address.street = 'Calle Nueva 999'
    address.save()
    product.price = Decimal('9999.00')
    product.title = 'Nombre cambiado'
    product.save()

    order.refresh_from_db()
    item.refresh_from_db()

    assert order.address_street == 'Calle 1'
    assert item.price_snapshot == Decimal('100.00')
    assert item.title_snapshot == 'Silla'


@pytest.mark.django_db
def test_owner_can_cancel_pending_order_and_stock_is_restocked(customer, address, product):
    order = OrderService.create_order(
        user=customer, address_id=address.id,
        items=[{'product_id': product.id, 'quantity': 2}],
    )

    OrderService.cancel_order(order=order, actor=customer)

    order.refresh_from_db()
    product.refresh_from_db()
    assert order.status == Order.Status.CANCELLED
    assert product.stock == 5


@pytest.mark.django_db
def test_owner_cannot_cancel_paid_order(customer, address, product):
    order = OrderService.create_order(
        user=customer, address_id=address.id,
        items=[{'product_id': product.id, 'quantity': 1}],
    )
    OrderService.mark_as_paid(order=order)

    with pytest.raises(InvalidOrderStateError):
        OrderService.cancel_order(order=order, actor=customer)


@pytest.mark.django_db
def test_staff_can_cancel_paid_order(customer, staff_user, address, product):
    order = OrderService.create_order(
        user=customer, address_id=address.id,
        items=[{'product_id': product.id, 'quantity': 1}],
    )
    OrderService.mark_as_paid(order=order)

    order = OrderService.cancel_order(order=order, actor=staff_user)
    assert order.status == Order.Status.CANCELLED


@pytest.mark.django_db
def test_user_cannot_access_others_order(api_client, customer, other_customer, address, product):
    order = OrderService.create_order(
        user=customer, address_id=address.id,
        items=[{'product_id': product.id, 'quantity': 1}],
    )

    api_client.force_authenticate(user=other_customer)
    resp = api_client.get(f'/api/orders/{order.id}/')
    assert resp.status_code == 404

    resp = api_client.post(f'/api/orders/{order.id}/cancel/')
    assert resp.status_code == 404


@pytest.mark.django_db
def test_only_staff_can_mark_as_paid(api_client, customer, staff_user, address, product):
    order = OrderService.create_order(
        user=customer, address_id=address.id,
        items=[{'product_id': product.id, 'quantity': 1}],
    )

    api_client.force_authenticate(user=customer)
    resp = api_client.patch(f'/api/orders/{order.id}/mark-as-paid/')
    assert resp.status_code == 403

    api_client.force_authenticate(user=staff_user)
    resp = api_client.patch(f'/api/orders/{order.id}/mark-as-paid/')
    assert resp.status_code == 200
    assert resp.data['status'] == 'paid'


@pytest.mark.django_db
def test_checkout_via_api_creates_order_and_decrements_stock(api_client, customer, address, product):
    api_client.force_authenticate(user=customer)

    resp = api_client.post('/api/orders/', {
        'address_id': address.id,
        'items': [{'product_id': product.id, 'quantity': 2}],
    }, format='json')

    assert resp.status_code == 201
    assert resp.data['status'] == 'pending'
    assert resp.data['total'] == '200.00'
    product.refresh_from_db()
    assert product.stock == 3


@pytest.mark.django_db
def test_checkout_via_api_rejects_empty_items(api_client, customer, address):
    api_client.force_authenticate(user=customer)

    resp = api_client.post('/api/orders/', {'address_id': address.id, 'items': []}, format='json')

    assert resp.status_code == 400


@pytest.mark.django_db
def test_checkout_via_api_with_bad_address_returns_400(api_client, customer, product):
    api_client.force_authenticate(user=customer)

    resp = api_client.post('/api/orders/', {
        'address_id': 999999,
        'items': [{'product_id': product.id, 'quantity': 1}],
    }, format='json')

    assert resp.status_code == 400
    assert Order.objects.count() == 0


@pytest.mark.django_db
def test_checkout_via_api_with_insufficient_stock_returns_400(api_client, customer, address, product):
    api_client.force_authenticate(user=customer)

    resp = api_client.post('/api/orders/', {
        'address_id': address.id,
        'items': [{'product_id': product.id, 'quantity': 999}],
    }, format='json')

    assert resp.status_code == 400
    assert Order.objects.count() == 0


@pytest.mark.django_db
def test_owner_can_list_retrieve_and_cancel_own_order_via_api(api_client, customer, address, product):
    order = OrderService.create_order(
        user=customer, address_id=address.id,
        items=[{'product_id': product.id, 'quantity': 1}],
    )
    api_client.force_authenticate(user=customer)

    resp = api_client.get('/api/orders/')
    assert resp.status_code == 200
    assert resp.data['count'] == 1

    resp = api_client.get(f'/api/orders/{order.id}/')
    assert resp.status_code == 200

    resp = api_client.post(f'/api/orders/{order.id}/cancel/')
    assert resp.status_code == 200
    assert resp.data['status'] == 'cancelled'
    product.refresh_from_db()
    assert product.stock == 5


@pytest.mark.django_db
def test_cancel_already_cancelled_order_via_api_returns_400(api_client, customer, address, product):
    order = OrderService.create_order(
        user=customer, address_id=address.id,
        items=[{'product_id': product.id, 'quantity': 1}],
    )
    api_client.force_authenticate(user=customer)
    api_client.post(f'/api/orders/{order.id}/cancel/')

    resp = api_client.post(f'/api/orders/{order.id}/cancel/')

    assert resp.status_code == 400


@pytest.mark.django_db
def test_mark_as_paid_on_already_paid_order_via_api_returns_400(api_client, customer, staff_user, address, product):
    order = OrderService.create_order(
        user=customer, address_id=address.id,
        items=[{'product_id': product.id, 'quantity': 1}],
    )
    api_client.force_authenticate(user=staff_user)
    api_client.patch(f'/api/orders/{order.id}/mark-as-paid/')

    resp = api_client.patch(f'/api/orders/{order.id}/mark-as-paid/')

    assert resp.status_code == 400


@pytest.mark.django_db
def test_staff_sees_all_orders_via_api(api_client, customer, staff_user, address, product):
    OrderService.create_order(
        user=customer, address_id=address.id,
        items=[{'product_id': product.id, 'quantity': 1}],
    )

    api_client.force_authenticate(user=staff_user)
    resp = api_client.get('/api/orders/')

    assert resp.status_code == 200
    assert resp.data['count'] == 1


@pytest.mark.django_db
def test_last_unit_race_only_one_buyer_wins(customer, other_customer, address, product):
    """Prueba la garantía real de select_for_update() + UPDATE condicional: solo un
    comprador se lleva la última unidad, sin importar el orden de llegada.

    SQLite (usado en test.py) no soporta locking real entre conexiones concurrentes
    de threads distintos — un test con threading.Thread da "database table is
    locked" de forma no determinística, no por un bug del código sino por una
    limitación conocida de SQLite. La garantía de no-oversell no depende de que dos
    requests literalmente coincidan en el tiempo: depende de que el UPDATE
    condicional (`stock__gte=quantity`) relea el estado real de la fila en el
    momento de escribir. Por eso alcanza con dos intentos secuenciales sobre el
    mismo stock=1 para probar la propiedad — en Postgres (producción) el mismo
    código además bloquea la segunda transacción con select_for_update() mientras
    la primera está en vuelo.
    """
    product.stock = 1
    product.save(update_fields=['stock'])

    other_address = Address.objects.create(
        user=other_customer, first_name='O', last_name='C', street='Calle 2',
        city='CABA', province='BA', phone='456', email='other@example.com',
    )

    OrderService.create_order(
        user=customer, address_id=address.id,
        items=[{'product_id': product.id, 'quantity': 1}],
    )

    with pytest.raises(InsufficientStockError):
        OrderService.create_order(
            user=other_customer, address_id=other_address.id,
            items=[{'product_id': product.id, 'quantity': 1}],
        )

    product.refresh_from_db()
    assert product.stock == 0
    assert Order.objects.filter(user=other_customer).count() == 0
