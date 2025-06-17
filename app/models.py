from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import secrets
import json

db = SQLAlchemy()

class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(512), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    progress = db.Column(db.Integer, default=0)  # 0-100
    total_items = db.Column(db.Integer, default=0)
    processed_items = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    current_item = db.Column(db.String(512), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    result = db.Column(db.Text, nullable=True)  # JSON result data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, id, name, description=None, total_items=0):
        self.id = id
        self.name = name
        self.description = description
        self.total_items = total_items

    def update_progress(self, processed_items, current_item=None, success_count=None, error_count=None):
        self.processed_items = processed_items
        if current_item:
            self.current_item = current_item
        if success_count is not None:
            self.success_count = success_count
        if error_count is not None:
            self.error_count = error_count
        
        if self.total_items > 0:
            self.progress = min(int((processed_items / self.total_items) * 100), 100)
        
        db.session.commit()

    def set_running(self):
        self.status = 'running'
        self.started_at = datetime.utcnow()
        db.session.commit()

    def set_completed(self, result=None):
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.progress = 100
        if result:
            self.result = json.dumps(result)
        db.session.commit()

    def set_failed(self, error_message):
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'progress': self.progress,
            'total_items': self.total_items,
            'processed_items': self.processed_items,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'current_item': self.current_item,
            'error_message': self.error_message,
            'result': json.loads(self.result) if self.result else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(12), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(6))
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    finish_date = db.Column(db.Date, nullable=True)
    cover_url = db.Column(db.String(512), nullable=True)
    want_to_read = db.Column(db.Boolean, default=False)
    library_only = db.Column(db.Boolean, default=False)
    # New metadata fields
    description = db.Column(db.Text, nullable=True)
    published_date = db.Column(db.String(50), nullable=True)
    page_count = db.Column(db.Integer, nullable=True)
    categories = db.Column(db.String(500), nullable=True)  # Store as comma-separated string
    publisher = db.Column(db.String(255), nullable=True)
    language = db.Column(db.String(10), nullable=True)
    average_rating = db.Column(db.Float, nullable=True)
    rating_count = db.Column(db.Integer, nullable=True)

    def __init__(self, title, author, isbn, start_date=None, finish_date=None, cover_url=None, want_to_read=False, library_only=False, description=None, published_date=None, page_count=None, categories=None, publisher=None, language=None, average_rating=None, rating_count=None, **kwargs):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.start_date = start_date
        self.finish_date = finish_date
        self.cover_url = cover_url
        self.want_to_read = want_to_read
        self.library_only = library_only
        self.description = description
        self.published_date = published_date
        self.page_count = page_count
        self.categories = categories
        self.publisher = publisher
        self.language = language
        self.average_rating = average_rating
        self.rating_count = rating_count
        # If you have other fields, set them here or with kwargs

    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_all_books(cls):
        return cls.query.all()

    @classmethod
    def get_book_by_isbn(cls, isbn):
        return cls.query.filter_by(isbn=isbn).first()

class ReadingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)

    book = db.relationship('Book', backref=db.backref('reading_logs', lazy=True))