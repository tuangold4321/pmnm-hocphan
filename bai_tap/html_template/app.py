from datetime import date

from flask import Flask, render_template

app = Flask(__name__, template_folder="templates", static_folder="static")

POSTS = [
    {"id": 1, "title": "Bài viết 1"},
]


@app.route("/")
@app.route("/hello/<name>")
def hello(name="Tuấn"):
    return render_template("hello.html", name=name)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.context_processor
def inject_globals():
    return {
        "site_name": "Nguyễn Đình Tuấn",
        "current_year": date.today().year,
        "post_count": len(POSTS),
    }


if __name__ == "__main__":
    app.run(debug=True)
