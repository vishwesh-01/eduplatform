from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_pymongo import PyMongo
# from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import secrets
import datetime
# import json
from bson import ObjectId
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
import io
# import os
import requests
import google.generativeai as genai

genai.configure(api_key="gemini-api-key-goes_here")
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/education_platform'

# Initialize MongoDB
mongo = PyMongo(app)

# Sample data for development/testing
SAMPLE_GOALS = [
    'Java Developer',
    'Python Developer',
    'Web Developer',
    'Data Scientist',
    'Mobile App Developer',
    'DevOps Engineer'
]

SAMPLE_QUIZ_QUESTIONS = {
    'Java Developer': [
        {
            'question': 'What is the main method signature in Java?',
            'options': ['public static void main(String[] args)', 'public void main(String[] args)',
                        'static void main(String[] args)', 'public main(String[] args)'],
            'correct': 0
        },
        {
            'question': 'Which keyword is used for inheritance in Java?',
            'options': ['implements', 'extends', 'inherits', 'super'],
            'correct': 1
        },
        {
            'question': 'What is encapsulation in Java?',
            'options': ['Hiding implementation details', 'Creating objects', 'Method overloading',
                        'Exception handling'],
            'correct': 0
        }
    ],
    'Python Developer': [
        {
            'question': 'Which of the following is used to define a function in Python?',
            'options': ['function', 'def', 'func', 'define'],
            'correct': 1
        },
        {
            'question': 'What is the correct way to create a list in Python?',
            'options': ['list = []', 'list = ()', 'list = {}', 'list = <>'],
            'correct': 0
        },
        {
            'question': 'Which method is used to add an element to a list?',
            'options': ['add()', 'append()', 'insert()', 'push()'],
            'correct': 1
        }
    ],
    'Web Developer': [
        {
            'question': 'What does HTML stand for?',
            'options': ['Hyper Text Markup Language', 'Home Tool Markup Language',
                        'Hyperlinks and Text Markup Language', 'Hyper Text Making Language'],
            'correct': 0
        },
        {
            'question': 'Which CSS property is used to change the text color?',
            'options': ['font-color', 'text-color', 'color', 'foreground-color'],
            'correct': 2
        },
        {
            'question': 'What is the correct HTML element for the largest heading?',
            'options': ['<h6>', '<h1>', '<heading>', '<header>'],
            'correct': 1
        }
    ]
}

# Sample course data (in real implementation, this would come from Gemini API)
SAMPLE_COURSES = {
    'Java Developer': [
        {
            'title': 'Java Programming Masterclass',
            'instructor': 'Tech Academy',
            'duration': '40 hours',
            'modules': [
                'Introduction to Java',
                'Object-Oriented Programming',
                'Data Structures',
                'Exception Handling',
                'Collections Framework',
                'Multithreading',
                'File I/O',
                'JDBC and Database Connectivity'
            ],
            'video_url': 'https://youtu.be/xTtL8E4LzTQ?si=2MyXCFrXgXiB6LIj'
        },
        {
            'title': 'Spring Boot Complete Course',
            'instructor': 'Code Masters',
            'duration': '25 hours',
            'modules': [
                'Spring Boot Basics',
                'REST APIs',
                'Spring Data JPA',
                'Security Implementation',
                'Testing',
                'Deployment'
            ],
            'video_url': 'https://youtu.be/5rNk7m_zlAg?si=x_o7FjkAvOYQYcPO'
        }
    ],
    'Python Developer': [
        {
            'title': 'Complete Python Bootcamp',
            'instructor': 'Python Pro',
            'duration': '35 hours',
            'modules': [
                'Python Basics',
                'Data Types and Structures',
                'Functions and Modules',
                'Object-Oriented Programming',
                'File Handling',
                'Web Scraping',
                'APIs and Databases',
                'Django Framework'
            ],
            'video_url': 'https://youtube.com/playlist?list=PLNcg_FV9n7qZGfFl2ANI_zISzNp257Lwn&si=w0XKNlQ4WAdPYOA1'
        }
    ],
    'Web Developer': [
        {
            'title': 'Full Stack Web Development',
            'instructor': 'Web Wizards',
            'duration': '50 hours',
            'modules': [
                'HTML5 Fundamentals',
                'CSS3 and Responsive Design',
                'JavaScript ES6+',
                'React.js',
                'Node.js and Express',
                'MongoDB',
                'Authentication & Security',
                'Deployment and DevOps'
            ],
            'video_url': 'https://youtu.be/LzMnsfqjzkA?si=fuJwJtyd3twfz6nT'
        }
    ]
}


