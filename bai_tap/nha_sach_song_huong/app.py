import os
import uuid
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from datetime import datetime, timedelta
from models import db, Book, Category, Order, OrderItem, OrderHistory
from forms import CheckoutForm, BookForm, CategoryForm
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///songhuong.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
CSRFProtect(app)

db.init_app(app)

@app.context_processor
def inject_cart_count():
    cart = session.get('cart', {})
    cart_count = sum(cart.values())
    return dict(cart_count=cart_count)

@app.route('/')
def index():
    return redirect(url_for('books'))

@app.route('/books')
def books():
    q = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', type=int)

    query = Book.query.order_by(Book.id.desc())
    if q:
        query = query.filter((Book.title.ilike(f'%{q}%')) | (Book.author.ilike(f'%{q}%')))
    if category_id is not None:
        query = query.filter_by(category_id=category_id)

    return render_template(
        'store/books.html',
        books=query.all(),
        categories=Category.query.order_by(Category.name).all(),
        current_cat=str(category_id) if category_id is not None else ''
    )

@app.route('/book/<int:id>')
def book_detail(id):
    book = Book.query.get_or_404(id)
    cart = session.get('cart', {})
    in_cart = cart.get(str(id), 0)

    max_add = book.stock - in_cart
    
    return render_template('store/book_detail.html', book=book, in_cart=in_cart, max_add=max_add)

@app.route('/cart/add/<int:book_id>', methods=['POST'])
def add_to_cart(book_id):
    book = Book.query.get_or_404(book_id)
    try:
        quantity = int(request.form.get('quantity', 1))
    except ValueError:
        flash('Số lượng không hợp lệ.', 'danger')
        return redirect(request.referrer or url_for('books'))

    if quantity <= 0:
        flash('Số lượng phải lớn hơn 0.', 'danger')
        return redirect(request.referrer or url_for('books'))

    cart = session.get('cart', {})
    current_quantity = cart.get(str(book_id), 0)

    if current_quantity + quantity > book.stock:
        flash(f'Lỗi: Chỉ có thể thêm tối đa {book.stock - current_quantity} cuốn.', 'danger')
    else:
        cart[str(book_id)] = current_quantity + quantity
        session['cart'] = cart
        session.modified = True
        flash(f'✓ Đã thêm {quantity} × {book.title} vào giỏ hàng.', 'success')

    return redirect(request.referrer or url_for('books'))

@app.route('/cart')
def cart():
    cart_session = session.get('cart', {})
    cart_items = []
    total_amount = 0
    
    for book_id_str, quantity in cart_session.items():
        book = Book.query.get(int(book_id_str))
        if book: # Chỉ hiển thị sách còn tồn tại trong DB, lấy giá mới nhất
            item_total = book.price * quantity
            total_amount += item_total
            cart_items.append({
                'book': book,
                'quantity': quantity,
                'item_total': item_total
            })
        else:
             session['cart'].pop(book_id_str, None)
             session.modified = True

    return render_template('store/cart.html', cart_items=cart_items, total_amount=total_amount)

