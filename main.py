#서버 코드 파일

from flask import Flask, request, session, render_template, jsonify, send_file
import psycopg2
from file import save_to_csv

app = Flask("StudyRoom")
app.config['SECRET_KEY'] = '1234'

conn = psycopg2.connect(
    database = 'japanese',
    user = 'db2024',
    password = '1234',
    host = '::1',
    port = '5432',
    client_encoding='UTF8'
)
cursor = conn.cursor()

@app.route("/")
def home():
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    if not user:
        return jsonify({"success": False, "error": "Invalid username or password"})
    
    user_id = user[0]
    user_role = user[3]
    session['user_id'] = user_id
    
    if user_role == "student":
        return jsonify({"success": True, "redirect_url": "/student_home"})
    elif user_role == "teacher":
        return jsonify({"success": True, "redirect_url": "/teacher_home"})
    elif user_role == "parents":
        return jsonify({"success": True, "redirect_url": "/child_status"})
        
@app.route('/student_home')
def student_home():
    return render_template("home.html")

@app.route('/teacher_home')
def teacher_home():
    return render_template("course_enroll.html")

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    child_name = data.get('child_name') if role == 'parents' else None
    
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()

    if result is not None:
        return jsonify({"success": False, "error": "이미 사용 중인 아이디입니다."})
    
    cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
    conn.commit()
    
    if role == "parents":
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        parent = cursor.fetchone()
        parent_id = parent[0]
        cursor.execute("SELECT id FROM users WHERE username = %s", (child_name,))
        child = cursor.fetchone()
        child_id = child[0]
        
        cursor.execute("INSERT INTO parents (parent_id, child_id) VALUES (%s, %s)", (parent_id, child_id))
        conn.commit()
    return jsonify({"success": True})

@app.route('/japanese')
def japanese():
    return render_template("japanese.html")

@app.route('/japanese_level', methods=['POST'])
def japanese_level():
    id = session.get('user_id')
    level = request.form.get('level')
    cursor.execute("SELECT * FROM kanji WHERE level = %s", (level,))
    result = cursor.fetchall()
    cursor.execute("SELECT * FROM courses")
    result2 = cursor.fetchall()
    
    return render_template("japanese_level.html", level=level, words=result, courses=result2, id=id)

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    row_id = data.get("master")
    row_kanji = data.get("kanji")
    row_kor = data.get("kor")
    row_meaning = data.get("meaning")
    row_on = data.get("on")
    row_kun = data.get("kun")

    sqlq = """
            INSERT INTO japanese_workbook(masterid, kanji, korean_onkun, meaning, on_yomi, kun_yomi)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
    try:
        cursor.execute(sqlq, (row_id, row_kanji, row_kor, row_meaning, row_on, row_kun))
        conn.commit()
        return jsonify({"message": "Success"})
    except Exception as e:
        return jsonify({"message": str(e)})

@app.route("/app_course", methods=["POST"])
def app_course():
    student_id = session.get('user_id')
    course_id = request.json.get('course_id')
    cursor.execute("SELECT * FROM enrollments WHERE student_id = %s and course_id = %s", (student_id, course_id))
    result = cursor.fetchone()
    
    if result is None:
        try:
            cursor.execute("SELECT * FROM courses WHERE cid = %s", (course_id,))
            result = cursor.fetchone()
            print(result[4] >= result[2])
            if result[4] >= result[2]:
                raise Exception()
            cursor.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
            cursor.execute("UPDATE courses SET current = current + 1 WHERE cid = %s", (course_id,))
            conn.commit()
            return jsonify({"success": True})
        except Exception:
            return jsonify({"success": False, "error": "수강 제한인원이 초과되었습니다"})
        
    else:
        return jsonify({"success": False, "error": "이미 신청한 강의입니다"})
    
@app.route('/my_workbook')
def my_workbook():
    id = session.get('user_id')
    cursor.execute("SELECT * FROM japanese_workbook WHERE masterid = %s", (id,))
    result = cursor.fetchall()
    return render_template("my_workbook.html", my_words=result)

@app.route('/export')
def export():
    id = session.get('user_id')
    cursor.execute("SELECT * FROM japanese_workbook WHERE masterid = %s", (id,))
    result = cursor.fetchall()
    save_to_csv(result)
    return send_file("word.csv", as_attachment=True)

    
@app.route('/enroll_course', methods=['POST'])
def enroll_course():
    try:
        data = request.get_json()
        id = session.get('user_id')
        course_name = data['coursename']
        capacity = data['capacity']
        language = data['language']

        cursor.execute("INSERT INTO courses (tid, course_name, capacity, language) VALUES (%s, %s, %s, %s)", (id, course_name, capacity, language))
        conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        print(e)
        return jsonify({"success": False})

@app.route('/my_course')
def my_course():
    id = session.get('user_id')
    cursor.execute("SELECT role FROM users WHERE id = %s", (id,))
    result = cursor.fetchone()
    if result[0] == "teacher":
        cursor.execute("SELECT * FROM courses WHERE tid = %s", (id,))
        result = cursor.fetchall()
        return render_template("my_course.html", my_courses=result)
    else:
        cursor.execute("""SELECT DISTINCT c.* 
                       FROM courses c JOIN enrollments e ON c.cid = e.course_id
                       WHERE e.student_id = %s;""", (id,))
        result = cursor.fetchall()
        print(result)
        return render_template("my_course.html", my_courses=result)
    
@app.route('/my_student')
def my_student():
    teacher_id = session.get('user_id')
    cursor.execute("SELECT c.cid, c.course_name FROM courses c WHERE c.tid = %s", (teacher_id,))
    courses = cursor.fetchall()
    student_info_by_course = {}

    for course in courses:
        course_id = course[0]
        cursor.execute("""
            SELECT u.username
            FROM users u
            JOIN enrollments e ON u.id = e.student_id
            WHERE e.course_id = %s
        """, (course_id,))
        students = cursor.fetchall()
        student_info_by_course[course_id] = students

    return render_template("my_student.html", courses=courses, student_info_by_course=student_info_by_course, id=teacher_id)
    
@app.route('/child_status')
def child_status():
    id = session.get('user_id')
    cursor.execute("SELECT child_id FROM parents WHERE parent_id = %s", (id,))
    result = cursor.fetchone()
    child_id = result[0]
    
    cursor.execute("""SELECT DISTINCT c.* 
                       FROM courses c JOIN enrollments e ON c.cid = e.course_id
                       WHERE e.student_id = %s;""", (child_id,))
    result_courses = cursor.fetchall()
    
    cursor.execute("SELECT * FROM japanese_workbook WHERE masterid = %s", (child_id,))
    result_words = cursor.fetchall()
    word_num = len(result_words)
    
    cursor.execute("""
            SELECT f.* 
            FROM feedback f
            JOIN users u ON f.student_name = u.username
            WHERE u.id = %s
        """, (child_id,))
    result_feedbacks = cursor.fetchall()
    
    return render_template("child_status.html", 
                           child_courses=result_courses,
                           word_num = word_num,
                           child_words=result_words,
                           child_feedbacks=result_feedbacks)
    
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    feedback_data = data.get('dataToSend', {})
    
    teacher_id = feedback_data.get('teacherId')
    course_name = feedback_data.get('courseName')
    student_name = feedback_data.get('studentName')
    feedback = feedback_data.get('feedbackText')

    cursor.execute("""
        INSERT INTO feedback (tid, course_name, student_name, feedback_content) 
        VALUES (%s, %s, %s, %s)
    """, (teacher_id, course_name, student_name, feedback))
    conn.commit()

    return jsonify({"success": True})

app.run(debug=True)