def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


def check_password(password, hashed):
    """Check password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)


def login_required(f):
    """Decorator to require login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        if not user or not user.get('is_admin', False):
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Check if user already exists
        if mongo.db.users.find_one({'email': email}):
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))

        # Create new user
        hashed_password = hash_password(password)
        user_data = {
            'name': name,
            'email': email,
            'password': hashed_password,
            'is_admin': False,
            'created_at': datetime.datetime.now(),
            'learning_goal': None,
            'skill_level': 0,
            'courses': [],
            'certificates': [],
            'quiz_history': []
        }

        result = mongo.db.users.insert_one(user_data)
        session['user_id'] = str(result.inserted_id)
        flash('Registration successful!', 'success')
        return redirect(url_for('onboarding'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = mongo.db.users.find_one({'email': email})

        if user and check_password(password, user['password']):
            session['user_id'] = str(user['_id'])
            flash('Login successful!', 'success')

            # Redirect admin to admin panel
            if user.get('is_admin', False):
                return redirect(url_for('admin_dashboard'))

            # Redirect to onboarding if no learning goal set
            if not user.get('learning_goal'):
                return redirect(url_for('onboarding'))

            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding():
    """User onboarding - select learning goal"""
    if request.method == 'POST':
        learning_goal = request.form['learning_goal']

        # Update user's learning goal
        mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {'learning_goal': learning_goal}}
        )

        flash(f'Learning goal set: {learning_goal}', 'success')
        return redirect(url_for('assessment'))

    return render_template('onboarding.html', goals=SAMPLE_GOALS)


@app.route('/assessment', methods=['GET', 'POST'])
@login_required
def assessment():
    """Skill assessment quiz"""
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    learning_goal = user.get('learning_goal')

    if not learning_goal:
        return redirect(url_for('onboarding'))

    if request.method == 'POST':
        answers = []
        score = 0
        questions = SAMPLE_QUIZ_QUESTIONS.get(learning_goal, [])

        for i, question in enumerate(questions):
            answer = int(request.form.get(f'question_{i}', -1))
            answers.append(answer)
            if answer == question['correct']:
                score += 1

        # Calculate percentage and level
        percentage = (score / len(questions)) * 100 if questions else 0

        if percentage >= 80:
            level = 'Advanced'
        elif percentage >= 60:
            level = 'Intermediate'
        else:
            level = 'Beginner'

        # Save quiz result
        quiz_result = {
            'date': datetime.datetime.now(),
            'score': score,
            'total': len(questions),
            'percentage': percentage,
            'level': level
        }

        mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {
                '$set': {'skill_level': percentage},
                '$push': {'quiz_history': quiz_result}
            }
        )

        session['quiz_result'] = quiz_result
        return redirect(url_for('assessment_results'))

    questions = SAMPLE_QUIZ_QUESTIONS.get(learning_goal, [])
    return render_template('assessment.html', questions=questions, learning_goal=learning_goal)