@app.route('/cart/update/<int:book_id>', methods=['POST'])
def update_cart(book_id):
    book = Book.query.get_or_404(book_id)
    action = request.form.get('action') # 'increase' hoặc 'decrease'
    
    cart = session.get('cart', {})
    book_id_str = str(book_id)
    
    if book_id_str in cart:
        if action == 'increase':
            if cart[book_id_str] < book.stock:
                cart[book_id_str] += 1
            else:
                 flash('Đã đạt số lượng tồn kho tối đa.', 'warning')
        elif action == 'decrease':
            cart[book_id_str] -= 1
            if cart[book_id_str] <= 0:
                cart.pop(book_id_str)
                
        session['cart'] = cart
        session.modified = True
        
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:book_id>', methods=['POST'])
def remove_from_cart(book_id):
    cart = session.get('cart', {})
    book_id_str = str(book_id)
    if book_id_str in cart:
        cart.pop(book_id_str)
        session['cart'] = cart
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/cart/clear', methods=['POST'])
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', {})
    
    # 1. Giỏ rỗng mà vào /checkout: về /cart, flash cảnh báo
    if not cart:
        flash('Giỏ hàng của bạn đang trống. Vui lòng chọn mua sách trước khi thanh toán.', 'warning')
        return redirect(url_for('cart'))
        
    form = CheckoutForm()
    
    # Lấy thông tin chi tiết giỏ hàng để hiển thị bên phải
    cart_items = []
    subtotal = 0
    for book_id_str, quantity in cart.items():
        book = Book.query.get(int(book_id_str))
        if book:
            item_total = book.price * quantity
            subtotal += item_total
            cart_items.append({
                'book': book, 
                'quantity': quantity, 
                'item_total': item_total
            })
            
    # 2. Phí giao hàng 20.000 đ, miễn phí khi tạm tính từ 200.000 đ
    shipping_fee = 0 if subtotal >= 200000 else 20000
    total_amount = subtotal + shipping_fee
    
    # 3. Xử lý khi bấm "Xác nhận đặt hàng"
    if form.validate_on_submit():
        
        # a. Kiểm tra lại tồn kho cho tất cả sách trong giỏ
        out_of_stock_books = []
        for item in cart_items:
            if item['book'].stock < item['quantity']:
                out_of_stock_books.append(item['book'].title)
                
        # Một sách không đủ hàng: không tạo đơn, quay về giỏ, báo rõ sách nào
        if out_of_stock_books:
            books_str = ', '.join(out_of_stock_books)
            flash(f'Rất tiếc, sách "{books_str}" không đủ số lượng tồn kho. Vui lòng giảm số lượng hoặc xoá khỏi giỏ hàng.', 'danger')
            return redirect(url_for('cart'))
            
        # b. Đủ tồn kho -> Tạo Order
        new_order = Order(
            customer_name=form.fullname.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            note=form.note.data,
            payment_method=form.payment_method.data,
            shipping_fee=shipping_fee,
            total_amount=total_amount,
            status='Chờ xác nhận'
        )
        db.session.add(new_order)
        db.session.flush() # Đẩy xuống DB tạm để lấy new_order.id
        
        # c. Tạo các OrderItem, lưu đơn giá lúc đặt, trừ tồn kho
        for item in cart_items:
            book = item['book']
            qty = item['quantity']
            
            order_item = OrderItem(
                order_id=new_order.id,
                book_id=book.id,
                unit_price=book.price, # Lưu giá ngay lúc này
                quantity=qty
            )
            db.session.add(order_item)
            
            # Trừ tồn kho
            book.stock -= qty
            
        # Ghi nhận lịch sử "Chờ xác nhận"
        history = OrderHistory(order_id=new_order.id, status='Chờ xác nhận', timestamp=datetime.now())
        db.session.add(history)
        
        # Lưu tất cả vào CSDL
        db.session.commit()
        
        # d. Xoá giỏ hàng
        session.pop('cart', None)
        
        flash('Đặt hàng thành công!', 'success')
        
        # e. Chuyển sang /orders/<id> (Đảm bảo bạn có route cho customer_order_detail)
        return redirect(url_for('customer_order_detail', id=new_order.id))

    # Xử lý GET hoặc form validation fail
    return render_template('store/checkout.html', 
                           form=form, 
                           cart_items=cart_items, 
                           subtotal=subtotal, 
                           shipping_fee=shipping_fee, 
                           total_amount=total_amount)

# Route hiển thị chi tiết đơn hàng cho khách (Ví dụ)
@app.route('/orders/<int:id>')
def customer_order_detail(id):
    order = Order.query.get_or_404(id)
    return render_template('store/order_detail.html', order=order)


