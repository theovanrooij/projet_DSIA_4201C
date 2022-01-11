# Scrapping temps réel :  Pas utile pour nous


import dash
from dash import html,dcc
from dash.dependencies import Input, Output
import plotly_express as px
from flask import Flask


def format_money(money):
    return '${:,.2f}'.format(money)
### APP ###
app = dash.Dash(__name__)
server = app.server

years_possible = list()
for year in range(2010,2022) :
    years_possible.append({'label':str(year),'value':str(year)})



#### Ranking Année sélectionné


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Ce qui va être afficher sur notre dashboard.
accueil_layout = html.Div(className="accueil",
        children=[
            dcc.Dropdown(
                id='select_year',
                options=years_possible,
                value="2021"
            ),
            html.P("Dashboard fait par DANG Méline et VAN ROOIJ Théo."),
            html.Div(id='page-content')
        ]
    
)

import pymongo
client = pymongo.MongoClient("mongo_app")
database = client['boxoffice']
collection_box = database['scrapy_items']

def getMovieRanking(year=2021):
    cur = list(collection_box.aggregate([  {"$match":
    {'year': int(year)} },
        {"$group" : {"_id" : {"movie":"$movie","rlid":"$releaseID"}, "Recettes totales" : {"$max" : "$boxoffice_cumul"}}},{ "$sort" : { "Recettes totales" : -1 } }]))

    if len(cur) == 0 :
        cur = list(collection_box.aggregate([{"$group" : {"_id" : {"movie":"$movie","rlid":"$releaseID"},"Recettes totales" : {"$max" : "$boxoffice_cumul"}}},{ "$sort" : { "Recettes totales" : -1 } }]))
    movie_ranking = list()
    print(cur[0:10])
    for movie in cur:
        movie_ranking.append(html.Li(
            children=[html.A(movie["_id"]["movie"],href='/movie-detail/'+movie["_id"]["rlid"]),format_money(movie["Recettes totales"])]
            ))
    
    return movie_ranking


def getMovieRankingLayout(year=2021) :
    return html.Div(
        children=[
            html.H1("Classement des films en "+str(year)),
            html.Ol(children =getMovieRanking(year))
        ]
    )

def getMovieDetail(release_id):

    return None
# Update the index
@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    split_path  = pathname.split("/")

    if split_path[1] == 'movie-ranking':
        if  (len(split_path)  >=3):
            year = split_path[2]
        else :
            year=2021
        return getMovieRankingLayout(year)
    elif split_path[1] == 'movie-detail':
        return  getMovieDetail(split_path[2])
    else:
        return accueil_layout
    # You could also return a 404 "URL not found" page here


if __name__ == '__main__':
    app.run_server(debug=True, port=8050, host="0.0.0.0")
