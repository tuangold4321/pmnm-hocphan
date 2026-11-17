from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import StringField, IntegerField, TextAreaField, SelectField, FloatField, SubmitField, RadioField
from wtforms.validators import DataRequired, Email, NumberRange, Optional, Regexp, ValidationError
from datetime import datetime
from sqlalchemy import func
from models import Book

class CheckoutForm(FlaskForm):
    fullname = StringField('Họ tên *', validators=[
        DataRequired(message='Vui lòng nhập họ tên')
    ])
    
    phone = StringField('Số điện thoại *', validators=[
        DataRequired(message='Vui lòng nhập số điện thoại'),
        # Kiểm tra bắt đầu bằng 0 và theo sau là 9 chữ số
        Regexp(r'^0\d{9}$', message='Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0.')
    ])
    
    email = StringField('Email', validators=[
        Optional(), 
        Email(message='Email không hợp lệ')
    ])
    
    address = TextAreaField('Địa chỉ giao hàng *', validators=[
        DataRequired(message='Vui lòng nhập địa chỉ')
    ])
    
    note = StringField('Ghi chú')
    
    payment_method = RadioField('Thanh toán *', choices=[
        ('cod', 'Tiền mặt khi nhận hàng'),
        ('transfer', 'Chuyển khoản')
    ], default='cod', validators=[DataRequired(message='Vui lòng chọn phương thức thanh toán')])

class BookForm(FlaskForm):
    title = StringField('Tên sách *', validators=[DataRequired(message='Vui lòng nhập tên sách')])
    author = StringField('Tác giả *', validators=[DataRequired(message='Vui lòng nhập tác giả')])
    category_id = SelectField('Danh mục *', coerce=int, validators=[DataRequired()])
    publish_year = IntegerField('Năm xuất bản', validators=[
        NumberRange(min=1900, max=datetime.now().year, message=f'Năm từ 1900 - {datetime.now().year}')
    ])
    price = FloatField('Giá (đồng) *', validators=[
        DataRequired(), 
        NumberRange(min=1000, message='Giá phải từ 1.000đ trở lên')
    ])
    stock = IntegerField('Tồn kho *', validators=[
        DataRequired(), 
        NumberRange(min=0, message='Tồn kho không âm.')
    ])
    description = TextAreaField('Mô tả')
    image = FileField('Ảnh bìa', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Chỉ hỗ trợ định dạng JPG, PNG, WEBP'),
        FileSize(max_size=2 * 1024 * 1024, message='Kích thước ảnh tối đa 2 MB')
    ])

    def __init__(self, original_id=None, *args, **kwargs):
        super(BookForm, self).__init__(*args, **kwargs)
        self.original_id = original_id

    # Kiểm tra tên sách không trùng (bỏ qua khoảng trắng, không phân biệt hoa thường)
    def validate_title(self, field):
        query = Book.query.filter(func.lower(Book.title) == func.lower(field.data.strip()))
        if self.original_id:
            query = query.filter(Book.id != self.original_id)
        if query.first():
            raise ValidationError('Tên sách này đã tồn tại.')

class CategoryForm(FlaskForm):
    name = StringField('Tên danh mục', validators=[DataRequired()])
    submit = SubmitField('Lưu')