# Furniro E-commerce Backend

API REST para el backend de un e-commerce de muebles, construida con Django y Django REST Framework. Maneja identidad de usuarios, catálogo de productos, ciclo de vida de pedidos con control de stock concurrente, y contenido editorial (blog).

## Stack

- **Django 6.1** + **Django REST Framework**
- **Autenticación**: JWT vía `djangorestframework-simplejwt` (login, refresh y logout con blacklist)
- **Base de datos**: PostgreSQL en producción, SQLite en desarrollo/tests
- **Media**: Cloudinary (imágenes de productos y posts)
- **Documentación de API**: `drf-spectacular` (OpenAPI, Swagger, Redoc)
- **Static files en producción**: WhiteNoise
- **Servidor de producción**: Gunicorn

## Arquitectura

El proyecto tiene 4 apps bajo `apps/`, cada una dueña de un único dominio. No hay una app `core`/`common` compartida a propósito — si en algún momento aparece código realmente compartido entre apps, se extrae recién en ese momento.

| App | Dominio | Modelos |
|---|---|---|
| `apps.accounts` | Identidad | `User` (login por `email`, no `username`), `Address` |
| `apps.catalog` | Catálogo público | `Category`, `Product` |
| `apps.orders` | Ciclo de vida del pedido | `Order`, `OrderItem` |
| `apps.blog` | Contenido editorial | `Post`, `PostCategory` |

### Regla de capas

Cada app sigue el flujo `models.py` → `serializers.py` → `services.py` (solo donde aplica) → `views.py` → `urls.py`, más su propio `permissions.py` (sin imports cruzados entre apps). Si una operación toca 2+ modelos o necesita ser transaccional, va en `services.py`; si toca 1 modelo y es solo forma/validación de campo, va en el serializer o el modelo. Las vistas solo orquestan HTTP, nunca contienen lógica de negocio.

El único servicio hoy es `apps/orders/services.py::OrderService`, punto único de mutación de `Order`/`OrderItem`/`Product.stock`. El descuento de stock combina `select_for_update()` con un `UPDATE` condicional atómico (`Product.objects.filter(id=x, stock__gte=n).update(...)`) para evitar oversell incluso en SQLite, donde el locking de fila no alcanza solo.

### Snapshots en pedidos

`Order` y `OrderItem` copian los datos de `Address`/`Product` en el momento de la compra (dirección, título, precio) en vez de referenciarlos por FK — así un pedido histórico no cambia si el usuario edita su dirección o el producto sube de precio después.

## Instalación y desarrollo local

```bash
git clone <url-del-repo>
cd furniro-ecommerce-backend
python -m venv venv
source venv/bin/activate

pip install -r requirements-dev.txt   # runtime + testing/lint

cp .env.example .env                  # completar con tus valores locales
python manage.py migrate
python manage.py runserver
```

Con `DEBUG=True` (settings de desarrollo), la base de datos es SQLite local y no hace falta Postgres para levantar el proyecto.

## Variables de entorno

