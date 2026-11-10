from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, ForeignKey, String, event, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

APP_DIR = Path(__file__).resolve().parent
DATABASE = APP_DIR.parents[1] / "instance" / "ql_sach.db"
DATABASE.parent.mkdir(parents=True, exist_ok=True)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE.as_posix()}"
db.init_app(app)

class Category(db.Model):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100, collation="NOCASE"), unique=True, nullable=False
    )
    description: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )
    books: Mapped[list["Book"]] = relationship(
        back_populates="category", passive_deletes="all"
    )

class Book(db.Model):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str] = mapped_column(String(150), nullable=False)
    isbn: Mapped[str] = mapped_column(String(30), default="", nullable=False)
    publisher: Mapped[str] = mapped_column(String(150), default="", nullable=False)
    published_year: Mapped[int | None] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(String(2000), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )
    category: Mapped[Category] = relationship(back_populates="books")

def enable_sqlite_foreign_keys(connection, _connection_record):
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def init_db():
    with app.app_context():
        event.listen(db.engine, "connect", enable_sqlite_foreign_keys)
        db.create_all()

@app.context_processor
def inject_template_values():
    notices = {
        "category-added": ("success", "Đã thêm danh mục sách."),
        "category-updated": ("success", "Đã cập nhật danh mục."),
        "category-deleted": ("success", "Đã xóa danh mục."),
        "category-duplicate": ("error", "Tên danh mục này đã tồn tại."),
        "category-in-use": (
            "error",
            "Không thể xóa danh mục đang có sách. Hãy chuyển hoặc xóa sách trước.",
        ),
        "category-missing": ("error", "Không tìm thấy danh mục cần xóa."),
        "category-required": (
            "error",
            "Hãy tạo danh mục trước khi thêm sách.",
        ),
        "book-added": ("success", "Đã thêm sách."),
        "book-updated": ("success", "Đã cập nhật sách."),
        "book-deleted": ("success", "Đã xóa sách."),
        "book-missing": ("error", "Không tìm thấy sách cần xóa."),
    }
    return {"notification": notices.get(request.args.get("notice"))}

@app.get("/")
def dashboard():
    stats = {
        "categories": db.session.scalar(db.select(func.count(Category.id))) or 0,
        "books": db.session.scalar(db.select(func.count(Book.id))) or 0,
    }
    stats["books_without_category"] = db.session.scalar(
        db.select(func.count(Category.id))
        .outerjoin(Book)
        .where(Book.id.is_(None))
    ) or 0
    category_rows = db.session.execute(
        db.select(Category, func.count(Book.id).label("book_count"))
        .outerjoin(Book)
        .group_by(Category.id)
        .order_by(Category.name)
    ).all()
    category_stats = [
        {
            "id": category.id,
            "name": category.name,
            "book_count": book_count,
        }
        for category, book_count in category_rows
    ]
    recent_books = db.session.execute(
        db.select(Book, Category.name.label("category_name"))
        .join(Book.category)
        .order_by(Book.created_at.desc(), Book.id.desc())
        .limit(5)
    ).all()
    recent_books = [
        {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "created_at": book.created_at,
            "category_name": category_name,
        }
        for book, category_name in recent_books
    ]
    return render_template(
        "dashboard.html",
        stats=stats,
        category_stats=category_stats,
        recent_books=recent_books,
    )

@app.get("/danh-muc")
def categories():
    rows = db.session.execute(
        db.select(Category, func.count(Book.id).label("book_count"))
        .outerjoin(Book)
        .group_by(Category.id)
        .order_by(Category.name)
    ).all()
    category_list = [
        {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "book_count": book_count,
        }
        for category, book_count in rows
    ]
    return render_template("categories.html", categories=category_list)

def category_form_values():
    return {
        "name": request.form.get("name", "").strip(),
        "description": request.form.get("description", "").strip(),
    }

def validate_category(values):
    errors = []
    if not values["name"]:
        errors.append("Tên danh mục không được để trống.")
    elif len(values["name"]) > 100:
        errors.append("Tên danh mục không được vượt quá 100 ký tự.")
    if len(values["description"]) > 1000:
        errors.append("Mô tả không được vượt quá 1000 ký tự.")
    return errors

@app.route("/danh-muc/them", methods=["GET", "POST"])
def add_category():
    values = {"name": "", "description": ""}
    errors = []
    if request.method == "POST":
        values = category_form_values()
        errors = validate_category(values)
        if not errors:
            try:
                db.session.add(Category(**values))
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                errors.append("Tên danh mục này đã tồn tại.")
            else:
                return redirect(url_for("categories", notice="category-added"))
    return render_template(
        "category_form.html", page_title="Thêm danh mục", category=values, errors=errors
    )

@app.route("/danh-muc/<int:category_id>/sua", methods=["GET", "POST"])
def edit_category(category_id):
    category = db.get_or_404(Category, category_id)
    values = {"name": category.name, "description": category.description}
    errors = []
    if request.method == "POST":
        values.update(category_form_values())
        errors = validate_category(values)
        if not errors:
            category.name = values["name"]
            category.description = values["description"]
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                errors.append("Tên danh mục này đã tồn tại.")
            else:
                return redirect(url_for("categories", notice="category-updated"))
    return render_template(
        "category_form.html", page_title="Sửa danh mục", category=values, errors=errors
    )

