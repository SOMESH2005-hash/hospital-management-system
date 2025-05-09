from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, logout_user, login_required, LoginManager, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql

# Initialize Flask App
app = Flask(__name__)
app.secret_key = 'hmsprojects'

# Database Configuration (Set MySQL Password)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:2005@localhost/hosptial'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Flask-Login Configuration
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    usertype = db.Column(db.String(50))  # Patient or Doctor
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(1000))

class Patients(db.Model):
    pid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50))
    name = db.Column(db.String(50))
    gender = db.Column(db.String(50))
    slot = db.Column(db.String(50))
    disease = db.Column(db.String(50))
    time = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    dept = db.Column(db.String(50))
    number = db.Column(db.String(50))

class Doctors(db.Model):
    did = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50))
    doctorname = db.Column(db.String(50))
    dept = db.Column(db.String(50))

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Doctor Registration
@app.route('/doctors', methods=['POST', 'GET'])
def doctors():
    if request.method == "POST":
        email = request.form.get('email')
        doctorname = request.form.get('doctorname')
        dept = request.form.get('dept')
        
        doctor = Doctors(email=email, doctorname=doctorname, dept=dept)
        db.session.add(doctor)
        db.session.commit()
        flash("Doctor Added Successfully", "success")

    return render_template('doctor.html')

# Patient Booking
@app.route('/patients', methods=['POST', 'GET'])
@login_required
def patient():
    doct = Doctors.query.all()
    if request.method == "POST":
        email = request.form.get('email')
        name = request.form.get('name')
        gender = request.form.get('gender')
        slot = request.form.get('slot')
        disease = request.form.get('disease')
        time = request.form.get('time')
        date = request.form.get('date')
        dept = request.form.get('dept')
        number = request.form.get('number')

        if len(number) != 10:
            flash("Please enter a valid 10-digit phone number", "warning")
            return render_template('patient.html', doct=doct)

        query = Patients(email=email, name=name, gender=gender, slot=slot, disease=disease, time=time, date=date, dept=dept, number=number)
        db.session.add(query)
        db.session.commit()
        flash("Appointment Booked Successfully", "success")

    return render_template('patient.html', doct=doct)

# View Bookings
@app.route('/bookings')
@login_required
def bookings():
    em = current_user.email
    if current_user.usertype == "Doctor":
        query = Patients.query.all()
    else:
        query = Patients.query.filter_by(email=em)

    return render_template('booking.html', query=query)

# Edit Booking
@app.route("/edit/<string:pid>", methods=['POST', 'GET'])
@login_required
def edit(pid):
    post = Patients.query.filter_by(pid=pid).first()
    if request.method == "POST":
        post.email = request.form.get('email')
        post.name = request.form.get('name')
        post.gender = request.form.get('gender')
        post.slot = request.form.get('slot')
        post.disease = request.form.get('disease')
        post.time = request.form.get('time')
        post.date = request.form.get('date')
        post.dept = request.form.get('dept')
        post.number = request.form.get('number')

        db.session.commit()
        flash("Appointment Updated Successfully", "success")
        return redirect('/bookings')

    return render_template('edit.html', posts=post)

# Delete Booking
@app.route("/delete/<string:pid>", methods=['POST', 'GET'])
@login_required
def delete(pid):
    query = Patients.query.filter_by(pid=pid).first()
    db.session.delete(query)
    db.session.commit()
    flash("Appointment Deleted Successfully", "danger")
    return redirect('/bookings')

# Signup
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        usertype = request.form.get('usertype')
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email Already Exists", "warning")
            return render_template('signup.html')

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, usertype=usertype, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Signup Successful! Please Login.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

# Login
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login Successful", "primary")
            return redirect(url_for('index'))
        else:
            flash("Invalid Credentials", "danger")
            return render_template('login.html')

    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged Out Successfully", "warning")
    return redirect(url_for('login'))

# Test Database Connection
@app.route('/test_db')
def test_db():
    try:
        db.session.execute('SELECT 1')  # Test query
        return "Database Connected Successfully!"
    except Exception as e:
        return f"Database Connection Failed: {str(e)}"

# Search Doctor
@app.route('/search', methods=['POST', 'GET'])
@login_required
def search():
    if request.method == "POST":
        query = request.form.get('search')
        doctor = Doctors.query.filter((Doctors.dept == query) | (Doctors.doctorname == query)).first()
        
        if doctor:
            flash("Doctor is Available", "info")
        else:
            flash("Doctor Not Found", "danger")

    return render_template('index.html')

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
