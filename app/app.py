from flask import Flask, flash, redirect, render_template, request, url_for
import pandas as pd
import json
import plotly
import plotly.express as px

from forms import yearForm,textForm
# from flask_bootstrap import Bootstrap



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret key'
# Bootstrap(app)

years_possible = list()
for year in range(2010,2022) :
    years_possible.append({'label':str(year),'value':str(year)})


import pymongo
client = pymongo.MongoClient("mongo_app")
database = client['boxoffice']
collection_box = database['scrapy_items']

@app.context_processor
def utility_processor():
    def format_money(money):
        return '${:,.2f}'.format(money)
    return dict(format_money=format_money)

@app.context_processor
def utility_processor():
    def format_time(time):

        return '{hour} h {mins} mins'.format(hour=int(time/60),mins=time%60)
    return dict(format_time=format_time)


def getMovieRanking(year=2021):
    cur = list(collection_box.aggregate([  {"$match":
    {'year': int(year)} },
        {"$group" : {"_id" : {"title":"$title","rlid":"$releaseID"}, "Recettes totales" : {"$max" : "$recettes_cumul"}}},{ "$sort" : { "Recettes totales" : -1 } }]))

    if len(cur) == 0 :
        cur = list(collection_box.aggregate([{"$group" : {"_id" : {"title":"$title","rlid":"$releaseID"},"Recettes totales" : {"$max" : "$recettes_cumul"}}},{ "$sort" : { "Recettes totales" : -1 } }]))
    movie_list = []
    for movie in cur:
        movie_list.append([movie["_id"]["title"],movie["_id"]["rlid"],movie["Recettes totales"]])
    return movie_list


def getMovieDetail(rlId):
    cur = list(collection_box.find({"releaseID":rlId}).sort( [("year",1),("week",1)]))
    return cur


def searchMovies(searchName):
    cur  = list(collection_box.aggregate( [{"$match": {"title": {'$regex':  searchName} }  },{"$group" : {"_id" : {"title":"$title","rlid":"$releaseID"}}} ] ))
    return cur

### Gestion des pages web

@app.route('/')
def accueil():
    return 'Quelle année étudier ?'

@app.route('/movie-detail/<rlId>')
def movie_detail(rlId):
    details = getMovieDetail(rlId)
    df = pd.DataFrame(details)

    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.line(df, x="week_year", y="recettes_cumul", title='Recette par semaine')  
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return 'Détail du film {}!'.format(rlId) + render_template('movie_detail.html', details=details,graphJSON=graphJSON)

# @app.route('/movie-ranking/<int:year>')
# def movie_ranking(year):
#     return render_template('ranking_movies.html', year=year, list=getMovieRanking(year))

@app.route('/movie-ranking', methods= ['GET'])
def movie_ranking():
    form = yearForm()
    
    # try  :
    #     year  = request.args.get('year')
    # except  (KeyError, TypeError):
    #     year = 0
    year  = request.args.get('input')
    if year ==  None :
        year =  0

    print("year",year)
    if  int(year) < 2007 :
        title = "Classement des revenus  depuis 2007"
    else:
        title = "Classement des revenus pour l'année "+year

    return render_template('ranking_movies.html', form=form,title=title, list=getMovieRanking(year))


@app.route('/movie-search', methods= ['GET'])
def movie_search():
    form = textForm()
    
    text  = request.args.get('input')
    if text != None : 
        title = "Résultats de  recherches pour : |"+text+"|"
    else : 
        title  = "Recherche d'un film"


    return render_template('movie_search.html',title=title, form=form,movie_list=searchMovies(text))


@app.errorhandler(404)
def page_not_found(e):
    return 'Nothing to see here'

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0" ,port=8050) 