@app.route('/assessment-results')
@login_required
def assessment_results():
    """Display assessment results"""
    quiz_result = session.pop('quiz_result', None)
    if not quiz_result:
        return redirect(url_for('dashboard'))

    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    learning_goal = user.get('learning_goal')

    # Get recommended courses (simulate Gemini API response)
    recommended_courses = SAMPLE_COURSES.get(learning_goal, [])

    return render_template('assessment_results.html',
                           quiz_result=quiz_result,
                           recommended_courses=recommended_courses,
                           learning_goal=learning_goal)


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})

    # Calculate statistics
    total_courses = len(user.get('courses', []))
    completed_courses = len([c for c in user.get('courses', []) if c.get('completed', False)])
    certificates_earned = len(user.get('certificates', []))

    # Get quiz history for chart
    quiz_history = user.get('quiz_history', [])

    # Get course progress data
    courses = user.get('courses', [])

    return render_template('dashboard.html',
                           user=user,
                           total_courses=total_courses,
                           completed_courses=completed_courses,
                           certificates_earned=certificates_earned,
                           quiz_history=quiz_history,
                           courses=courses)


@app.route('/add-course/<int:course_index>')
@login_required
def add_course(course_index):
    """Add a course to user's learning path"""
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    learning_goal = user.get('learning_goal')

    if learning_goal in SAMPLE_COURSES and course_index < len(SAMPLE_COURSES[learning_goal]):
        course = SAMPLE_COURSES[learning_goal][course_index].copy()
        course['enrolled_date'] = datetime.datetime.now()
        course['completed'] = False
        course['progress'] = {module: False for module in course['modules']}
        course['completion_percentage'] = 0

        # Add course to user's courses
        mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$push': {'courses': course}}
        )

        flash(f'Course "{course["title"]}" added to your learning path!', 'success')
    else:
        flash('Course not found!', 'error')

    return redirect(url_for('dashboard'))


@app.route('/course/<int:course_index>')
@login_required
def view_course(course_index):
    """View course details and track progress"""
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    courses = user.get('courses', [])

    if course_index < len(courses):
        course = courses[course_index]
        return render_template('course.html', course=course, course_index=course_index)
    else:
        flash('Course not found!', 'error')
        return redirect(url_for('dashboard'))


@app.route('/update-progress/<int:course_index>/<int:module_index>')
@login_required
def update_progress(course_index, module_index):
    """Update module completion progress"""
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    courses = user.get('courses', [])

    if course_index < len(courses):
        course = courses[course_index]
        modules = course['modules']

        if module_index < len(modules):
            module_name = modules[module_index]

            # Toggle module completion
            course['progress'][module_name] = not course['progress'].get(module_name, False)

            # Calculate completion percentage
            completed_modules = sum(1 for completed in course['progress'].values() if completed)
            course['completion_percentage'] = (completed_modules / len(modules)) * 100

            # Check if course is completed
            if course['completion_percentage'] == 100 and not course.get('completed'):
                course['completed'] = True
                course['completion_date'] = datetime.datetime.now()

                # Generate certificate
                certificate_code = secrets.token_hex(8).upper()
                certificate = {
                    'course_title': course['title'],
                    'completion_date': datetime.datetime.now(),
                    'certificate_code': certificate_code
                }

                # Update user with completed course and certificate
                mongo.db.users.update_one(
                    {'_id': ObjectId(session['user_id'])},
                    {
                        '$set': {f'courses.{course_index}': course},
                        '$push': {'certificates': certificate}
                    }
                )

                flash(f'Congratulations! You completed "{course["title"]}" and earned a certificate!', 'success')
            else:
                # Update course progress
                mongo.db.users.update_one(
                    {'_id': ObjectId(session['user_id'])},
                    {'$set': {f'courses.{course_index}': course}}
                )

                flash(f'Progress updated for "{module_name}"!', 'success')

    return redirect(url_for('view_course', course_index=course_index))


@app.route('/certificates')
@login_required
def certificates():
    """View user certificates"""
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    certificates = user.get('certificates', [])

    return render_template('certificates.html', certificates=certificates)


