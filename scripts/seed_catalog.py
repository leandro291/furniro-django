"""Carga un catálogo de demo (categorías y productos) a través de la API.

Funciona contra cualquier entorno (local o Render) porque solo usa HTTP: hace falta un
usuario staff. Las imágenes se generan con Pillow y se suben por la propia API, así que
en producción terminan en Cloudinary con las credenciales que ya tiene el backend.

    ./venv/bin/python scripts/seed_catalog.py --base-url https://<backend>.onrender.com \
        --email admin@example.com --password '...'

Es idempotente: los productos con el mismo título no se vuelven a crear.
"""
import argparse
import io
import os
import random
import sys

import requests
from PIL import Image, ImageDraw, ImageFont

# Los 8 modelos por categoría dan 48 productos (el pedido era "al menos 40").
CATALOG = {
    'Sofas': (['Cloud', 'Nordic', 'Milano', 'Oslo', 'Velvet', 'Chesterfield', 'Lounge', 'Modular'], (700, 1800), '#B88E2F'),
    'Chairs': (['Eames', 'Oak', 'Windsor', 'Bistro', 'Lounge', 'Ergo', 'Barstool', 'Rocking'], (60, 260), '#7C8B6F'),
    'Tables': (['Roble', 'Centro', 'Comedor', 'Consola', 'Escritorio', 'Auxiliar', 'Nogal', 'Plegable'], (150, 700), '#8A6F5A'),
    'Beds': (['King', 'Queen', 'Nordic', 'Plataforma', 'Litera', 'Individual', 'Canapé', 'Baúl'], (400, 1200), '#6F7F8B'),
    'Storage': (['Estantería', 'Cómoda', 'Armario', 'Biblioteca', 'Zapatero', 'Aparador', 'Cajonera', 'Vitrina'], (120, 600), '#8B7A6F'),
    'Lighting': (['Lámpara Pie', 'Lámpara Mesa', 'Colgante', 'Aplique', 'Arco', 'Industrial', 'Rattan', 'Globo'], (30, 220), '#C2A23E'),
}
TIMEOUT = 90  # el primer request a Render free puede tardar ~50s en frío
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def placeholder(title, color):
    """JPEG 600x600 con el color de la categoría y el nombre del producto."""
    img = Image.new('RGB', (600, 600), color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT, 44)
    except OSError:
        font = ImageFont.load_default(size=44)
    draw.text((300, 300), title, font=font, fill='white', anchor='mm')
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=85)
    return buf.getvalue()


def fetch_all(session, url):
    """Recorre la paginación y devuelve todos los resultados."""
    results = []
    while url:
        data = session.get(url, timeout=TIMEOUT).json()
        results += data['results']
        url = data['next']
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--base-url', default=os.environ.get('SEED_BASE_URL'), required=not os.environ.get('SEED_BASE_URL'))
    parser.add_argument('--email', default=os.environ.get('SEED_EMAIL'), required=not os.environ.get('SEED_EMAIL'))
    parser.add_argument('--password', default=os.environ.get('SEED_PASSWORD'), required=not os.environ.get('SEED_PASSWORD'))
    args = parser.parse_args()
    base = args.base_url.rstrip('/')

    session = requests.Session()
    login = session.post(f'{base}/api/auth/token/', json={'email': args.email, 'password': args.password}, timeout=TIMEOUT)
    if login.status_code != 200:
        sys.exit(f'Login falló ({login.status_code}): {login.text[:200]}')
    session.headers['Authorization'] = f"Bearer {login.json()['access']}"

    categories = {c['name']: c['id'] for c in fetch_all(session, f'{base}/api/catalog/categories/')}
    existing = {p['title'] for p in fetch_all(session, f'{base}/api/catalog/products/')}
    rng = random.Random(7)  # mismos precios y ratings en cada corrida
    created = skipped = 0

    for name, (models, (low, high), color) in CATALOG.items():
        if name not in categories:
            res = session.post(f'{base}/api/catalog/categories/', json={'name': name}, timeout=TIMEOUT)
            if res.status_code == 403:
                sys.exit(f'{args.email} no es staff: crear categorías y productos requiere is_staff=true.')
            res.raise_for_status()
            categories[name] = res.json()['id']

        for model in models:
            title = f'{name[:-1] if name.endswith("s") else name} {model}'
            price = rng.randrange(low, high, 5)
            rating, count, stock = round(rng.uniform(3.2, 5.0), 2), rng.randint(5, 240), rng.randint(3, 40)
            if title in existing:
                skipped += 1
                continue
            res = session.post(f'{base}/api/catalog/products/', timeout=TIMEOUT, data={
                'title': title,
                'description': f'{model}: diseño moderno, materiales de calidad y envío a todo el país.',
                'price': price, 'category': categories[name],
                'rating_rate': rating, 'rating_count': count, 'stock': stock,
            }, files={'image': (f'{title}.jpg', placeholder(title, color), 'image/jpeg')})
            if res.status_code != 201:
                sys.exit(f'No se pudo crear "{title}" ({res.status_code}): {res.text[:300]}')
            created += 1
            print(f'+ {title}')

    print(f'Listo: {created} creados, {skipped} ya existían.')


if __name__ == '__main__':
    main()
