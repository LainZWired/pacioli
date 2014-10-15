from flask_wtf import Form
from wtforms import TextField, TextAreaField, \
SubmitField, SelectField, FloatField, validators, BooleanField
from wtforms.validators import Required, Length

class NewFileMap(Form):
  fileMapName = TextField("File Map Name")
  
class NewFileMapping(Form):
  fileMappingName = TextField("Name")
  fileMappingType = TextField("Type")
  fileMappingArgument = TextField("Argument")
  fileMappingValue = TextField("Value")
