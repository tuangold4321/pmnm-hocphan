import sys

sys.dont_write_bytecode = True

from flask import Flask, render_template

from bmi_routes import bmi_bp
from diem_hp_routes import diem_hp_bp
from may_tinh_routes import may_tinh_bp

app = Flask(__name__)
app.register_blueprint(bmi_bp, url_prefix="/bmi")
app.register_blueprint(diem_hp_bp, url_prefix="/diem-hp")
app.register_blueprint(may_tinh_bp, url_prefix="/may-tinh")

@app.route('/')
def home():
    return render_template('tinh_toan.html')

if __name__ == '__main__':
    app.run(debug=True)