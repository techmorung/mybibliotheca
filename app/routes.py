from flask import Blueprint, current_app, render_template, request, redirect, url_for, jsonify, flash, send_file
from .models import Book, db, ReadingLog
from .utils import fetch_book_data, get_reading_streak, get_google_books_cover, generate_month_review_image, rate_limited_request
from datetime import datetime, date
import secrets
import requests
from io import BytesIO
import pytz
import csv # Ensure csv is imported

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
    timezone = pytz.timezone(current_app.config.get('TIMEZONE', 'UTC'))
    streak = get_reading_streak(timezone)
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
            # Fetch book data using the provided ISBN
            isbn = request.form['isbn'].strip()
            if not isbn:
                flash('Error: ISBN is required to fetch book data.', 'danger')
                return render_template('add_book.html', book_data=None)

            book_data = fetch_book_data(isbn)
            if not book_data:
                flash('No book data found for the provided ISBN.', 'warning')
            else:
                # Overwrite cover with Google Books if available
                google_cover = get_google_books_cover(isbn)
                if google_cover:
                    book_data['cover'] = google_cover

            # Re-render the form with fetched data
            return render_template('add_book.html', book_data=book_data)

        elif 'add' in request.form:
            # Validate required fields
            title = request.form['title'].strip()
            if not title:
                flash('Error: Title is required to add a book.', 'danger')
                return render_template('add_book.html', book_data=None)

            isbn = request.form['isbn']
            # Check for duplicate ISBN
            if Book.query.filter_by(isbn=isbn).first():
                flash('A book with this ISBN already exists.', 'danger')
                return render_template('add_book.html', book_data=None)

            author = request.form['author']
            start_date_str = request.form.get('start_date') or None
            finish_date_str = request.form.get('finish_date') or None
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
            finish_date = datetime.strptime(finish_date_str, '%Y-%m-%d').date() if finish_date_str else None
            want_to_read = 'want_to_read' in request.form
            library_only = 'library_only' in request.form

            cover_url = get_google_books_cover(isbn)

            # Get additional metadata from Google Books API first, then fallback to OpenLibrary
            google_data = get_google_books_cover(isbn, fetch_title_author=True)
            if google_data:
                description = google_data.get('description')
                published_date = google_data.get('published_date')
                page_count = google_data.get('page_count')
                categories = google_data.get('categories')
                publisher = google_data.get('publisher')
                language = google_data.get('language')
                average_rating = google_data.get('average_rating')
                rating_count = google_data.get('rating_count')
            else:
                # Fallback to OpenLibrary data
                ol_data = fetch_book_data(isbn)
                if ol_data:
                    description = ol_data.get('description')
                    published_date = ol_data.get('published_date')
                    page_count = ol_data.get('page_count')
                    categories = ol_data.get('categories')
                    publisher = ol_data.get('publisher')
                    language = ol_data.get('language')
                    average_rating = None
                    rating_count = None
                else:
                    description = published_date = page_count = categories = publisher = language = average_rating = rating_count = None

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
                library_only=library_only,
                description=description,
                published_date=published_date,
                page_count=page_count,
                categories=categories,
                publisher=publisher,
                language=language,
                average_rating=average_rating,
                rating_count=rating_count
            )
            book.save()
            flash(f'Book "{title}" added successfully.', 'success')
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
            # Google Books API search with rate limiting
            try:
                response = rate_limited_request(
                    'https://www.googleapis.com/books/v1/volumes',
                    timeout=5,
                    params={'q': query, 'maxResults': 10}
                )
                data = response.json()
            except Exception as e:
                current_app.logger.error(f"Google Books API search failed: {e}")
                flash('Search failed. Please try again later.', 'danger')
                return render_template('search_books.html', results=results, query=query)
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
    # Get filter parameters from URL
    category_filter = request.args.get('category', '')
    publisher_filter = request.args.get('publisher', '')
    language_filter = request.args.get('language', '')
    search_query = request.args.get('search', '')
    
    books_query = Book.query
    
    # Apply filters
    if category_filter:
        books_query = books_query.filter(Book.categories.contains(category_filter))
    if publisher_filter:
        books_query = books_query.filter(Book.publisher.ilike(f'%{publisher_filter}%'))
    if language_filter:
        books_query = books_query.filter(Book.language == language_filter)
    if search_query:
        books_query = books_query.filter(
            (Book.title.ilike(f'%{search_query}%')) |
            (Book.author.ilike(f'%{search_query}%')) |
            (Book.description.ilike(f'%{search_query}%'))
        )
    
    books = books_query.all()
    
    # Get distinct values for filter dropdowns
    all_books = Book.query.all()
    categories = set()
    publishers = set()
    languages = set()
    
    for book in all_books:
        if book.categories:
            categories.update([cat.strip() for cat in book.categories.split(',')])
        if book.publisher:
            publishers.add(book.publisher)
        if book.language:
            languages.add(book.language)
    
    return render_template(
        'library.html', 
        books=books,
        categories=sorted(categories),
        publishers=sorted(publishers),
        languages=sorted(languages),
        current_category=category_filter,
        current_publisher=publisher_filter,
        current_language=language_filter,
        current_search=search_query
    )

