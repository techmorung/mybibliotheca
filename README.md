# 📚 Bibliotheca

**Bibliotheca** is a self-hosted personal library and reading tracker web app built with Flask. It lets you log, organize, and visualize your reading journey. Add books by ISBN, track reading progress, log daily reading, and generate monthly wrap-up images of your finished titles.

---

## ✨ Features

- 📖 **Add Books**: Add books quickly by ISBN with automatic cover and metadata fetching.
- ✅ **Track Progress**: Mark books as *Currently Reading*, *Want to Read*, *Finished*, or *Library Only*.
- 📅 **Reading Logs**: Log daily reading activity and maintain streaks.
- 🖼️ **Monthly Wrap-Ups**: Generate shareable image collages of books completed each month.
- 🔎 **Search**: Find and import books using the Google Books API.
- 📱 **Responsive UI**: Clean, mobile-friendly interface built with Bootstrap.

---

## 🖼️ Preview

![App Preview](https://i.imgur.com/AkiBN68.png)
![Library](https://i.imgur.com/h9iR9ql.png)

---

## 🚀 Getting Started

## 📦 Run with Docker

Bibliotheca can be run completely in Docker — no need to install Python or dependencies on your machine.

### ✅ Prerequisites

- [Docker](https://www.docker.com/) installed
- [Docker Compose](https://docs.docker.com/compose/) installed

---

### 🔁 Option 1: One-liner (Docker only)

```bash
docker run -d \
  -v "$PWD/books.db:/app/books.db" \
  -p 5054:5054 \
  --name bibliotheca \
  pickles4evaaaa/bibliotheca:latest

#### 📄 `docker-compose.yml`

```yaml
version: '3.8'

services:
  bibliotheca:
    image: pickles4evaaaa/bibliotheca:latest
    container_name: bibliotheca
    ports:
      - "5054:5054"
    volumes:
      - ./books.db:/app/books.db
    restart: unless-stopped


### ✅ Prerequisites (install from source)

- Python 3.8+
- `pip`

---

### 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/pickles4evaaaa/bibliotheca.git
   cd bibliotheca
   ```

2. **Create a Python virtual environment**  
   *(Virtual environments isolate dependencies to prevent conflicts and make the app easier to run and update.)*
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
   ```bash
   python setup_db.py
   ```

5. **Run the app**
   ```bash
   python run.py
   ```
   Visit: [http://127.0.0.1:5054](http://127.0.0.1:5054)

---

### ⚙️ Configuration

- Defaults to SQLite and a development secret key.
- For production, set environment variables like `SECRET_KEY` and `DATABASE_URL`, or edit `config.py`.

---

## 🗂️ Project Structure

```
bibliotheca/
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

---

## 📄 License

Licensed under the [MIT License](LICENSE).

---

### ❤️ Contribute

**Bibliotheca** is open source and contributions are welcome!
