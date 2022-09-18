from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField,EmailField
from wtforms.validators import DataRequired, URL,Email
from flask_ckeditor import CKEditorField

##WTForm
##New POST FORM
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

##REGISTER
class RegisterForm(FlaskForm):
    email = EmailField("Email Address", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Register")


    def name_check(self):
        message = f"The username {self.name.data} already exists. Try another one"
        self.name.errors.append(message)



##LOGIN FORM

class LoginForm(FlaskForm):
    email = EmailField("Email Address", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class CommentForm(FlaskForm):
    comment_text = CKEditorField("Your comments here", validators=[DataRequired()])
    submit = SubmitField("Send Comment")

    def comment_check(self):
        message = f"You've already made a comment to this blog"
        self.comment_text.errors.append(message)
