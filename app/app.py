import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly_express as px
from flask import Flask

### APP ###
app = dash.Dash(__name__)
server = app.server

years_possible = list()
for year in range(2010,2022) :
    years_possible.append({'label':str(year),'value':str(year)})



#### Ranking Année sélectionné
import pymongo
client = pymongo.MongoClient("mongo_app")
database = client['boxoffice']
collection_box = database['scrapy_items']
cur = collection_box.aggregate([{"$group" : {"_id" : "$movie", "Recettes totales" : {"$max" : "$boxoffice_cumul"}}},{ "$sort" : { "Recettes totales" : -1 } }])
print(list(cur))
    
print(years_possible)
# Ce qui va être afficher sur notre dashboard.
app.layout = html.Div(
    dcc.Dropdown(
        id='demo-dropdown',
        options=years_possible,
        value="2021"
    ),)

if __name__ == '__main__':
    app.run_server(debug=True, port=8050, host="0.0.0.0")
