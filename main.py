import flask
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterUserForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
from functools import wraps
import os

from email_manager import EmailManager

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap(app)

# Manage Database:
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Manage Users:
login_manager = LoginManager()
login_manager.init_app(app)
gravatar = Gravatar(app, size=100)


@login_manager.user_loader
def user_loader(user_id):
    return db.session.get(User, user_id)


# Tables:
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.mapped_column(db.ForeignKey('users.id'))
    author = relationship('User', back_populates='posts')  # This is now a User object

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    # Comments relationship
    post_comments = relationship('Comment', back_populates='post')  # This is now given to the comment?
    @hybrid_property
    def author_name(self):
        return self.author.name


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False, unique=True)
    password = db.Column(db.String(250), nullable=False)

    # Relationship
    posts = relationship('BlogPost', back_populates='author')
    user_comments = relationship('Comment', back_populates='user')


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)

    user_id = db.mapped_column(db.ForeignKey('users.id'))
    user = relationship('User', back_populates='user_comments')

    post_id = db.mapped_column(db.ForeignKey('blog_posts.id'))
    post = relationship('BlogPost', back_populates='post_comments')  # Comment is now a property of a BlogPost object


with app.app_context():
    db.create_all()


# Admin checker
def admin_only(fn):
    @wraps(fn)
    def check_admin(*args, **kwargs):
        if current_user.is_anonymous:
            return flask.abort(403)  # TODO Clean this up
        elif current_user.id == 1:
            return fn(*args, **kwargs)
        else:
            return flask.abort(403)
    return check_admin


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterUserForm()
    if request.method == 'POST' and form.validate_on_submit():
        if not db.session.query(User, User.email).filter_by(email=request.form['email']).first():
            try:
                new_user = User()
                new_user.name = request.form['name']
                new_user.email = request.form['email']
                new_user.password = generate_password_hash(password=request.form['password'],
                                                           method='pbkdf2:sha256',
                                                           salt_length=8)
            except KeyError:
                flask.flash('One or more fields were missing or incorrect.')
                return render_template('register.html', form=form)
            else:
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                flask.flash('Successfully registered! You are logged in now.')
                return redirect(url_for('get_all_posts'))
        flask.flash('A user with that email already exists!')
        return redirect(url_for('register'))
    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=request.form['email']).first()
        if user:
            if check_password_hash(pwhash=user.password, password=request.form['password']):
                login_user(user)
                flask.flash(f'Successfully logged in, {user.name}!')
                return redirect(url_for('get_all_posts'))
            flask.flash('Password was incorrect.')
            return redirect(url_for('login'))
        flask.flash('No user was found with that email')
        return redirect(url_for('login'))
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    flask.flash('Successfully logged out.')
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    comment_form = CommentForm()
    requested_post = BlogPost.query.filter_by(id=post_id).first()
    if request.method == 'POST':
        if current_user.is_anonymous:
            flask.flash('You need to be logged in to post a comment!')
            return redirect(url_for('login'))
        print("Validated the comment submission form")
        new_comment = Comment(text=request.form.get('text'),
                              user=current_user,
                              post=requested_post
                              )
        print(f"New comment object: {new_comment}")
        if new_comment:
            print(f"Attempting to add {new_comment} to database.")
            db.session.add(new_comment)
            db.session.commit()
            print(f"{new_comment} added to database.")
            return redirect(url_for('show_post', post_id=requested_post.id))
    return render_template("post.html", post=requested_post, comment_form=comment_form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        message_data = request.form
        name = current_user.name
        email = request.form['email']
        phone = request.form['phone'] if request.form['phone'] else None
        message = request.form['message']
        data = f'Message request received. ' \
               f'name:\n{name}<br />\nemail:\n{email}<br />\n' \
               f'phone:{phone}<br />\nmessage:\n{message}'
        email_manager = EmailManager()
        email_manager.send_email(data=message_data)
        flask.flash('Your message was sent!')
        return redirect(url_for('contact'))
    return render_template('contact.html')



@app.route("/new-post", methods=['GET', 'POST'])
@login_required
def add_new_post():
    form = CreatePostForm()

    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    post = db.session.get(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author_name,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = post.author
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.session.get(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
    #app.run(host='0.0.0.0', port=5000)
