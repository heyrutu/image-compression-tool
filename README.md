# PixelPress — Image Compression Tool

A Flask web app for the "Image Compression Tool" project (TYBCA, MGM's College of
Computer Science & IT, Nanded). Users create an account, upload a JPEG/PNG/WEBP/BMP
image, choose a quality level, and get back a compressed file — with every upload
saved to their personal history (original size, compressed size, % saved).

## Tech stack
- **Frontend:** HTML, CSS, JavaScript (server-rendered with Jinja2 templates)
- **Backend:** Python (Flask)
- **Database:** SQLite by default (zero setup). Swap to MySQL by installing
  `pymysql` and setting the `DATABASE_URL` environment variable — see `app.py`.
- **Image processing:** Pillow
- **Auth:** Flask-Login + password hashing via Werkzeug

## Features
- User registration and login (passwords are hashed, never stored in plain text)
- Drag-and-drop image upload with a quality slider (10–95)
- Format-aware compression: JPEG re-encoding, PNG palette reduction, WEBP quality codec
- Optional resolution cap (1920px) for extra savings on large photos
- Per-user history: original size, compressed size, % saved, download, delete
- Each user only sees their own images

## Setup

```bash
# 1. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

The SQLite database (`instance/app.db`) and uploads folder (`static/uploads/`)
are created automatically on first run.

## Switching to MySQL

```bash
pip install pymysql
```

```bash
export DATABASE_URL="mysql+pymysql://<user>:<password>@localhost/image_compression_db"
```

Create the database first (`CREATE DATABASE image_compression_db;`), then run
`python app.py` as usual — the tables are created automatically.

## Project structure

```
image_compression_tool/
├── app.py                  # Routes, models, auth, compression logic
├── requirements.txt
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   └── uploads/             # Compressed images are stored here
├── templates/
│   ├── base.html
│   ├── index.html           # Landing page
│   ├── login.html
│   ├── register.html
│   └── dashboard.html       # Upload + history
└── instance/
    └── app.db                # SQLite database (created on first run)
```

## Team
- Ruturaj Mohan Shinde
- Yashkumar Vijay Gaikwad
- Vaishnavi Bhagwatiprasad Oza

Guide: Ms. Shivani Neralkar · Project Incharge: Ms. Rajshri N. Nadre
