from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    text = TextAreaField('Post text', validators=[DataRequired()])
    subjects = StringField('Subjects')
    tags = StringField('Tags')
    author = StringField('Author', validators=[DataRequired()])
    image = StringField("Image URL")
    image_creator = StringField('Image creator')
    image_creator_url = StringField('Image creator URL')