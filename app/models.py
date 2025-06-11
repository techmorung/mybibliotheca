from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import secrets

db = SQLAlchemy()

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

    def __init__(self, title, author, isbn, start_date=None, finish_date=None, cover_url=None, want_to_read=False, library_only=False, **kwargs):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.start_date = start_date
        self.finish_date = finish_date
        self.cover_url = cover_url
        self.want_to_read = want_to_read
        self.library_only = library_only
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