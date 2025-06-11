# Bibliotheca

**Bibliotheca** is a personal library and reading tracker web application built with Flask. It allows you to log, organize, and visualize your reading journey. Add books by ISBN, track your reading status, log daily reading, and generate monthly wrap-up images of your finished books.

## Features

- **Add Books**: Quickly add books by ISBN, with automatic cover and metadata fetching.
- **Track Reading**: Mark books as "Currently Reading", "Want to Read", "Finished", or "Library Only".
- **Reading Logs**: Log your reading days and track your reading streak.
- **Monthly Wrap-Up**: Generate a shareable image collage of books finished each month.
- **Search**: Search for books using the Google Books API.
- **Responsive UI**: Clean, mobile-friendly interface using Bootstrap.

![App Preview](https://i.imgur.com/AkiBN68.png)
![Library](https://i.imgur.com/h9iR9ql.png)

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/pickles4evaaaa/bibliotheca.git
   cd bibliotheca
   ```


1.a **Create Python Virtual Environment:**
   ```sh
   cd bibliotheca
   python3 -m venv venv
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up the database:**
   ```sh
   python setup_db.py
   ```

4. **Run the application:**
   ```sh
   python run.py
   ```
   The app will be available at [http://127.0.0.1:5054](http://127.0.0.1:5054).

### Configuration

- By default, the app uses SQLite and a development secret key.
- For production, set environment variables for `SECRET_KEY` and `DATABASE_URL` or edit `config.py`.

## Project Structure

```
Bibliotheca/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── utils.py
│   └── templates/
├── static/
├── requirements.txt
├── run.py
├── setup_db.py
└── README.md
```

## License

This project is licensed under the MIT License.

---

**Bibliotheca** is open source and contributions are welcome!
