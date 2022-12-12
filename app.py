from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Unauthorized

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "123abcd"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)

@app.route('/')
def home_page():
    return redirect('/register')


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """FILL THE FORM TO REGISTER IF YOU ARE NEW USER"""
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            #IF username is duplicated, use another username to register
            form.username.errors.append('Username taken.  Please pick another')
            return render_template('register.html', form=form)
        session['username'] = new_user.username
        flash('Welcome! Successfully Created Your Account!', "success")
        return redirect(f"/users/{new_user.username}")

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if "username" in session:
        return redirect(f"/users/{session['username']}")
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.username}!", "primary")
            session['username'] = user.username
            return redirect('/users/{user.username}')
        else:
            form.username.errors = ['Invalid username/password.']
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)


@app.route('/users/<username>')
def show_user(username):
    """Show username if user logined"""
    if "username" not in session or username != session['username']:
        raise Unauthorized()
    user = User.query.get(username)
    return render_template("users_show.html", user=user)


@app.route('/logout')
def logout_user():
    session.pop('username')
    flash("Goodbye!", "info")
    return redirect('/')


@app.route('/users/<username>/delete', methods = ['POST'])
def delete_user(username):
    if "username" not in session or username != session['username']:
        raise Unauthorized()

    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop("username")

    return redirect("/login")

@app.route('/users/<username>/feedback/add', methods =['GET', 'POST'])
def add_feedback(username):
    if "username" not in session or username != session['username']:
        raise Unauthorized()

    form = FeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        feedback = Feedback(title= title, content=content, username = username)
        db.session.add(feedback)
        db.session.commit()
        return redirect(f"/users/{feedback.username}")
    else:
        return render_template("feedback_new.html", form=form)

@app.route('/feedback/<int:feedback_id>/update', methods = ['GET', 'POST'])
def update_feedback(feedback_id):
    
    feedback = Feedback.query.get(feedback_id)
    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()
    form = FeedbackForm(obj=feedback)
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    return render_template("feedback_edit.html", form=form, feedback=feedback)

@app.route('/feedback/<int:feedback_id>/delete', methods= ['POST'])
def delete_feedback(feedback_id):
    """delete feeback of logined user"""
    feedback = Feedback.query.get(feedback_id)
    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()

    feedback = Feedback.query.get_or_404(feedback_id)
    if feedback.username == session['username']:
        db.session.delete(feedback)
        db.session.commit()
        flash("Feedback deleted!", "info")
        return redirect(f'/users/{feedback.username}')
    flash("You don't have permission to do that!", "danger")
    return redirect(f"/users/{feedback.username}")
    



    