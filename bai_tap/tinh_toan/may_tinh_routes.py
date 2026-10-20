import math

from flask import Blueprint, render_template, request

may_tinh_bp = Blueprint("may_tinh", __name__)

VALID_OPS = {"+", "-", "*", "/"}


def parse_number(raw):
    raw = (raw or "").strip().replace(",", ".")
    if not raw:
        return None

    try:
        value = float(raw)
    except ValueError:
        return None

    return value if math.isfinite(value) else None


def format_number(value):
    value = round(value, 10)
    if value == int(value):
        return str(int(value))
    return str(value)


@may_tinh_bp.route("/", methods=["GET", "POST"], strict_slashes=False)
def calculator():
    a_raw = ""
    b_raw = ""
    op = "*"
    errors = {}
    result = None

    if request.method == "POST":
        a_raw = request.form.get("a", "")
        b_raw = request.form.get("b", "")
        op = request.form.get("op", "")

        a = parse_number(a_raw)
        b = parse_number(b_raw)

        if a is None:
            errors["a"] = "Vui lòng nhập số hợp lệ."
        if b is None:
            errors["b"] = "Vui lòng nhập số hợp lệ."
        if op not in VALID_OPS:
            errors["op"] = f"Phép toán '{op}' không hợp lệ."
        if not errors and op == "/" and b == 0:
            errors["b"] = "Không thể chia cho 0."

        if not errors:
            if op == "+":
                value = a + b
            elif op == "-":
                value = a - b
            elif op == "*":
                value = a * b
            else:
                value = a / b

            result = (
                f"{format_number(a)} {op} "
                f"{format_number(b)} = {format_number(value)}"
            )

    return render_template(
        "may_tinh/index.html",
        a=a_raw,
        b=b_raw,
        op=op,
        errors=errors,
        result=result,
        ops=["+", "-", "*", "/"],
    )
