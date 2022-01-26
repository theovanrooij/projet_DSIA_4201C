from flask_wtf import Form
from wtforms import SelectField, SubmitField,StringField
from wtforms.validators import DataRequired

class yearForm(Form):
    years_possible = [(0,"Tous les temps")]
    for year in range(2007,2023) :
        years_possible.append((year,year))
    input = SelectField(u'Année à étudier : ', choices=years_possible)
    submit = SubmitField('Go')

class textForm(Form):
    input = StringField('Nom à rechercher :  ', validators=[DataRequired()])
    submit = SubmitField('Go')