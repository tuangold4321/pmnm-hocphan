from flask import Flask, request, jsonify, url_for, abort, redirect, make_response, render_template
from datetime import date
import io
import csv

app = Flask(__name__)

STUDENTS = {
    "23T1020001": {"name": "Nguyễn Văn An", "lop": "K47A", "scores": {"PMNM": 8.5, "CSDL": 7.0, "MTK": 9.0}},
    "23T1020002": {"name": "Trần Thị Bình", "lop": "K47A", "scores": {"PMNM": 6.0, "CSDL": 5.5, "MTK": 7.0}},
    "23T1020003": {"name": "Lê Hoàng Cường", "lop": "K47B", "scores": {"PMNM": 9.5, "CSDL": 9.0}},
    "23T1020004": {"name": "Phạm Minh Dũng", "lop": "K47B", "scores": {"PMNM": 4.0, "CSDL": 3.5, "MTK": 5.0}},
    "23T1020005": {"name": "Hoàng Thu Hà", "lop": "K47A", "scores": {}},
    "23T1020006": {"name": "Võ Quốc Khánh", "lop": "K47C", "scores": {"PMNM": 7.5, "MTK": 8.0}},
}

# Custom Jinja2 filter registration
@app.template_filter('format_avg')
def format_avg_filter(scores_list):
    if not scores_list:
        return "-"
    return f"{sum(scores_list) / len(scores_list):.2f}"

def get_avg_and_rank(scores):
    """Tính điểm trung bình và xếp loại"""
    if not scores or len(scores) == 0:
        return "-", "-"
    
    avg = round(sum(scores.values()) / len(scores), 2)
    
    if avg >= 8.5: rank = "Giỏi"
    elif avg >= 7.0: rank = "Khá"
    elif avg >= 5.5: rank = "Trung bình"
    elif avg >= 4.0: rank = "Yếu"
    else: rank = "Kém"
        
    return avg, rank

@app.route('/')
@app.route('/hello/<name>')
def hello(name="Tuấn"):
    skills = ["python", "flask", "jinja2", "html/css"]
    return render_template(
        "hello.html", 
        name=name, 
        skills=skills, 
        students=STUDENTS
    )

@app.route('/students')
def students():
    all_classes = sorted(list(set(s['lop'] for s in STUDENTS.values())))
    lop_filter = request.args.get('lop', '').strip().upper()
    
    filters = [f'<a href="{url_for("students")}">Tất cả</a>']
    for c in all_classes:
        filters.append(f'<a href="{url_for("students", lop=c)}">{c}</a>')
        
    filter_bar = " | ".join(filters)
    
    result_lines = []
    for mssv, info in STUDENTS.items():
        if not lop_filter or info['lop'].upper() == lop_filter:
            avg, rank = get_avg_and_rank(info['scores'])
            sv_url = url_for('redirect_sv', mssv=mssv)
            line = f"MSSV: <a href='{sv_url}'>{mssv}</a> - Họ tên: {info['name']} - Lớp: {info['lop']} - ĐTB: {avg} - Xếp loại: {rank}"
            result_lines.append(line)
            
    content = "<br>".join(result_lines) if result_lines else "Không có sinh viên phù hợp"
        
    return f"""
    DANH SÁCH SINH VIÊN<br>
    {filter_bar}<br><br>
    {content}<br><br>
    <a href="{url_for('search')}">Tìm kiếm sinh viên</a> | <a href="{url_for('hello')}">Trở về trang chủ</a>
    """

@app.route('/sv/<mssv>')
def redirect_sv(mssv):
    return redirect(url_for('student_detail', mssv=mssv), code=301)

@app.route('/students/<mssv>')
def student_detail(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    
    info = STUDENTS[mssv]
    avg, rank = get_avg_and_rank(info['scores'])
    class_url = url_for('students', lop=info['lop'])
    export_url = url_for('export_student_csv', mssv=mssv)
    
    scores = info.get('scores', {})
    if not scores:
        score_html = "Chưa có điểm"
    else:
        score_html = "<br>".join([f"- {subject}: {score}" for subject, score in scores.items()])
        
    return f"""
    CHI TIẾT SINH VIÊN<br>
    MSSV: {mssv}<br>
    Họ tên: {info['name']}<br>
    Lớp: <a href="{class_url}">{info['lop']}</a><br>
    Điểm TB: {avg}<br>
    Xếp loại: {rank}<br><br>
    BẢNG ĐIỂM TỪNG HỌC PHẦN:<br>
    {score_html}<br><br>
    <a href="{export_url}">Tải bảng điểm (CSV)</a><br><br>
    <a href="{url_for('students')}">Trở về danh sách tổng</a> | <a href="{url_for('hello')}">Về trang chủ</a>
    """

@app.route('/students/<mssv>/export')
def export_student_csv(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
        
    scores = STUDENTS[mssv].get('scores', {})
    
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(["hoc_phan", "diem"])
    for subject, score in scores.items():
        writer.writerow([subject, score])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=diem_{mssv}.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    results = []
    
    if query:
        query_lower = query.lower()
        for mssv, info in STUDENTS.items():
            if query_lower in mssv.lower() or query_lower in info['name'].lower():
                sv_url = url_for('redirect_sv', mssv=mssv)
                results.append(f"MSSV: <a href='{sv_url}'>{mssv}</a> - Họ tên: {info['name']} ({info['lop']})")

    search_form = f"""
    <form action="{url_for('search')}" method="get">
        <input type="text" name="q" value="{query}" placeholder="Nhập MSSV hoặc Họ tên...">
        <button type="submit">Tìm kiếm</button>
    </form>
    """
    
    if not query:
        result_html = ""
    elif results:
        count_str = f"Tìm thấy {len(results)} kết quả cho \"{query}\":<br><br>"
        result_html = count_str + "<br>".join(results)
    else:
        result_html = f"Tìm thấy 0 kết quả cho \"{query}\""
        
    return f"""
    TÌM KIẾM SINH VIÊN<br><br>
    {search_form}<br>
    {result_html}<br><br>
    <a href="{url_for('students')}">Trở về danh sách</a> | <a href="{url_for('hello')}">Về trang chủ</a>
    """

@app.errorhandler(404)
def page_not_found(e):
    error_message = e.description if hasattr(e, 'description') and e.description else "Trang không tồn tại"
    return error_message, 404

@app.route('/api/students')
def api_students():
    return jsonify(STUDENTS)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

POSTS = [
    {"id": 1, "title": "Bài viết 1"},
]

@app.context_processor
def inject_globals():
    return {
        "site_name": "Nguyễn Đình Tuấn",
        "current_year": date.today().year,
        "post_count": len(POSTS),
    }

if __name__ == '__main__':
    app.run(debug=True)