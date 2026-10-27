
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    Regexp,
    EqualTo,
    InputRequired
)


class RegisterForm(FlaskForm):
    username = StringField(
        "Tên đăng nhập",
        validators=[
            DataRequired(message="Vui lòng nhập tên đăng nhập."),
            Length(
                min=4,
                max=20,
                message="Tên đăng nhập phải từ 4 đến 20 ký tự."
            ),
            Regexp(
                r"^[a-z0-9_]+$",
                message=(
                    "Tên đăng nhập chỉ được chứa chữ thường "
                    "không dấu, số và dấu gạch dưới (_)."
                )
            )
        ]
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Vui lòng nhập email."),
            Email(message="Email không đúng định dạng.")
        ]
    )

    password = PasswordField(
        "Mật khẩu",
        validators=[
            DataRequired(message="Vui lòng nhập mật khẩu."),
            Length(
                min=8,
                message="Mật khẩu tối thiểu 8 ký tự."
            )
        ]
    )

    confirm_password = PasswordField(
        "Nhập lại mật khẩu",
        validators=[
            DataRequired(
                message="Vui lòng nhập lại mật khẩu."
            ),
            EqualTo(
                "password",
                message="Mật khẩu nhập lại không khớp."
            )
        ]
    )

    agree = BooleanField(
        "Tôi đồng ý với điều khoản sử dụng",
        validators=[
            DataRequired(
                message="Bạn phải đồng ý với điều khoản."
            )
        ]
    )

    submit = SubmitField("Đăng ký")
