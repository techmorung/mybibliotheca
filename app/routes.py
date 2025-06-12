from flask import Blueprint, current_app, render_template, request, redirect, url_for, jsonify, flash, send_file
from .models import Book, db, ReadingLog
from .utils import fetch_book_data, get_reading_streak, get_google_books_cover, generate_month_review_image
from datetime import datetime, date
import secrets
import requests
from io import BytesIO
import pytz
import csv

app = Blueprint('app', __name__)
bp = Blueprint('main', __name__)

@app.route('/log_book', methods=['POST'])
def log_book():
    data = request.json
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    start_date = datetime.now().strftime('%Y-%m-%d')
    
    book = Book(title=title, author=author, isbn=isbn, start_date=start_date)
    book.save()  # Assuming save method is defined in the Book model
    
    return jsonify({'message': 'Book logged successfully', 'book': book.to_dict()}), 201

@app.route('/reading_history', methods=['GET'])
def reading_history():
    books = Book.query.all()  # Assuming query method is defined in the Book model
    for book in books:
        if not book.uid:
            # Generate a uid if missing
            book.uid = secrets.token_urlsafe(6)
            db.session.commit()
    return jsonify([book.to_dict() for book in books]), 200

@app.route('/fetch_book/<isbn>', methods=['GET'])
def fetch_book(isbn):
    book_data = fetch_book_data(isbn) or {}
    google_cover = get_google_books_cover(isbn)
    if google_cover:
        book_data['cover'] = google_cover
    # If neither source provides a cover, set a default
    if not book_data.get('cover'):
        book_data['cover'] = url_for('static', filename='bookshelf.png')
    return jsonify(book_data), 200 if book_data else 404

@bp.route('/')
def index():
    books = Book.get_all_books()
    streak = get_reading_streak()
    for book in books:
        if not book.uid:
            book.uid = secrets.token_urlsafe(6)
            db.session.commit()
    want_to_read = [b for b in books if getattr(b, 'want_to_read', False)]
    # Exclude library_only books from currently_reading
    currently_reading = [
        b for b in books
        if not b.finish_date and not getattr(b, 'want_to_read', False) and not getattr(b, 'library_only', False)
    ]
    finished = sorted(
        [b for b in books if b.finish_date],
        key=lambda b: b.finish_date or '',
        reverse=True
    )
    return render_template(
        'index.html',
        currently_reading=currently_reading,
        finished=finished,
        want_to_read=want_to_read,
        streak=streak
    )

@bp.route('/add', methods=['GET', 'POST'])
def add_book():
    book_data = None
    if request.method == 'POST':
        if 'fetch' in request.form:
            # Only fetch book data, do not add book
            isbn = request.form['isbn']
            book_data = fetch_book_data(isbn)
            # Overwrite cover with Google Books
            google_cover = get_google_books_cover(isbn)
            if book_data:
                book_data['cover'] = google_cover
            else:
                book_data = {'cover': google_cover}
            # Re-render the form with fetched data
            return render_template('add_book.html', book_data=book_data)
        elif 'add' in request.form:
            # Actually add the book
            isbn = request.form['isbn']
            # Check for duplicate ISBN
            if Book.query.filter_by(isbn=isbn).first():
                flash('A book with this ISBN already exists.', 'danger')
                return render_template('add_book.html', book_data=None)
            title = request.form['title']
            author = request.form['author']
            start_date_str = request.form.get('start_date') or None
            finish_date_str = request.form.get('finish_date') or None
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
            finish_date = datetime.strptime(finish_date_str, '%Y-%m-%d').date() if finish_date_str else None
            want_to_read = 'want_to_read' in request.form
            library_only = 'library_only' in request.form

            cover_url = get_google_books_cover(isbn)

            if not cover_url:
                flash('Warning: No cover image found on Google Books for this ISBN. A default image will be used. A manual cover URL can be added in the "edit book" section.', 'warning')

            book = Book(
                title=title,
                author=author,
                isbn=isbn,
                start_date=start_date,
                finish_date=finish_date,
                cover_url=cover_url,
                want_to_read=want_to_read,
                library_only=library_only
            )
            book.save()
            return redirect(url_for('main.index'))

    return render_template('add_book.html', book_data=book_data)

