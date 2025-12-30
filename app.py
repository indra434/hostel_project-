from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3, os, uuid
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "hostel_secret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists("database.db"):
        conn = sqlite3.connect("database.db")
        with open("database.sql", "r") as f:
            conn.executescript(f.read())

        users = [
            ("admin", "admin123", "admin"),
            ("student1", "student123", "student"),
            ("principal1", "principal123", "principal"),
            ("warden1", "warden123", "warden"),
            ("guardian1", "guardian123", "guardian"),
        ]

        for u, p, r in users:
            conn.execute(
                "INSERT INTO users(username,password,role) VALUES (?,?,?)",
                (u, generate_password_hash(p), r)
            )

        conn.commit()
        conn.close()
        print("✅ Database created with default users")

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=?",(u,)
        ).fetchone()
        db.close()

        if user and check_password_hash(user["password"], p):
            session["uid"] = user["id"]
            session["role"] = user["role"]
            return redirect(url_for(user["role"]))

        flash("Invalid credentials")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    if session.get("role") != "admin": return redirect("/")
    c = get_db()
    return render_template(
        "admin_dashboard.html",
        colleges=c.execute("SELECT * FROM colleges").fetchall(),
        hostels=c.execute("SELECT * FROM hostels").fetchall()
    )

@app.route("/admin/add_college", methods=["POST"])
def add_college():
    c = get_db()
    c.execute("INSERT INTO colleges(name) VALUES(?)",(request.form["name"],))
    c.commit()
    return redirect("/admin")

@app.route("/admin/add_hostel", methods=["POST"])
def add_hostel():
    c = get_db()
    rooms = int(request.form["rooms"])
    c.execute("""
        INSERT INTO hostels(name,college,total_rooms,available_rooms)
        VALUES (?,?,?,?)
    """,(request.form["name"],request.form["college"],rooms,rooms))
    c.commit()
    return redirect("/admin")

# ---------------- STUDENT ----------------
@app.route("/student")
def student():
    if session.get("role") != "student": return redirect("/")
    c = get_db()
    return render_template(
        "student_dashboard.html",
        hostels=c.execute("SELECT * FROM hostels").fetchall(),
        photos=c.execute("SELECT * FROM room_photos").fetchall()
    )

@app.route("/student/apply/<int:hid>", methods=["POST"])
def student_apply(hid):
    f = request.files["document"]
    filename = secure_filename(f.filename)
    newname = f"{uuid.uuid4().hex}_{filename}"
    f.save(os.path.join(UPLOAD_FOLDER, newname))

    c = get_db()
    c.execute("""
        INSERT INTO applications(student_id,hostel_id,document)
        VALUES (?,?,?)
    """,(session["uid"], hid, newname))
    c.commit()
    return redirect("/student")

# ---------------- PRINCIPAL ----------------
@app.route("/principal")
def principal():
    if session.get("role") != "principal": return redirect("/")
    apps = get_db().execute("""
        SELECT a.id,u.username,h.name,a.document
        FROM applications a
        JOIN users u ON a.student_id=u.id
        JOIN hostels h ON a.hostel_id=h.id
        WHERE a.status='pending'
    """).fetchall()
    return render_template("principal_dashboard.html", apps=apps)

@app.route("/principal/approve/<int:id>")
def approve(id):
    c = get_db()
    c.execute("UPDATE applications SET status='approved' WHERE id=?", (id,))
    c.execute("""
        UPDATE hostels SET available_rooms=available_rooms-1
        WHERE id=(SELECT hostel_id FROM applications WHERE id=?)
    """,(id,))
    c.commit()
    return redirect("/principal")

@app.route("/principal/reject/<int:id>")
def reject(id):
    c = get_db()
    c.execute("UPDATE applications SET status='rejected' WHERE id=?", (id,))
    c.commit()
    return redirect("/principal")

# ---------------- WARDEN ----------------
@app.route("/warden")
def warden():
    if session.get("role") != "warden": return redirect("/")
    c = get_db()
    return render_template(
        "warden_dashboard.html",
        students=c.execute("SELECT * FROM users WHERE role='student'").fetchall(),
        attendance=c.execute("SELECT * FROM attendance").fetchall()
    )

@app.route("/warden/attendance", methods=["POST"])
def mark_attendance():
    c = get_db()
    c.execute("""
        INSERT INTO attendance(student_id,date,status)
        VALUES (?,?,?)
    """,(request.form["student"],request.form["date"],request.form["status"]))
    c.commit()
    return redirect("/warden")

@app.route("/warden/photo", methods=["POST"])
def room_photo():
    f = request.files["photo"]
    name = secure_filename(f.filename)
    new = f"{uuid.uuid4().hex}_{name}"
    f.save(os.path.join(UPLOAD_FOLDER,new))
    c = get_db()
    c.execute("INSERT INTO room_photos(filename) VALUES(?)",(new,))
    c.commit()
    return redirect("/warden")

# ---------------- GUARDIAN ----------------
@app.route("/guardian")
def guardian():
    if session.get("role") != "guardian": return redirect("/")
    return render_template(
        "guardian_dashboard.html",
        attendance=get_db().execute("""
            SELECT u.username,a.date,a.status
            FROM attendance a
            JOIN users u ON a.student_id=u.id
        """).fetchall()
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)