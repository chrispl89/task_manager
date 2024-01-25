from flask import Flask, render_template, url_for, request, redirect, session, abort, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt


app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = "SUP3R_Classif1ed"
app.config['SESSION_PERMANENT'] = False
db = SQLAlchemy(app)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(255))
    complete = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    author = db.Column(db.String(50))
    assigned_to = db.Column(db.String(50))

    def __init__(self, title, description, complete=False, deadline=None, author=None, assigned_to=None):
        self.title = title
        self.description = description
        self.complete = complete
        self.deadline = deadline
        self.author = author
        self.assigned_to = assigned_to


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

    def update_password(self, new_password):
        self.password = bcrypt.generate_password_hash(new_password).decode('utf-8')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already taken. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


def create_tables():
    with app.app_context():
        db.create_all()


if not app.config.get('tables_created'):
    create_tables()
    app.config['tables_created'] = True


@app.route("/", methods=['GET', 'POST'])
def home():
    if 'loggedin' in session and session['loggedin']:
        if request.method == 'POST':
            task_title = request.form['title']
            task_description = request.form['description']
            new_todo = Todo(title=task_title, description=task_description, complete=False)

            try:
                db.session.add(new_todo)
                db.session.commit()
                return redirect('/')
            except:
                return 'There was an issue adding your task'
        else:
            tasks = Todo.query.order_by(Todo.created_at).all()
            return render_template('base.html', tasks=tasks)
    else:
        abort(401)


@app.route("/add", methods=["POST"])
def add():
    if 'loggedin' not in session:
        abort(401)

    title = request.form.get("title")
    description = request.form.get("description")
    deadline_str = request.form.get("deadline")
    author = request.form.get("author")
    assigned_to = request.form.get("assigned_to")

    try:
        deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M') if deadline_str else None
    except ValueError:
        deadline = None

    new_todo = Todo(
        title=title,
        description=description,
        complete=False,
        deadline=deadline,
        author=author,
        assigned_to=assigned_to
    )

    try:
        db.session.add(new_todo)
        db.session.commit()
        return redirect(url_for("home"))
    except Exception as e:
        print(f"Error adding task: {e}")
        db.session.rollback()
        return 'There was an issue adding your task'


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    if 'loggedin' not in session:
        abort(401)

    task = Todo.query.get_or_404(id)

    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        task.complete = 'complete' in request.form
        db.session.commit()
        return redirect('/')
    else:
        return render_template('update.html', task=task)


@app.route("/delete/<int:id>")
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting that task'


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Account already exists!', 'error')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, password=hashed_password, email=email)
            db.session.add(new_user)
            db.session.commit()
            flash('You have successfully registered!', 'success')
            return redirect(url_for("login"))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['loggedin'] = True
            session['id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for("home"))
        else:
            flash('Incorrect username/password!', 'error')

    return render_template('login.html', form=form)


app.config['PROPAGATE_EXCEPTIONS'] = True
if __name__ == "__main__":
    app.run(debug=True)