@bp.route('/book/<uid>', methods=['GET', 'POST'])
def view_book(uid):
    book = Book.query.filter_by(uid=uid).first_or_404()
    cover_url = book.cover_url  # Use the saved cover_url
    if request.method == 'POST':
        # Update start/finish dates
        start_date_str = request.form.get('start_date')
        finish_date_str = request.form.get('finish_date')
        book.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        book.finish_date = datetime.strptime(finish_date_str, '%Y-%m-%d').date() if finish_date_str else None
        db.session.commit()
        flash('Book dates updated.')
        return redirect(url_for('main.view_book', uid=book.uid))
    return render_template('view_book.html', book=book, cover_url=cover_url)

@bp.route('/book/<uid>/log', methods=['POST'])
def log_reading(uid):
    book = Book.query.filter_by(uid=uid).first_or_404()
    log_date_str = request.form.get('log_date')
    log_date = datetime.strptime(log_date_str, '%Y-%m-%d').date() if log_date_str else date.today()
    existing_log = ReadingLog.query.filter_by(book_id=book.id, date=log_date).first()
    if existing_log:
        flash('You have already logged reading for this day.')
    else:
        log = ReadingLog(book_id=book.id, date=log_date)
        db.session.add(log)
        db.session.commit()
        flash('Reading day logged.')
    return redirect(url_for('main.view_book', uid=book.uid))

@bp.route('/book/<uid>/delete', methods=['POST'])
def delete_book(uid):
    book = Book.query.filter_by(uid=uid).first_or_404()
    ReadingLog.query.filter_by(book_id=book.id).delete()
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully.')
    return redirect(url_for('main.index'))

@bp.route('/book/<uid>/toggle_finished', methods=['POST'])
def toggle_finished(uid):
    book = Book.query.filter_by(uid=uid).first_or_404()
    if book.finish_date:
        book.finish_date = None
        flash('Book marked as currently reading.')
    else:
        book.finish_date = date.today()
        flash('Book marked as finished.')
    db.session.commit()
    return redirect(url_for('main.view_book', uid=book.uid))

@bp.route('/book/<uid>/start_reading', methods=['POST'])
def start_reading(uid):
    book = Book.query.filter_by(uid=uid).first_or_404()
    book.want_to_read = False
    if not book.start_date:
        book.start_date = datetime.today().date()
    db.session.commit()
    flash(f'Started reading "{book.title}".')
    return redirect(url_for('main.index'))

@bp.route('/book/<uid>/update_status', methods=['POST'])
def update_status(uid):
    book = Book.query.filter_by(uid=uid).first_or_404()
    # Set status based on checkboxes
    book.want_to_read = 'want_to_read' in request.form
    book.library_only = 'library_only' in request.form
    finished = 'finished' in request.form
    currently_reading = 'currently_reading' in request.form

    if finished:
        book.finish_date = datetime.now().date()
        book.want_to_read = False
        book.library_only = False
    elif currently_reading:
        book.finish_date = None
        book.want_to_read = False
        book.library_only = False
        if not book.start_date:
            book.start_date = datetime.now().date()
    elif book.want_to_read:
        book.finish_date = None
        book.library_only = False
    elif book.library_only:
        book.finish_date = None
        book.want_to_read = False

    db.session.commit()
    flash('Book status updated.')
    return redirect(url_for('main.view_book', uid=book.uid))

@bp.route('/search', methods=['GET', 'POST'])
def search_books():
    results = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('query', '')
        if query:
            # Google Books API search
            resp = requests.get(
                'https://www.googleapis.com/books/v1/volumes',
                params={'q': query, 'maxResults': 10}
            )
            data = resp.json()
            for item in data.get('items', []):
                volume_info = item.get('volumeInfo', {})
                image = volume_info.get('imageLinks', {}).get('thumbnail')
                isbn = None
                for iden in volume_info.get('industryIdentifiers', []):
                    if iden['type'] in ('ISBN_13', 'ISBN_10'):
                        isbn = iden['identifier']
                        break
                results.append({
                    'title': volume_info.get('title'),
                    'authors': ', '.join(volume_info.get('authors', [])),
                    'image': image,
                    'isbn': isbn
                })
    return render_template('search_books.html', results=results, query=query)

@bp.route('/library')
def library():
    books = Book.get_all_books()
    return render_template('library.html', books=books)

@bp.route('/public-library')
def public_library():
    filter_status = request.args.get('filter', 'all')
    books_query = Book.query.order_by(Book.id.desc())
    if filter_status == 'currently_reading':
        books_query = books_query.filter(
            Book.finish_date is None,
            Book.want_to_read is False,
            Book.library_only is False
        )
    elif filter_status == 'want_to_read':
        books_query = books_query.filter(Book.want_to_read is True)
    books = books_query.all()
    return render_template('public_library.html', books=books, filter_status=filter_status)