Se cargan desde un archivo `.env` en la raíz (vía `python-dotenv`) **solo para desarrollo local** — nunca se commitea, está en `.gitignore`. En producción no existe archivo `.env`: las variables se cargan directo como variables de entorno reales en la plataforma de hosting (ver [Despliegue](#despliegue)).

| Variable | Qué hace | Obligatoria en producción |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | Qué archivo de settings usar (`...settings.development` / `.production` / `.test`). **Solo tiene efecto si se exporta como variable de entorno real antes de arrancar el proceso** (shell o plataforma) — el valor dentro de `.env` no lo controla, porque se lee después de que Django ya eligió el settings module. | Sí (la setea la plataforma) |
| `DJANGO_SECRET_KEY` | Firma sesiones, cookies y tokens JWT (simplejwt usa `SECRET_KEY` como `SIGNING_KEY` por default). Generar con `python -c "import secrets; print(secrets.token_urlsafe(50))"`. | Sí |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, **sin** esquema (`https://`) ni barra final — solo el hostname, separados por coma. | Sí |
| `DATABASE_URL` | Conexión a Postgres (`postgres://user:pass@host:5432/db`). Solo se usa en producción; desarrollo usa SQLite. | Sí |
| `CORS_ALLOWED_ORIGINS` | Orígenes del frontend que pueden pegarle a la API, **con** esquema y **sin** barra final (debe matchear el header `Origin` exacto). | Sí |
| `CSRF_TRUSTED_ORIGINS` | Dominios con esquema completo, necesarios para que `/admin/` funcione detrás de un proxy TLS (Railway/Render). La API vía JWT no lo necesita. | Recomendada |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` / `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Duración de los tokens JWT. Tienen default (30 / 7) si no se setean. | No |
| `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET` | Credenciales de Cloudinary para subir imágenes de productos y posts. | Sí |

## Endpoints principales

Todos los endpoints de API (salvo auth y docs) están montados bajo `/api/<app>/`.

| Método/path | Descripción | Permiso |
|---|---|---|
| `POST /api/auth/token/` | Login (obtiene access + refresh token) | Público, throttled 5/min |
| `POST /api/auth/token/refresh/` | Renueva el access token | Público |
| `POST /api/auth/logout/` | Blacklistea el refresh token | Autenticado |
| `POST /api/accounts/register/` | Registro de usuario | Público |
| `/api/accounts/addresses/` | CRUD de direcciones | Dueño |
| `/api/catalog/categories/` | CRUD de categorías | Lectura pública, escritura `is_staff` |
| `/api/catalog/products/` | CRUD de productos | Lectura pública, escritura `is_staff` |
| `/api/orders/` | CRUD de pedidos | Dueño o staff |
| `/api/blog/categories/` | CRUD de categorías de blog | Lectura pública, escritura staff |
| `/api/blog/posts/` | CRUD de posts | Lectura pública, escritura staff |
| `/api/schema/` | Schema OpenAPI | — |
| `/api/docs/` | Swagger UI | — |
| `/api/redoc/` | Redoc | — |
| `/admin/` | Django admin | Staff |

## Testing

```bash
pytest                                          # todo el suite
pytest apps/orders/                             # solo una app
pytest apps/orders/tests/test_orders.py::test_checkout_decrements_stock  # un test puntual
pytest --cov=apps --cov-report=term-missing     # con cobertura
```

`pytest.ini` fija `DJANGO_SETTINGS_MODULE=furniro_ecommerce.settings.test` y `--reuse-db`, así que no hace falta exportar nada a mano para correr tests.

## Lint y seguridad

```bash
ruff check .
black .
isort .

pip-audit
bandit -r apps furniro_ecommerce manage.py -x '*/tests/*,*/migrations/*'
DJANGO_SETTINGS_MODULE=furniro_ecommerce.settings.production python manage.py check --deploy
```

## Despliegue

Pensado para PaaS tipo Railway/Render (detectan `requirements.txt` + `Procfile` solos, sin necesidad de Docker/CI):

- **Railway**: usa `Procfile` tal cual — fase `release` corre `migrate` + `collectstatic`; fase `web` levanta `gunicorn`.
- **Render**: no tiene fase `release`, así que hay que configurar a mano:
  - **Build Command**: `./build.sh` (instala dependencias, corre `collectstatic` y `migrate`).
  - **Start Command**: `gunicorn furniro_ecommerce.wsgi:application --bind 0.0.0.0:$PORT` (la línea `web` del `Procfile`).
- **Static files**: servidos por WhiteNoise (no hay CDN delante en estas plataformas); media sigue yendo a Cloudinary.
- **Variables de entorno**: se cargan en el dashboard de la plataforma, no en ningún archivo — ver la tabla de arriba. En particular, `DJANGO_SETTINGS_MODULE=furniro_ecommerce.settings.production` tiene que estar seteada ahí para que la app arranque con la configuración correcta.
- **Base de datos**: se linkea el addon de Postgres de la plataforma, que inyecta `DATABASE_URL` automáticamente.

Antes de cada deploy, correr el checklist de [Lint y seguridad](#lint-y-seguridad) completo.