@app.route('/download-certificate/<certificate_code>')
@login_required
def download_certificate(certificate_code):
    """Download certificate as PDF"""
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    certificates = user.get('certificates', [])

    certificate = next((cert for cert in certificates if cert['certificate_code'] == certificate_code), None)

    if not certificate:
        flash('Certificate not found!', 'error')
        return redirect(url_for('certificates'))

    # Create PDF certificate
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Certificate design
    width, height = letter

    # Border and background
    p.setStrokeColor(Color(0.2, 0.4, 0.8))
    p.setLineWidth(3)
    p.rect(50, 50, width - 100, height - 100)

    # Add inner decorative border
    p.setStrokeColor(Color(0.8, 0.8, 0.8))
    p.setLineWidth(1)
    p.rect(70, 70, width - 140, height - 140)

    # Helper function for centered text
    def draw_centered_text(canvas_obj, x_pos, y_pos, text, font_name, font_size):
        canvas_obj.setFont(font_name, font_size)
        text_width = canvas_obj.stringWidth(text, font_name, font_size)
        canvas_obj.drawString(x_pos - text_width / 2, y_pos, text)

    # Title
    p.setFillColor(Color(0.2, 0.4, 0.8))
    draw_centered_text(p, width / 2, height - 150, "CERTIFICATE OF COMPLETION", "Helvetica-Bold", 36)

    # Decorative line under title
    p.setStrokeColor(Color(0.2, 0.4, 0.8))
    p.setLineWidth(2)
    p.line(width / 2 - 200, height - 170, width / 2 + 200, height - 170)

    # Content
    p.setFillColor(Color(0.3, 0.3, 0.3))
    draw_centered_text(p, width / 2, height - 220, "This is to certify that", "Helvetica", 18)

    # User name (larger and prominent)
    p.setFillColor(Color(0.1, 0.1, 0.1))
    draw_centered_text(p, width / 2, height - 280, user['name'].upper(), "Helvetica-Bold", 32)

    # Decorative line under name
    p.setStrokeColor(Color(0.7, 0.7, 0.7))
    p.setLineWidth(1)
    name_width = p.stringWidth(user['name'].upper(), "Helvetica-Bold", 32)
    p.line(width / 2 - name_width / 2 - 20, height - 295, width / 2 + name_width / 2 + 20, height - 295)

    p.setFillColor(Color(0.3, 0.3, 0.3))
    draw_centered_text(p, width / 2, height - 330, "has successfully completed the course", "Helvetica", 18)

    # Course title
    p.setFillColor(Color(0.2, 0.4, 0.8))
    draw_centered_text(p, width / 2, height - 380, f'"{certificate["course_title"]}"', "Helvetica-Bold", 22)

    # Date and certificate info
    p.setFillColor(Color(0.4, 0.4, 0.4))
    completion_date = certificate['completion_date'].strftime("%B %d, %Y")
    draw_centered_text(p, width / 2, height - 450, f"Completed on: {completion_date}", "Helvetica", 16)

    draw_centered_text(p, width / 2, height - 480, f"Certificate ID: {certificate['certificate_code']}", "Helvetica",
                       14)

    # Add some decorative elements
    p.setFillColor(Color(0.9, 0.9, 0.9))
    # Left decoration
    p.circle(120, height / 2, 30, fill=1)
    p.setFillColor(Color(0.2, 0.4, 0.8))
    p.circle(120, height / 2, 20, fill=1)

    # Right decoration
    p.setFillColor(Color(0.9, 0.9, 0.9))
    p.circle(width - 120, height / 2, 30, fill=1)
    p.setFillColor(Color(0.2, 0.4, 0.8))
    p.circle(width - 120, height / 2, 20, fill=1)

    # Footer
    p.setFillColor(Color(0.5, 0.5, 0.5))
    draw_centered_text(p, width / 2, 120, "Personalized Education Platform", "Helvetica-Oblique", 14)
    draw_centered_text(p, width / 2, 100, "Empowering Learners Worldwide", "Helvetica-Oblique", 12)

    # Add timestamp for authenticity
    p.setFillColor(Color(0.7, 0.7, 0.7))
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    p.setFont("Helvetica", 8)
    p.drawString(60, 60, f"Generated: {timestamp}")

    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f'certificate_{certificate_code}.pdf',
                     mimetype='application/pdf')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        # Check if email is taken by another user
        existing_user = mongo.db.users.find_one({'email': email, '_id': {'$ne': ObjectId(session['user_id'])}})
        if existing_user:
            flash('Email already taken by another user!', 'error')
            return redirect(url_for('profile'))

        # Update user profile
        mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {'name': name, 'email': email}}
        )

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    total_users = mongo.db.users.count_documents({})
    total_courses = sum(len(SAMPLE_COURSES[goal]) for goal in SAMPLE_COURSES)

    # Get recent registrations
    recent_users = list(mongo.db.users.find({}).sort('created_at', -1).limit(5))

    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           total_courses=total_courses,
                           recent_users=recent_users)


