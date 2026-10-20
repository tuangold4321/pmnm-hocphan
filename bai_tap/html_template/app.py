import sys
import os
from flask import Flask, render_template

# Đảm bảo Python nhận diện được các thư mục anh em
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import các Blueprint từ 3 thư mục con
from bmi.app import bmi_bp
from diem_hp.app import diem_hp_bp
from may_tinh.may_tinh import may_tinh_bp

app = Flask(__name__)

# Đăng ký Blueprints với prefix đường dẫn riêng biệt
app.register_blueprint(bmi_bp, url_prefix='/bmi')
app.register_blueprint(diem_hp_bp, url_prefix='/diem-hp')
app.register_blueprint(may_tinh_bp, url_prefix='/may-tinh')

# các route giao diện chính
@app.route('/')
def hello():
    return render_template('hello.html')

# ROUTE TRANG LỰA CHỌN 3 BÀI TÍNH TOÁN
@app.route('/tinh-toan')
def tinh_toan():
    return render_template('tinh_toan.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)