from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qlsach.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    books = db.relationship('Book', backref='category', lazy=True, cascade="all, delete-orphan")

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

@app.route('/')
def dashboard():
    total_categories = Category.query.count()
    total_books = Book.query.count()
    return render_template('dashboard.html', total_categories=total_categories, total_books=total_books)

@app.route('/categories', methods=['GET', 'POST'])
def manage_categories():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            new_cat = Category(name=name)
            db.session.add(new_cat)
            db.session.commit()
            flash('Thêm danh mục thành công!', 'success')
        return redirect(url_for('manage_categories'))
    
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

@app.route('/categories/edit/<int:id>', methods=['POST'])
def edit_category(id):
    category = Category.query.get_or_404(id)
    category.name = request.form.get('name')
    db.session.commit()
    flash('Cập nhật danh mục thành công!', 'warning')
    return redirect(url_for('manage_categories'))

@app.route('/categories/delete/<int:id>')
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('Đã xóa danh mục!', 'danger')
    return redirect(url_for('manage_categories'))

@app.route('/books', methods=['GET', 'POST'])
def manage_books():
    categories = Category.query.all()
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        category_id = request.form.get('category_id')
        
        if title and author and category_id:
            new_book = Book(title=title, author=author, category_id=category_id)
            db.session.add(new_book)
            db.session.commit()
            flash('Thêm sách thành công!', 'success')
        return redirect(url_for('manage_books'))
    
    books = Book.query.all()
    return render_template('books.html', books=books, categories=categories)

@app.route('/books/edit/<int:id>', methods=['POST'])
def edit_book(id):
    book = Book.query.get_or_404(id)
    book.title = request.form.get('title')
    book.author = request.form.get('author')
    book.category_id = request.form.get('category_id')
    db.session.commit()
    flash('Cập nhật sách thành công!', 'warning')
    return redirect(url_for('manage_books'))

@app.route('/books/delete/<int:id>')
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    flash('Đã xóa sách!', 'danger')
    return redirect(url_for('manage_books'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)