from flask import Blueprint, render_template, request

bmi_bp = Blueprint("bmi", __name__)


@bmi_bp.route("/", methods=["GET", "POST"], strict_slashes=False)
def index():
    height_raw = ""
    weight_raw = ""
    errors = {}
    result = None

    if request.method == "POST":
        height_raw = request.form.get("height", "").strip()
        weight_raw = request.form.get("weight", "").strip()

        height_val = None
        weight_val = None
        if not height_raw:
            errors["height"] = "Vui lòng nhập chiều cao."
        else:
            try:
                height_val = float(height_raw.replace(",", "."))
                if height_val < 50 or height_val > 250:
                    errors["height"] = "Giá trị phải từ 50 đến 250."
            except ValueError:
                errors["height"] = "Vui lòng nhập một số."

        if not weight_raw:
            errors["weight"] = "Vui lòng nhập cân nặng."
        else:
            try:
                weight_val = float(weight_raw.replace(",", "."))
                if weight_val < 10 or weight_val > 300:
                    errors["weight"] = "Giá trị phải từ 10 đến 300."
            except ValueError:
                errors["weight"] = "Vui lòng nhập một số."

        if not errors and height_val is not None and weight_val is not None:
            height_m = height_val / 100
            bmi = round(weight_val / (height_m**2), 1)

            if bmi < 18.5:
                category, color_name, css_class = "Thiếu cân", "vàng", "yellow"
            elif bmi < 23:
                category, color_name, css_class = "Bình thường", "xanh", "green"
            elif bmi < 25:
                category, color_name, css_class = "Thừa cân", "vàng", "yellow"
            else:
                category, color_name, css_class = "Béo phì", "đỏ", "red"

            result = {
                "bmi": bmi,
                "category": category,
                "color_name": color_name,
                "css_class": css_class,
                "weight_min": round(18.5 * height_m**2, 1),
                "weight_max": round(22.9 * height_m**2, 1),
            }

    return render_template(
        "bmi/index.html",
        height_raw=height_raw,
        weight_raw=weight_raw,
        errors=errors,
        result=result,
    )
