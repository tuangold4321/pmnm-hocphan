from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Blueprint, render_template, request

diem_hp_bp = Blueprint("diem_hp", __name__)

FIELDS = [
    ("cc", "Chuyên cần (10%)", "CC", Decimal("0.1")),
    ("gk", "Giữa kỳ (30%)", "GK", Decimal("0.3")),
    ("ck", "Cuối kỳ (60%)", "CK", Decimal("0.6")),
]


def validate_score(raw):
    raw = (raw or "").strip().replace(",", ".")
    if not raw:
        return None, "Vui lòng nhập một số."

    try:
        value = Decimal(raw)
    except InvalidOperation:
        return None, "Vui lòng nhập một số."

    if not value.is_finite():
        return None, "Vui lòng nhập một số."
    if value < 0 or value > 10:
        return None, "Điểm phải từ 0 đến 10."
    return value, None


def to_letter(score):
    if score >= Decimal("8.5"):
        return "A"
    if score >= Decimal("7.0"):
        return "B"
    if score >= Decimal("5.5"):
        return "C"
    if score >= Decimal("4.0"):
        return "D"
    return "F"


@diem_hp_bp.route("/", methods=["GET", "POST"], strict_slashes=False)
def index():
    values = {key: "" for key, *_ in FIELDS}
    errors = {}
    result = None

    if request.method == "POST":
        scores = {}
        for key, _label, _short, _weight in FIELDS:
            values[key] = request.form.get(key, "")
            score, error = validate_score(values[key])
            if error:
                errors[key] = error
            else:
                scores[key] = score

        if not errors:
            total = sum(
                scores[key] * weight for key, _label, _short, weight in FIELDS
            )
            total = total.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            fatal = scores["ck"] < 1
            result = {
                "score": total,
                "letter": "F" if fatal else to_letter(total),
                "fatal": fatal,
            }

    return render_template(
        "diem_hp/index.html",
        fields=FIELDS,
        values=values,
        errors=errors,
        result=result,
    )
