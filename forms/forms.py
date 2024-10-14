from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, SelectField, FileField, IntegerField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import FileAllowed


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message='O nome de usuário é obrigatório.'), Length(min=4, max=150, message='O nome de usuário deve ter entre 4 e 150 caracteres.')])
    password = PasswordField('Password', validators=[DataRequired(message='A senha é obrigatória.')])
    submit = SubmitField('Login')

class UploadFileForm(FlaskForm):
    file = FileField('Upload Excel', validators=[DataRequired()])
    submit = SubmitField('Upload')

class FilterForm(FlaskForm):
    filial = StringField('Filial', validators=[Optional()])
    grupo = IntegerField('Grupo', validators=[Optional()])
    classificacao = StringField('Classificação', validators=[Optional()])
    codigo_bem = StringField('Código do Bem', validators=[Optional()])
    nota_fiscal = IntegerField('Nota Fiscal', validators=[Optional()])
    descricao_sintetica = StringField('Descricao', validators=[Optional()])
    submit = SubmitField('Filtrar')

class AlterarStatusForm(FlaskForm):
    novo_status = SelectField('Novo Status', choices=[('ATIVO', 'ATIVO'), ('DESATIVADO', 'DESATIVADO'),('FERIAS', 'FERIAS')], default='', validators=[DataRequired()])
    submit = SubmitField('Alterar Status')
    
class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    profile_pic = FileField('Upload Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update Profile')