@app.route('/admin')
def admin_dashboard():
    total_books = db.session.query(func.count(Book.id)).scalar()
    pending_orders = db.session.query(func.count(Order.id)).filter(Order.status == 'Chờ xác nhận').scalar()
    
    current_month = datetime.now().month
    monthly_revenue = db.session.query(func.sum(Order.total_amount))\
        .filter(Order.status == 'Hoàn tất', func.extract('month', Order.created_at) == current_month).scalar() or 0
        
    low_stock = Book.query.filter(Book.stock <= 5).all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    today = datetime.now().date()
    chart_labels = []
    chart_data = []
    
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        chart_labels.append(day.strftime('%d/%m'))
        daily_total = db.session.query(func.sum(Order.total_amount)).filter(
            Order.status == 'Hoàn tất',
            func.date(Order.created_at) == day
        ).scalar() or 0
        chart_data.append(daily_total)
    
    return render_template('admin/dashboard.html', 
                           total_books=total_books, 
                           pending_orders=pending_orders, 
                           monthly_revenue=monthly_revenue, 
                           low_stock=low_stock, 
                           recent_orders=recent_orders,
                           current_month=current_month,
                           chart_labels=chart_labels,
                           chart_data=chart_data)

@app.route('/admin/books')
def admin_books():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    stock_status = request.args.get('stock', '')

    query = Book.query

    if search:
        query = query.filter(db.or_(
            Book.title.ilike(f'%{search}%'),
            Book.author.ilike(f'%{search}%')
        ))
    
    if category_id:
        query = query.filter_by(category_id=category_id)
        
    if stock_status == 'in_stock':
        query = query.filter(Book.stock > 5)
    elif stock_status == 'low_stock':
        query = query.filter(Book.stock > 0, Book.stock <= 5)
    elif stock_status == 'out_of_stock':
        query = query.filter(Book.stock == 0)

    pagination = query.order_by(Book.id.desc()).paginate(page=page, per_page=5, error_out=False)
    
    categories = Category.query.all()
    
    books_in_orders = [item.book_id for item in OrderItem.query.with_entities(OrderItem.book_id).distinct()]

    return render_template('admin/books.html', pagination=pagination, categories=categories, 
                           books_in_orders=books_in_orders)

@app.route('/admin/books/new', methods=['GET', 'POST'])
@app.route('/admin/books/<int:id>/edit', methods=['GET', 'POST'])
def admin_book_form(id=None):
    book = Book.query.get_or_404(id) if id else None
    form = BookForm(original_id=id, obj=book)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        if not book:
            book = Book()
            db.session.add(book)
            
        form.populate_obj(book)

        # Xử lý upload ảnh
        if form.image.data:
            img = form.image.data
            filename = f"{uuid.uuid4().hex}_{secure_filename(img.filename)}"
            filepath = os.path.join(app.root_path, 'static/uploads', filename)
            img.save(filepath)
            
            # Xoá ảnh cũ nếu có
            if book.image:
                old_path = os.path.join(app.root_path, 'static/uploads', book.image)
                if os.path.exists(old_path):
                    os.remove(old_path)
            book.image = filename

        db.session.commit()
        flash('Đã lưu thông tin sách thành công.', 'success')
        return redirect(url_for('admin_books'))

    return render_template('admin/book_form.html', form=form, book=book)

@app.route('/admin/books/<int:id>/delete', methods=['POST'])
def admin_delete_book(id):
    book = Book.query.get_or_404(id)
    
    if OrderItem.query.filter_by(book_id=id).first():
        flash(f'Lỗi: Không thể xoá "{book.title}" vì đã có trong đơn hàng.', 'danger')
        return redirect(url_for('admin_books'))
        
    if book.image:
        old_path = os.path.join(app.root_path, 'static/uploads', book.image)
        if os.path.exists(old_path):
            os.remove(old_path)
            
    db.session.delete(book)
    db.session.commit()
    flash(f'Đã xoá sách "{book.title}".', 'success')
    return redirect(url_for('admin_books'))

