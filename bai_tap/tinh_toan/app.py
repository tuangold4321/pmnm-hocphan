import sys

sys.dont_write_bytecode = True

from datetime import timedelta
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, func
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

from bmi_routes import bmi_bp
from diem_hp_routes import diem_hp_bp
from may_tinh_routes import may_tinh_bp
from forms import RegisterForm


app = Flask(__name__)

app.config["SECRET_KEY"] = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = \
    "sqlite:///qlsv.db"
db.init_app(app)

class Student(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    mssv: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    gpa: Mapped[float] = mapped_column(default=0.0)
    def __repr__(self):
        return f"<Student {self.mssv} {self.name}>"
with app.app_context():
    db.create_all()

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


USERS = {
    "an": "an123456",
    "binh": "binh123456"
}

@app.get("/them-mau")
def add_sample():
    total = db.session.scalar(db.select(func.count(Student.id)))
    if total > 0:
        return f"Đã có {total} sinh viên, không thêm nữa."
    an = Student(mssv="23T1020001", name="Nguyễn Văn An", gpa=8.5)
    before = an.id
    db.session.add(an)
    db.session.add_all([
        Student(mssv="23T1020002", name="Trần Thị Bình", gpa=6.8),
        Student(mssv="23T1020003", name="Lê Hoàng Cường", gpa=9.1),
        Student(mssv="23T1020004", name="Phạm Minh Dũng", gpa=4.5),
        Student(mssv="23T1020005", name="Hoàng Thu Hà", gpa=7.4),
    ])
    db.session.commit()
    return (f"Đã thêm 5 sinh viên id của An: "
            f"Trước commit = {before}, "
            f"Sau commit = {an.id}")

app.register_blueprint(bmi_bp, url_prefix="/bmi")
app.register_blueprint(diem_hp_bp, url_prefix="/diem-hp")
app.register_blueprint(may_tinh_bp, url_prefix="/may-tinh")


PROTECTED_BLUEPRINTS = {
    bmi_bp.name,
    diem_hp_bp.name,
    may_tinh_bp.name
}



@app.before_request
def check_login():
    if request.endpoint in ("login", "register", "static"):
        return None

    if request.blueprint in PROTECTED_BLUEPRINTS:
        if "user" not in session:
            flash("Vui lòng đăng nhập...", "error")
            return redirect(url_for("login"))

    if request.endpoint == "profile":
        if "user" not in session:
            flash("Vui lòng đăng nhập...", "error")
            return redirect(url_for("login"))

    return None


@app.route("/")
def home():
    return render_template("base.html")


@app.route("/tinh-toan")
def tinh_toan():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "tinh_toan.html",
        username=session["user"]
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect(url_for("home"))

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()

        if username in USERS:
            form.username.errors.append(
                "Tên đăng nhập đã được sử dụng."
            )

        else:
            USERS[username] = form.password.data

            flash("Đăng ký thành công!", "success")
            return redirect(url_for("login"))

    return render_template(
        "register.html",
        form=form
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("home"))

    username = ""

    if request.method == "POST":
        username = request.form.get(
            "username", ""
        ).strip()

        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        if username in USERS and USERS[username] == password:
            session.clear()
            session["user"] = username
            session["login_success_message"] = (
                f"Đăng nhập thành công. Xin chào {username}!"
            )
            session.permanent = remember

            return redirect(url_for("home"))

        flash(
            "Sai tên đăng nhập hoặc mật khẩu!",
            "error"
        )

    return render_template(
        "login.html",
        username=username
    )


@app.route("/profile")
def profile():
    return render_template(
        "profile.html",
        username=session["user"]
    )


@app.route("/logout", methods=["POST"])
def logout():
    if "user" not in session:
        flash("Vui lòng đăng nhập...", "error")
        return redirect(url_for("login"))

    session.clear()

    flash("Bạn đã đăng xuất!", "success")

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
