from flask import Flask, request, jsonify, url_for

app = Flask(__name__)

STUDENTS = {
    "23T1020001": {"name": "Nguyễn Văn An", "lop": "K47A", "scores": {"PMNM": 8.5, "CSDL": 7.0, "MTK": 9.0}},
    "23T1020002": {"name": "Trần Thị Bình", "lop": "K47A", "scores": {"PMNM": 6.0, "CSDL": 5.5, "MTK": 7.0}},
    "23T1020003": {"name": "Lê Hoàng Cường", "lop": "K47B", "scores": {"PMNM": 9.5, "CSDL": 9.0}},
    "23T1020004": {"name": "Phạm Minh Dũng", "lop": "K47B", "scores": {"PMNM": 4.0, "CSDL": 3.5, "MTK": 5.0}},
    "23T1020005": {"name": "Hoàng Thu Hà", "lop": "K47A", "scores": {}},
    "23T1020006": {"name": "Võ Quốc Khánh", "lop": "K47C", "scores": {"PMNM": 7.5, "MTK": 8.0}},
}

def get_avg_and_rank(scores):
    """Tính điểm trung bình và xếp loại"""
    if not scores:
        return "-", "-"
    
    avg = round(sum(scores.values()) / len(scores), 2)
    
    if avg >= 8.5: rank = "Giỏi"
    elif avg >= 7.0: rank = "Khá"
    elif avg >= 5.5: rank = "Trung bình"
    elif avg >= 4.0: rank = "Yếu"
    else: rank = "Kém"
        
    return avg, rank

@app.route('/')
def index():
    total_students = len(STUDENTS)
    unique_classes = len(set(s['lop'] for s in STUDENTS.values()))
    
    # Tạo liên kết bằng url_for
    students_url = url_for('students')
    api_url = url_for('api_students')
    
    return f"""
    TRANG CHỦ<br>
    Tổng số sinh viên: {total_students}<br>
    Số lớp: {unique_classes}<br><br>
    <a href="{students_url}">Xem danh sách sinh viên</a><br>
    <a href="{api_url}">Xem dữ liệu API</a>
    """

@app.route('/students')
def students():
    # Lấy danh sách lớp động từ dữ liệu và sắp xếp
    all_classes = sorted(list(set(s['lop'] for s in STUDENTS.values())))
    lop_filter = request.args.get('lop', '').strip().upper()
    
    # Tạo thanh lọc động bằng url_for
    # url_for('students') -> /students
    # url_for('students', lop=c) -> /students?lop=K47A
    filters = [f'<a href="{url_for("students")}">Tất cả</a>']
    for c in all_classes:
        filters.append(f'<a href="{url_for("students", lop=c)}">{c}</a>')
        
    filter_bar = " | ".join(filters)
    
    # Lọc dữ liệu
    result_lines = []
    for mssv, info in STUDENTS.items():
        if not lop_filter or info['lop'].upper() == lop_filter:
            avg, rank = get_avg_and_rank(info['scores'])
            # Định dạng thành chuỗi văn bản thay vì bảng HTML
            line = f"MSSV: {mssv} - Họ tên: {info['name']} - Lớp: {info['lop']} - ĐTB: {avg} - Xếp loại: {rank}"
            result_lines.append(line)
            
    # Xử lý hiển thị kết quả
    if not result_lines:
        content = "Không có sinh viên phù hợp"
    else:
        content = "<br>".join(result_lines)
        
    home_url = url_for('index')
    
    return f"""
    DANH SÁCH SINH VIÊN<br>
    {filter_bar}<br><br>
    
    {content}<br><br>
    
    <a href="{home_url}">Trở về trang chủ</a>
    """

@app.route('/api/students')
def api_students():
    return jsonify(STUDENTS)

if __name__ == '__main__':
    app.run(debug=True)