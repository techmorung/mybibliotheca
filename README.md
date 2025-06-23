# 📚 MyBibliotheca

**MyBibliotheca** is your self-hosted personal library & reading tracker—an open-source alternative to Goodreads, StoryGraph, and Fable. Log, organize, and visualize your reading journey.  

> 🚀 **Installation & full documentation live only at** [mybibliotheca.org](https://mybibliotheca.org) — click the “Documentation” badge below to get started!

[![Documentation](https://img.shields.io/badge/Documentation-MyBibliotheca-4a90e2?style=for-the-badge&logo=read-the-docs&logoColor=white)](https://mybibliotheca.org)  
[![Discord](https://img.shields.io/badge/Discord-7289DA?logo=discord&logoColor=white&style=for-the-badge)](https://discord.gg/Hc8C5eRm7Q)

---

## ✨ Core Features

- **ISBN Lookup** & bulk-import via CSV  
- Reading progress states: *Reading*, *Want to Read*, *Finished*  
- Daily logs + streak tracking  
- Monthly wrap-up image collages  
- Multi-user authentication & admin tools  
- Responsive UI (Bootstrap)  

_For the full feature list, screenshots, and guides, head over to the docs linked above._  

---

## 🚀 Quick Start

### Docker (recommended)

```bash
docker run -d \
  --name mybibliotheca \
  -p 5054:5054 \
  -v /path/to/data:/app/data \
  -e TIMEZONE=America/Chicago \
  -e WORKERS=6 \
  --restart unless-stopped \
  pickles4evaaaa/mybibliotheca:1.1.1
```
---

## 📄 License

Licensed under the [MIT License](LICENSE).

---

## ❤️ Contribute

**MyBibliotheca** is open source and contributions are welcome!

Pull requests, bug reports, and feature suggestions are appreciated.