@app.post("/danh-muc/<int:category_id>/xoa")
def delete_category(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        return redirect(url_for("categories", notice="category-missing"))
    db.session.delete(category)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return redirect(url_for("categories", notice="category-in-use"))
    return redirect(url_for("categories", notice="category-deleted"))

@app.get("/sach")
def books():
    category_id = request.args.get("danh_muc", type=int)
    search = request.args.get("q", "").strip()
    statement = db.select(Book).join(Book.category)
    if category_id is not None:
        statement = statement.where(Book.category_id == category_id)
    if search:
        search_pattern = f"%{search}%"
        statement = statement.where(
            db.or_(
                Book.title.ilike(search_pattern),
                Book.author.ilike(search_pattern),
                Book.isbn.ilike(search_pattern),
            )
        )
    rows = db.session.scalars(statement.order_by(Book.title)).all()
    category_rows = db.session.scalars(
        db.select(Category).order_by(Category.name)
    ).all()
    book_list = [
        {
            "id": book.id,
            "category_id": book.category_id,
            "title": book.title,
            "author": book.author,
            "isbn": book.isbn,
            "publisher": book.publisher,
            "published_year": book.published_year,
            "description": book.description,
            "category_name": book.category.name,
        }
        for book in rows
    ]
    return render_template(
        "books.html",
        books=book_list,
        categories=category_rows,
        selected_category=category_id,
        search=search,
    )

def book_form_values():
    year_text = request.form.get("published_year", "").strip()
    year = None
    year_error = False
    if year_text:
        try:
            year = int(year_text)
        except ValueError:
            year_error = True
    category_text = request.form.get("category_id", "").strip()
    category_id = None
    category_error = False
    if category_text:
        try:
            category_id = int(category_text)
        except ValueError:
            category_error = True
    return {
        "category_id": category_id,
        "title": request.form.get("title", "").strip(),
        "author": request.form.get("author", "").strip(),
        "isbn": request.form.get("isbn", "").strip(),
        "publisher": request.form.get("publisher", "").strip(),
        "published_year": year,
        "published_year_text": year_text,
        "description": request.form.get("description", "").strip(),
        "category_error": category_error,
        "year_error": year_error,
    }


def validate_book(values):
    errors = []
    if values["category_error"] or values["category_id"] is None:
        errors.append("Vui lòng chọn danh mục sách hợp lệ.")
    elif db.session.get(Category, values["category_id"]) is None:
        errors.append("Danh mục được chọn không tồn tại.")
    if not values["title"]:
        errors.append("Tên sách không được để trống.")
    elif len(values["title"]) > 200:
        errors.append("Tên sách không được vượt quá 200 ký tự.")
    if not values["author"]:
        errors.append("Tác giả không được để trống.")
    elif len(values["author"]) > 150:
        errors.append("Tên tác giả không được vượt quá 150 ký tự.")
    if len(values["isbn"]) > 30:
        errors.append("ISBN không được vượt quá 30 ký tự.")
    if len(values["publisher"]) > 150:
        errors.append("Nhà xuất bản không được vượt quá 150 ký tự.")
    if values["year_error"]:
        errors.append("Năm xuất bản phải là một số nguyên.")
    elif values["published_year"] is not None and not 1000 <= values["published_year"] <= 9999:
        errors.append("Năm xuất bản phải nằm trong khoảng 1000–9999.")
    if len(values["description"]) > 2000:
        errors.append("Mô tả không được vượt quá 2000 ký tự.")
    return errors

def render_book_form(page_title, book, errors):
    category_rows = db.session.scalars(
        db.select(Category).order_by(Category.name)
    ).all()
    if not category_rows:
        return redirect(url_for("add_category", notice="category-required"))
    return render_template(
        "book_form.html",
        page_title=page_title,
        book=book,
        categories=category_rows,
        errors=errors,
    )

@app.route("/sach/them", methods=["GET", "POST"])
def add_book():
    values = {
        "category_id": request.args.get("danh_muc", type=int),
        "title": "",
        "author": "",
        "isbn": "",
        "publisher": "",
        "published_year": None,
        "published_year_text": "",
        "description": "",
        "category_error": False,
        "year_error": False,
    }
    errors = []
    if request.method == "POST":
        values = book_form_values()
        errors = validate_book(values)
        if not errors:
            book = Book(
                category_id=values["category_id"],
                title=values["title"],
                author=values["author"],
                isbn=values["isbn"],
                publisher=values["publisher"],
                published_year=values["published_year"],
                description=values["description"],
            )
            db.session.add(book)
            db.session.commit()
            return redirect(
                url_for(
                    "books",
                    danh_muc=values["category_id"],
                    notice="book-added",
                )
            )
    return render_book_form("Thêm sách", values, errors)

@app.route("/sach/<int:book_id>/sua", methods=["GET", "POST"])
def edit_book(book_id):
    book = db.get_or_404(Book, book_id)
    values = {
        "category_id": book.category_id,
        "title": book.title,
        "author": book.author,
        "isbn": book.isbn,
        "publisher": book.publisher,
        "published_year": book.published_year,
        "published_year_text": (
            str(book.published_year) if book.published_year is not None else ""
        ),
        "description": book.description,
        "category_error": False,
        "year_error": False,
    }
    errors = []
    if request.method == "POST":
        values.update(book_form_values())
        errors = validate_book(values)
        if not errors:
            book.category_id = values["category_id"]
            book.title = values["title"]
            book.author = values["author"]
            book.isbn = values["isbn"]
            book.publisher = values["publisher"]
            book.published_year = values["published_year"]
            book.description = values["description"]
            db.session.commit()
            return redirect(
                url_for(
                    "books",
                    danh_muc=values["category_id"],
                    notice="book-updated",
                )
            )
    return render_book_form("Sửa thông tin sách", values, errors)

@app.post("/sach/<int:book_id>/xoa")
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return redirect(url_for("books", notice="book-missing"))
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for("books", notice="book-deleted"))

init_db()

if __name__ == "__main__":
    app.run(debug=True)