@bp.route('/book/<uid>/edit', methods=['GET', 'POST'])
def edit_book(uid):
    book = Book.query.filter_by(uid=uid).first_or_404()
    if request.method == 'POST':
        new_isbn = request.form['isbn']
        # Check for duplicate ISBN (excluding the current book)
        if Book.query.filter(Book.isbn == new_isbn, Book.uid != book.uid).first():
            flash('A book with this ISBN already exists.', 'danger')
            return render_template('edit_book.html', book=book)
        book.title = request.form['title']
        book.author = request.form['author']
        book.isbn = new_isbn
        cover_url = request.form.get('cover_url', '').strip()
        book.cover_url = cover_url if cover_url else None
        db.session.commit()
        flash('Book updated.', 'success')
        return redirect(url_for('main.view_book', uid=book.uid))
    return render_template('edit_book.html', book=book)

@bp.route('/month_review/<int:year>/<int:month>.jpg')
def month_review(year, month):
    # Query books finished in the given month/year
    books = Book.query.filter(
        Book.finish_date is not None,
        Book.finish_date >= datetime(year, month, 1),
        Book.finish_date < (
            datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
        )
    ).all()
    if not books:
        # Optionally, return a placeholder image or 404
        return "No books finished in this month.", 404

    img = generate_month_review_image(books, month, year)
    buf = BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    return send_file(buf, mimetype='image/jpeg', as_attachment=True, download_name=f"month_review_{year}_{month}.jpg")

@bp.route('/generate_month_wrapup')
def generate_month_wrapup():
    # Get current month and year using Central America time
    tz = pytz.timezone(current_app.config.get('TIMEZONE', 'UTC'))
    now_ca = datetime.now(tz)
    year = now_ca.year
    month = now_ca.month
    
    # Redirect to the month review endpoint
    return redirect(url_for('main.month_review', year=year, month=month))

@bp.route('/add_book_from_search', methods=['POST'])
def add_book_from_search():
    title = request.form.get('title')
    author = request.form.get('author')
    isbn = request.form.get('isbn')
    cover_url = request.form.get('cover_url')

    # Prevent duplicate ISBNs
    if isbn and Book.query.filter_by(isbn=isbn).first():
        flash('A book with this ISBN already exists.', 'danger')
        return redirect(url_for('main.search_books'))

    book = Book(
        title=title,
        author=author,
        isbn=isbn,
        cover_url=cover_url
    )
    book.save()
    flash(f'Added "{title}" to your library.', 'success')
    return redirect(url_for('main.library'))

@bp.route('/import_goodreads', methods=['POST'])
def import_goodreads():
    file = request.files.get('goodreads_csv')
    if not file or not file.filename.endswith('.csv'):
        flash('Please upload a valid Goodreads CSV file.', 'danger')
        return redirect(url_for('main.add_book'))

    stream = file.stream.read().decode('utf-8').splitlines()
    reader = csv.DictReader(stream)
    imported = 0
    for row in reader:
        title = row.get('Title')
        author = row.get('Author')
        # Goodreads CSV sometimes has ISBN/ISBN13 as ='978...'
        def clean_isbn(val):
            if not val:
                return ""
            val = val.strip()
            if val.startswith('="') and val.endswith('"'):
                val = val[2:-1]
            return val.strip()
        isbn = clean_isbn(row.get('ISBN13')) or clean_isbn(row.get('ISBN'))
        date_read = row.get('Date Read')
        want_to_read = 'to-read' in (row.get('Bookshelves') or '')
        finish_date = None
        if date_read:
            try:
                finish_date = datetime.strptime(date_read, "%Y/%m/%d").date()
            except Exception:
                pass
        # Skip books with missing or blank ISBN
        if not title or not author or not isbn or isbn == "":
            continue
        if not Book.query.filter_by(isbn=isbn).first():
            # Try Google Books cover first
            cover_url = get_google_books_cover(isbn)
            # Fallback to OpenLibrary if Google Books fails
            if not cover_url:
                book_data = fetch_book_data(isbn)
                cover_url = book_data.get('cover') if book_data else None
            # Fallback to default if both fail
            if not cover_url:
                cover_url = url_for('static', filename='bookshelf.png')
            book = Book(
                title=title,
                author=author,
                isbn=isbn,
                finish_date=finish_date,
                want_to_read=want_to_read,
                cover_url=cover_url
            )
            db.session.add(book)
            imported += 1
    db.session.commit()
    flash(f'Imported {imported} books from Goodreads.', 'success')
    return redirect(url_for('main.add_book'))