@app.route('/admin/categories', methods=['GET', 'POST'])
def admin_categories():
    edit_id = request.args.get('edit_id', type=int)
    edit_category = Category.query.get(edit_id) if edit_id else None
    form = CategoryForm(obj=edit_category)
    
    if form.validate_on_submit():
        existing = Category.query.filter(func.lower(Category.name) == func.lower(form.name.data)).first()
        if existing and (not edit_category or existing.id != edit_category.id):
            flash('Danh mục đã tồn tại.', 'danger')
        else:
            if not edit_category:
                edit_category = Category()
                db.session.add(edit_category)
            edit_category.name = form.name.data
            db.session.commit()
            flash('Đã lưu danh mục.', 'success')
            return redirect(url_for('admin_categories'))
            
    categories = db.session.query(
        Category.id, Category.name, func.count(Book.id).label('book_count')
    ).outerjoin(Book).group_by(Category.id).all()
    
    return render_template('admin/categories.html', categories=categories, form=form, edit_category=edit_category)

@app.route('/admin/categories/<int:id>/delete', methods=['POST'])
def admin_delete_category(id):
    category = Category.query.get_or_404(id)
    if category.books:
        flash(f'Không thể xoá "{category.name}": còn {len(category.books)} sách.', 'danger')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Đã xoá danh mục.', 'success')
    return redirect(url_for('admin_categories'))

@app.route('/admin/orders')
def admin_orders():
    status = request.args.get('status')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)

    query = Order.query

    # Tab trạng thái
    if status:
        query = query.filter_by(status=status)
        
    # Tìm kiếm mã đơn, tên, sđt
    if search:
        # Xử lý tìm theo mã đơn (nếu search có dấu # hoặc là số)
        search_id = search.replace('#', '')
        if search_id.isdigit():
             query = query.filter(
                 db.or_(
                     Order.id == int(search_id),
                     Order.customer_name.ilike(f'%{search}%'),
                     Order.phone.ilike(f'%{search}%')
                 )
             )
        else:
             query = query.filter(
                 db.or_(
                     Order.customer_name.ilike(f'%{search}%'),
                     Order.phone.ilike(f'%{search}%')
                 )
             )

    # Phân trang, mới nhất trước
    pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=10, error_out=False)

    # Truy vấn group by lấy số lượng mỗi trạng thái
    status_counts_query = db.session.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    status_counts = dict(status_counts_query)
    total_orders = Order.query.count()

    # Tính tổng giá trị của bộ lọc hiện tại
    total_filtered_value = sum([o.total_amount for o in pagination.items])

    return render_template('admin/orders.html', 
                           pagination=pagination, 
                           status_counts=status_counts, 
                           total_orders=total_orders,
                           current_status=status,
                           total_filtered_value=total_filtered_value)


@app.route('/admin/orders/<int:id>', methods=['GET', 'POST'])
def admin_order_detail(id):
    order = Order.query.get_or_404(id)
    
    # Lấy các tuỳ chọn trạng thái tiếp theo hợp lệ
    next_statuses = []
    if order.status == 'Chờ xác nhận':
        next_statuses = ['Đang giao']
    elif order.status == 'Đang giao':
        next_statuses = ['Hoàn tất']

    if request.method == 'POST':
        action = request.form.get('action')
        new_status = None

        if action == 'update':
            new_status = request.form.get('new_status')
            if new_status not in next_statuses:
                flash('Trạng thái chuyển đổi không hợp lệ.', 'danger')
                return redirect(url_for('admin_order_detail', id=order.id))
                
        elif action == 'cancel':
            if order.status in ['Chờ xác nhận', 'Đang giao']:
                new_status = 'Đã huỷ'
                # Hoàn lại tồn kho
                for item in order.items:
                    item.book.stock += item.quantity
            else:
                flash('Không thể huỷ đơn hàng ở trạng thái này.', 'danger')
                return redirect(url_for('admin_order_detail', id=order.id))

        if new_status:
            order.status = new_status
            
            # Ghi lại lịch sử
            history = OrderHistory(order_id=order.id, status=new_status, timestamp=datetime.now())
            db.session.add(history)
            
            db.session.commit()
            flash(f'Đã cập nhật trạng thái đơn hàng thành "{new_status}".', 'success')
            
        return redirect(url_for('admin_order_detail', id=order.id))

    return render_template('admin/order_detail.html', order=order, next_statuses=next_statuses)
@app.context_processor
def inject_admin_badges():
    pending_count = Order.query.filter_by(status='Chờ xác nhận').count()
    return dict(pending_count=pending_count)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)