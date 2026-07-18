"""
Image Compression Tool
-----------------------
A Flask web app that lets registered users upload JPEG / PNG / WEBP / BMP
images, compresses them server-side with Pillow, stores the result on disk,
and keeps a per-user history (original size, compressed size, % saved) in
a database.

Project by: Ruturaj Mohan Shinde, Yashkumar Vijay Gaikwad, Vaishnavi Bhagwatiprasad Oza
Guide: Ms. Shivani Neralkar | MGM's College of Computer Science & IT, Nanded
"""

import os
import uuid
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_from_directory, abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image

# ---------------------------------------------------------------------------
# App & config (Render Persistent Storage Configuration)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp"}[cite: 2]
MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB per upload[cite: 2]

# Check if running on Render environment
IS_RENDER = os.environ.get("RENDER") == "true"

if IS_RENDER:
    # Use the persistent disk paths mapped on Render
    # Note: If the root /data has strict mount rules, Render allows sub-folder generation
    UPLOAD_DIR = "/data/uploads"
    DB_PATH = "/data/app.db"
else:
    # Use local project paths for development environment
    UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")[cite: 2]
    DB_PATH = os.path.join(BASE_DIR, "instance", "app.db")[cite: 2]

app = Flask(__name__)[cite: 2]
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")[cite: 2]

# Database URI routing based on our environment selection
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get([cite: 2]
    "DATABASE_URL", f"sqlite:///{DB_PATH}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False[cite: 2]
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH[cite: 2]

db = SQLAlchemy(app)[cite: 2]

login_manager = LoginManager(app)[cite: 2]
login_manager.login_view = "login"[cite: 2]
login_manager.login_message = "Please log in to access your dashboard."[cite: 2]
login_manager.login_message_category = "info"[cite: 2]

# Safe Directory Initialization with try-except to catch permission edge cases
try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except PermissionError:
    # Fallback to local working directory structure if Render volume isn't ready
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
    DB_PATH = os.path.join(BASE_DIR, "app.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

if not IS_RENDER:
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)[cite: 2]

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    images = db.relationship(
        "ImageRecord", backref="owner", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


class ImageRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    original_size = db.Column(db.Integer, nullable=False)   # bytes
    compressed_size = db.Column(db.Integer, nullable=False)  # bytes
    quality = db.Column(db.Integer, nullable=False)
    image_format = db.Column(db.String(10), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def percent_saved(self):
        if self.original_size == 0:
            return 0
        return round((1 - (self.compressed_size / self.original_size)) * 100, 1)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def human_size(num_bytes):
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{int(num_bytes)} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


app.jinja_env.filters["human_size"] = human_size


def compress_image(file_storage, quality, shrink_large):
    """
    Compress an uploaded image using Pillow.
    Returns (stored_filename, original_size, compressed_size, fmt).
    """
    original_bytes = file_storage.read()
    original_size = len(original_bytes)
    file_storage.seek(0)

    img = Image.open(file_storage)
    fmt = (img.format or "JPEG").upper()
    if fmt == "JPG":
        fmt = "JPEG"

    # Optionally cap resolution to shave extra size off very large photos
    if shrink_large:
        max_dim = 1920
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.LANCZOS)

    ext = "jpg" if fmt == "JPEG" else fmt.lower()
    stored_filename = f"{uuid.uuid4().hex}.{ext}"
    stored_path = os.path.join(UPLOAD_DIR, stored_filename)

    save_kwargs = {}
    if fmt == "JPEG":
        # JPEG has no alpha channel
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        save_kwargs = {"quality": quality, "optimize": True, "progressive": True}
    elif fmt == "PNG":
        # Pillow PNG compress_level: 0 (fast/large) - 9 (slow/small)
        compress_level = max(0, min(9, round((100 - quality) / 100 * 9)))
        save_kwargs = {"optimize": True, "compress_level": compress_level}
        # Extra savings at low quality: reduce to an adaptive palette
        if quality < 70 and img.mode in ("RGB", "RGBA"):
            img = img.convert("RGBA").convert(
                "P", palette=Image.ADAPTIVE, colors=256
            )
    elif fmt == "WEBP":
        save_kwargs = {"quality": quality, "method": 6}
    else:  # BMP and anything else -> fall back to optimized JPEG-like save
        save_kwargs = {"optimize": True}

    img.save(stored_path, format=fmt, **save_kwargs)
    compressed_size = os.path.getsize(stored_path)

    return stored_filename, original_size, compressed_size, fmt


# ---------------------------------------------------------------------------
# Routes: marketing / auth
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        error = None
        if not username or not email or not password:
            error = "All fields are required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif User.query.filter_by(username=username).first():
            error = "That username is already taken."
        elif User.query.filter_by(email=email).first():
            error = "An account with that email already exists."

        if error:
            flash(error, "error")
            return render_template("register.html", username=username, email=email)

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created. You can log in now.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.username}.", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))

        flash("Invalid username/email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Routes: dashboard / compression
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    images = (
        ImageRecord.query.filter_by(user_id=current_user.id)
        .order_by(ImageRecord.uploaded_at.desc())
        .all()
    )
    total_original = sum(i.original_size for i in images)
    total_compressed = sum(i.compressed_size for i in images)
    total_saved = total_original - total_compressed
    return render_template(
        "dashboard.html",
        images=images,
        total_original=total_original,
        total_compressed=total_compressed,
        total_saved=total_saved,
    )


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("image")
    quality = request.form.get("quality", 75)
    shrink_large = request.form.get("shrink_large") == "on"

    try:
        quality = max(1, min(95, int(quality)))
    except ValueError:
        quality = 75

    if not file or file.filename == "":
        flash("Please choose an image to upload.", "error")
        return redirect(url_for("dashboard"))

    if not allowed_file(file.filename):
        flash("Unsupported file type. Use JPEG, PNG, WEBP, or BMP.", "error")
        return redirect(url_for("dashboard"))

    try:
        stored_filename, original_size, compressed_size, fmt = compress_image(
            file, quality, shrink_large
        )
    except Exception as exc:  # noqa: BLE001
        flash(f"Could not process that image: {exc}", "error")
        return redirect(url_for("dashboard"))

    record = ImageRecord(
        user_id=current_user.id,
        original_filename=secure_filename(file.filename),
        stored_filename=stored_filename,
        original_size=original_size,
        compressed_size=compressed_size,
        quality=quality,
        image_format=fmt,
    )
    db.session.add(record)
    db.session.commit()

    flash(
        f"Compressed {record.original_filename} — saved {record.percent_saved}%.",
        "success",
    )
    return redirect(url_for("dashboard"))


@app.route("/download/<int:image_id>")
@login_required
def download(image_id):
    record = db.session.get(ImageRecord, image_id)
    if not record or record.user_id != current_user.id:
        abort(404)
    download_name = f"compressed_{record.original_filename}"
    return send_from_directory(
        UPLOAD_DIR, record.stored_filename, as_attachment=True,
        download_name=download_name,
    )


@app.route("/delete/<int:image_id>", methods=["POST"])
@login_required
def delete(image_id):
    record = db.session.get(ImageRecord, image_id)
    if not record or record.user_id != current_user.id:
        abort(404)

    stored_path = os.path.join(UPLOAD_DIR, record.stored_filename)
    if os.path.exists(stored_path):
        os.remove(stored_path)

    db.session.delete(record)
    db.session.commit()
    flash("Image removed.", "info")
    return redirect(url_for("dashboard"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