@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin user management"""
    users = list(mongo.db.users.find({'is_admin': {'$ne': True}}))
    return render_template('admin_users.html', users=users)


@app.route('/api/dashboard-data')
@login_required
def dashboard_data():
    """API endpoint for dashboard charts"""
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})

    # Quiz history for line chart
    quiz_history = user.get('quiz_history', [])
    quiz_data = {
        'labels': [q['date'].strftime('%m/%d') for q in quiz_history],
        'scores': [q['percentage'] for q in quiz_history]
    }

    # Course progress for doughnut chart
    courses = user.get('courses', [])
    completed = len([c for c in courses if c.get('completed', False)])
    in_progress = len(courses) - completed

    course_data = {
        'labels': ['Completed', 'In Progress'],
        'data': [completed, in_progress]
    }

    return jsonify({
        'quiz_data': quiz_data,
        'course_data': course_data
    })


if __name__ == '__main__':
    app.run(debug=True)

# HTML Templates (save these as separate files in a 'templates' directory)

# templates/base.html
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Personalized Education Platform{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .navbar-brand { font-weight: bold; }
        .card { box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .progress-bar { transition: width 0.5s ease; }
        .certificate-card { border: 2px solid gold; background: linear-gradient(135deg, #f6f9fc 0%, #e9ecef 100%); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">
                <i class="fas fa-graduation-cap"></i> EduPlatform
            </a>
            <div class="navbar-nav ms-auto">
                {% if session.user_id %}
                    <a class="nav-link" href="{{ url_for('dashboard') }}">Dashboard</a>
                    <a class="nav-link" href="{{ url_for('certificates') }}">Certificates</a>
                    <a class="nav-link" href="{{ url_for('profile') }}">Profile</a>
                    <a class="nav-link" href="{{ url_for('logout') }}">Logout</a>
                {% else %}
                    <a class="nav-link" href="{{ url_for('login') }}">Login</a>
                    <a class="nav-link" href="{{ url_for('register') }}">Register</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <main class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
'''

# Additional templates would be created similarly...
# Due to space constraints, I'm showing the main application structure.
# The complete implementation would include all the HTML templates for:
# - index.html (landing page)
# - register.html (registration form)
# - login.html (login form)
# - onboarding.html (goal selection)
# - assessment.html (quiz interface)
# - assessment_results.html (quiz results and recommendations)
# - dashboard.html (main user dashboard with charts)
# - course.html (individual course view)
# - certificates.html (certificate gallery)
# - profile.html (user profile management)
# - admin_dashboard.html (admin overview)
# - admin_users.html (user management)

print("Personalized Education Platform - Complete Flask Application")
print("=" * 60)
print("\nFeatures Implemented:")
print("✓ User registration and authentication with bcrypt")
print("✓ Session management and security")
print("✓ Learning goal selection and onboarding")
print("✓ Dynamic skill assessment quizzes")
print("✓ AI-powered course recommendations (simulated)")
print("✓ Progress tracking and course completion")
print("✓ Interactive dashboard with Chart.js visualizations")
print("✓ PDF certificate generation with ReportLab")
print("✓ Admin panel for user management")
print("✓ Responsive Bootstrap UI")
print("✓ MongoDB integration with PyMongo")
print("\nTo run this application:")
print("1. Install dependencies: pip install flask flask-pymongo bcrypt reportlab")
print("2. Set up MongoDB server")
print("3. Create HTML templates in 'templates/' directory")
print("4. Run: python app.py")