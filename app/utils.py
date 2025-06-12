from datetime import date, timedelta, datetime
import pytz
from .models import ReadingLog
from sqlalchemy import func
import calendar
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import os

def fetch_book_data(isbn):
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    response = requests.get(url)
    data = response.json()
    book_key = f"ISBN:{isbn}"
    if book_key in data:
        book = data[book_key]
        title = book.get('title', '')
        authors = ', '.join([a['name'] for a in book.get('authors', [])])
        cover = book.get('cover', {}).get('large') or book.get('cover', {}).get('medium') or book.get('cover', {}).get('small')
        return {
            'title': title,
            'author': authors,
            'cover': cover
        }
    return None

def get_google_books_cover(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        items = data.get("items")
        if items:
            image_links = items[0]["volumeInfo"].get("imageLinks", {})
            # Prefer medium/thumbnail, fallback to smallThumbnail
            return image_links.get("thumbnail") or image_links.get("smallThumbnail")
    except Exception:
        pass
    return None

def format_date(date):
    return date.strftime("%Y-%m-%d") if date else None

def get_reading_streak(timezone):
    # Get all unique dates with a reading log, sorted descending
    dates = (
        ReadingLog.query.with_entities(ReadingLog.date)
        .distinct()
        .order_by(ReadingLog.date.desc())
        .all()
    )
    dates = [d[0] for d in dates]
    if not dates:
        return 0

    # Use Central America time for "today"
    now_ca = datetime.now(timezone)
    today = now_ca.date()

    streak = 0
    for i, d in enumerate(dates):
        expected = today - timedelta(days=i)
        if d == expected:
            streak += 1
        else:
            break
    current_streak = streak
    return current_streak

def generate_month_review_image(books, month, year):
    import calendar
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO
    import requests
    import os

    img_size = 1080
    cols = 4
    cover_w, cover_h = 200, 300
    padding = 30
    # Increase title_height to give more space for the text
    title_height = 220
    grid_w = cols * cover_w + (cols - 1) * padding
    rows = ((len(books) - 1) // cols) + 1 if books else 1
    grid_h = rows * cover_h + (rows - 1) * padding
    # Move grid lower to avoid overlap
    grid_top = title_height + 40
    grid_left = (img_size - grid_w) // 2

    # Try bookshelf background
    bg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'bookshelf.png'))
    print("Looking for bookshelf background at:", bg_path)
    try:
        bg = Image.open(bg_path).convert('RGBA').resize((img_size, img_size))
        print("Bookshelf background loaded!")
    except Exception as e:
        print("Failed to load bookshelf background:", e)
        bg = Image.new('RGBA', (img_size, img_size), (255, 230, 200, 255))

    draw = ImageDraw.Draw(bg)

    # Draw month title in white
    month_name = f"{calendar.month_name[month].upper()} {year}"
    max_width = img_size - 80  # 40px margin on each side
    font_size = 220
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not os.path.exists(font_path):
        font_path = os.path.join(os.path.dirname(__file__), "static", "Arial.ttf")
    while font_size > 10:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            print("Font load failed:", e)
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), month_name, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if w <= max_width:
            break
        font_size -= 10
    shadow_offset = 4
    # Draw shadow for readability
    draw.text(((img_size - w) // 2 + shadow_offset, 40 + shadow_offset), month_name, fill=(0,0,0,128), font=font)
    # Draw main text in white
    draw.text(((img_size - w) // 2, 40), month_name, fill=(255, 255, 255), font=font)

    # Place covers
    for idx, book in enumerate(books):
        row = idx // cols
        col = idx % cols
        x = grid_left + col * (cover_w + padding)
        y = grid_top + row * (cover_h + padding)
        cover_url = getattr(book, 'cover_url', None)
        try:
            if cover_url:
                r = requests.get(cover_url, timeout=10)
                cover = Image.open(BytesIO(r.content)).convert("RGBA")
                cover = cover.resize((cover_w, cover_h))
            else:
                raise Exception("No cover")
        except Exception:
            cover = Image.new('RGBA', (cover_w, cover_h), (220, 220, 220, 255))
        bg.paste(cover, (x, y), cover if cover.mode == 'RGBA' else None)

    return bg.convert('RGB')