@bp.route('/public-library')
def public_library():
    filter_status = request.args.get('filter', 'all')
    books_query = Book.query
    
    if filter_status == 'currently_reading':
        books_query = books_query.filter(
            Book.finish_date.is_(None),
            Book.want_to_read.isnot(True),  # Handle NULL and False
            Book.library_only.isnot(True)  # Handle NULL and False
        )
    elif filter_status == 'want_to_read':
        books_query = books_query.filter(Book.want_to_read.is_(True))
    else:  # Default "Show All" case
        books_query = books_query.order_by(Book.finish_date.desc().nullslast(), Book.id.desc())
    
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
        
        # Update new metadata fields
        book.description = request.form.get('description', '').strip() or None
        book.published_date = request.form.get('published_date', '').strip() or None
        book.page_count = int(request.form.get('page_count')) if request.form.get('page_count', '').strip() else None
        book.publisher = request.form.get('publisher', '').strip() or None
        book.language = request.form.get('language', '').strip() or None
        book.categories = request.form.get('categories', '').strip() or None
        book.average_rating = float(request.form.get('average_rating')) if request.form.get('average_rating', '').strip() else None
        book.rating_count = int(request.form.get('rating_count')) if request.form.get('rating_count', '').strip() else None
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

    # Get additional metadata if available
    if isbn:
        google_data = get_google_books_cover(isbn, fetch_title_author=True)
        if google_data:
            description = google_data.get('description')
            published_date = google_data.get('published_date')
            page_count = google_data.get('page_count')
            categories = google_data.get('categories')
            publisher = google_data.get('publisher')
            language = google_data.get('language')
            average_rating = google_data.get('average_rating')
            rating_count = google_data.get('rating_count')
        else:
            description = published_date = page_count = categories = publisher = language = average_rating = rating_count = None
    else:
        description = published_date = page_count = categories = publisher = language = average_rating = rating_count = None

    book = Book(
        title=title,
        author=author,
        isbn=isbn,
        cover_url=cover_url,
        description=description,
        published_date=published_date,
        page_count=page_count,
        categories=categories,
        publisher=publisher,
        language=language,
        average_rating=average_rating,
        rating_count=rating_count
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
            # Try Google Books first for comprehensive metadata
            google_data = get_google_books_cover(isbn, fetch_title_author=True)
            if google_data:
                cover_url = google_data.get('cover')
                description = google_data.get('description')
                published_date = google_data.get('published_date')
                page_count = google_data.get('page_count')
                categories = google_data.get('categories')
                publisher = google_data.get('publisher')
                language = google_data.get('language')
                average_rating = google_data.get('average_rating')
                rating_count = google_data.get('rating_count')
            else:
                # Fallback to OpenLibrary if Google Books fails
                book_data = fetch_book_data(isbn)
                if book_data:
                    cover_url = book_data.get('cover')
                    description = book_data.get('description')
                    published_date = book_data.get('published_date')
                    page_count = book_data.get('page_count')
                    categories = book_data.get('categories')
                    publisher = book_data.get('publisher')
                    language = book_data.get('language')
                    average_rating = rating_count = None
                else:
                    cover_url = url_for('static', filename='bookshelf.png')
                    description = published_date = page_count = categories = publisher = language = average_rating = rating_count = None
            
            book = Book(
                title=title,
                author=author,
                isbn=isbn,
                finish_date=finish_date,
                want_to_read=want_to_read,
                cover_url=cover_url,
                description=description,
                published_date=published_date,
                page_count=page_count,
                categories=categories,
                publisher=publisher,
                language=language,
                average_rating=average_rating,
                rating_count=rating_count
            )
            db.session.add(book)
            imported += 1
    db.session.commit()
    flash(f'Imported {imported} books from Goodreads.', 'success')
    return redirect(url_for('main.add_book'))

@bp.route('/download_db', methods=['GET'])
def download_db():
    db_path = current_app.config.get('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', '')
    return send_file(
        db_path,
        as_attachment=True,
        download_name='books.db',
        mimetype='application/octet-stream'
    )

@bp.route('/bulk_import', methods=['GET', 'POST'])
def bulk_import():
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['csv_file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and file.filename.endswith('.csv'):
            try:
                # Read CSV content
                csv_content = file.stream.read().decode("utf-8")
                
                # Start background task
                from .utils import start_bulk_import_task
                task_id = start_bulk_import_task(csv_content, 'isbn_only')
                
                flash('Bulk import started! You can check the progress below.', 'success')
                return redirect(url_for('main.task_status', task_id=task_id))

            except Exception as e:
                current_app.logger.error(f"Error starting bulk import: {e}")
                flash('An error occurred starting the bulk import. Please try again.', 'danger')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload a CSV file.', 'danger')
            return redirect(request.url)

    return render_template('bulk_import.html')

@bp.route('/task/<task_id>')
def task_status(task_id):
    """Display task status page"""
    from .models import Task
    task = Task.query.get_or_404(task_id)
    return render_template('task_status.html', task=task)

@bp.route('/api/task/<task_id>')
def api_task_status(task_id):
    """API endpoint for task status (for AJAX polling)"""
    from .models import Task
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())

@bp.route('/tasks')
def list_tasks():
    """List all tasks"""
    from .models import Task
    tasks = Task.query.order_by(Task.created_at.desc()).limit(20).all()
    return render_template('task_list.html', tasks=tasks)