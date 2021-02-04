from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    intro = TextAreaField('Post intro')
    text = TextAreaField('Post text', validators=[DataRequired()])
    subjects = StringField('Subjects')
    tags = StringField('Tags')
    author = StringField('Author', validators=[DataRequired()])
    image = StringField("Image URL")
    image_creator = StringField('Image creator')
    image_creator_url = StringField('Image creator URL')
    submit_button = SubmitField('Submit Post')

class TaxForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    slug = StringField("Slug", validators=[DataRequired()])
    description = TextAreaField("Description")
    image = StringField("Image URL")
    image_creator = StringField('Image creator')
    image_creator_url = StringField('Image creator URL')
    submit_button = SubmitField('Submit Info')
