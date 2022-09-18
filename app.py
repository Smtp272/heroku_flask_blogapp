import os
from flask import Flask, render_template, redirect, url_for, flash, session, request, g, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
from functools import wraps
from dotenv import load_dotenv

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

load_dotenv("D:\Downloads\Starting code\.env")
app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv("api_secret_key")
salting_value = int(os.getenv("salting_value"))
##BOOTSTRAP
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

###LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)

##CKEditor
ckeditor = CKEditor(app)

###GRAVATAR
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


##CONFIGURE TABLES

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="blog")


class User(UserMixin, db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), nullable=False)
    user_image_url = db.Column(db.String(250))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("Users.id"))
    comment_author = relationship("User", back_populates="comments")
    blog_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    blog = relationship("BlogPost", back_populates="comments")
    time_of_upload = db.Column(db.String(250), nullable=False)


# db.create_all()

def admin_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or str(current_user.get_id()) != "1":
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=['POST', 'GET'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        email = register_form.email.data
        user = User.query.filter_by(email_address=email).first()
        if not user:
            password = register_form.password.data
            name = register_form.name.data
            user_name = User.query.filter_by(name=name).first()
            if not user_name:
                new_user = User(
                    email_address=email,
                    password=generate_password_hash(password=register_form.password.data, method='pbkdf2:sha256', salt_length=salting_value),
                    name=name
                )
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return redirect(url_for('get_all_posts'))
            else:
                # flash(f"User name {name} already in use. Try another one")
                register_form.name_check()

        else:
            flash("Email already registered. Login instead!")
            error = "You've already signed up with that email, log in instead!"
            return redirect(url_for('login'))

    return render_template("register.html", form=register_form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    login_form = LoginForm()

    if login_form.validate_on_submit() and request.method == 'POST':
        password = login_form.password.data
        user = User.query.filter_by(email_address=login_form.email.data).first()

        # TODO; check if the user exists
        if not user:
            error = 'Email Address not registered'
        elif check_password_hash(user.password, login_form.password.data):
            login_user(user)
            return redirect(url_for('get_all_posts'))
        else:
            error = "Invalid password"

    return render_template("login.html", form = login_form, error=error)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=['post', 'get'])
def show_post(post_id):
    edit_comment_error = None
    comment_form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    #
    # if comment_to_update:
    #     edit_comment_error = "You already made a comment to this blog"
    #     text_to_edit = comment_to_update.text
    #     comment_form.comment_text.data = text_to_edit
    #     comment_form.submit.label.text = "Update Comment"

    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to be able to post a comment")
            return redirect(url_for("login"))
        ##CHECK IF USER HAS MADE ANY COMMENTS ON THE BLOG
        else:
            comment_to_update = db.session.query(Comment).filter_by(author_id=int(current_user.get_id()),
                                                                    blog_id=post_id).first()
            if not comment_to_update:
                new_comment = Comment(
                    text=comment_form.comment_text.data,
                    comment_author=current_user,
                    blog=requested_post,
                    time_of_upload=date.today().strftime("%B %d, %Y")
                )
                db.session.add(new_comment)
                db.session.commit()
            else:
                edit_comment_error = "You already made a comment to this blog"
            # else:
            #     comment_to_update.text = comment_form.comment_text.data
            #     db.session.commit()
            #     flash("Your comment has been updated")
            #     return redirect(url_for('show_post', post_id=post_id))
            #

    return render_template("post.html", post=requested_post, form=comment_form, edit_comment_error=edit_comment_error)


@app.route("/post/edit_comment/<int:post_id>", methods=['post', 'get'])
def edit_comment(post_id):
    comment_to_update = db.session.query(Comment).filter_by(author_id=int(current_user.get_id())).first()
    text_to_edit = comment_to_update.text
    comment_form = CommentForm(comment_text=text_to_edit,
                               )
    comment_form.submit.label.text = "Update Comment"
    if comment_form.validate_on_submit():
        comment_to_update.text = comment_form.comment_text.data
        db.session.commit()
        flash("Your comment has been updated")
        return redirect(url_for('show_post', post_id=post_id))
    return render_template("edit_comment.html", form=comment_form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=['POST', 'GET'])
@admin_access
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


@app.route("/edit-post/<int:post_id>", methods=['POST', 'GET'])
@admin_access
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_access
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
