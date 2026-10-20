import math
from flask import Flask, render_template, request

app = Flask(__name__)

valid_ops = {"+", "-", "*", "/"}


def parse_number(raw):
    raw = (raw or "").strip().replace(",", ".")

    if not raw:
        return None

    try:
        value = float(raw)
    except ValueError:
        return None

    if not math.isfinite(value):
        return None

    return value


def format_number(x):
    x = round(x, 10)
    if x == int(x):
        return str(int(x))
    return str(x)


@app.route("/", methods=["GET", "POST"])
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

        if op not in valid_ops:
            errors["op"] = (f"Phép toán '{op}' không hợp lệ. ")

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
        "index.html",
        a=a_raw,
        b=b_raw,
        op=op,
        errors=errors,
        result=result,
        ops=["+", "-", "*", "/"]
    )


if __name__ == "__main__":
    app.run(debug=True)