from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(255))
    complete = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    author = db.Column(db.String(50))  # Dodane pole 'author'
    assigned_to = db.Column(db.String(50))  # Dodane pole 'assigned_to'

    def __init__(self, title, description, complete=False, deadline=None, author=None, assigned_to=None):
        self.title = title
        self.description = description
        self.complete = complete
        self.deadline = deadline
        self.author = author
        self.assigned_to = assigned_to


def create_tables():
    with app.app_context():
        db.create_all()


if not app.config.get('tables_created'):
    create_tables()
    app.config['tables_created'] = True


@app.route("/", methods=['GET', 'POST'])
def home():
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


@app.route("/add", methods=["POST"])
def add():
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
    task = Todo.query.get_or_404(id)

    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        # Ustawienie wartości complete w zależności od formularza (np. checkbox)
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


if __name__ == "__main__":
    app.run(debug=True)
