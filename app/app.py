from flask import Flask, flash, send_from_directory, render_template, request, url_for
import pandas as pd
import json
import plotly
import plotly.express as px
from collections import Counter
from itertools import chain

from forms import yearForm,textForm



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret key'

years_possible = list()
for year in range(2010,2022) :
    years_possible.append({'label':str(year),'value':str(year)})


import pymongo
client = pymongo.MongoClient("mongo_app")
database = client['boxoffice']
collection = database['scrapy_items']

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
    if int(year)<2007 :
        year_dict = {'year': {"$gt": 0}}
    else : 
        year_dict  = {'year': int(year)}

    cur = list(collection.aggregate([  
        {"$match": year_dict },
        {"$group" : {"_id" : {"title":"$title","rlid":"$releaseID","rlDate":"$releaseDate"}, "Recettes totales" : { "$first":"$recettes_totales"} }},
        { "$sort" : { "Recettes totales" : -1 } }
            ]))

    return cur


def getMovieDetail(rlId):
    cur = list(collection.find({"releaseID":rlId}).sort( [("year",1),("week",1)]))
    return cur


def searchMovies(searchName):
    cur  = list(collection.aggregate( [{"$match": {"title": {'$regex':  searchName} }  },{"$group" : {"_id" : {"title":"$title","rlid":"$releaseID", "runningTime":"$runningTime","poster":"$poster","resume":"$resume", "director":"$director", "releaseDate":"$releaseDate"}}},{ "$sort" : { "_id.title" : 1 } }]))
    return cur


def getActorMovies(actorName):
    if actorName == "" :
        return []
    cur = list(collection.aggregate([  {"$match":
    {"$and": [
        {"cast.name":actorName  },
    ]}},
     {
         "$unwind": "$cast"
     }
    ,
    {"$match":
    {"$and": [
        {"cast.name":actorName  },
    ]}},
        {"$group" : {"_id" : {"actorId":"$cast.actorId","actor":"$cast.actor","img_link": "$cast.img_link"},"movies": {"$addToSet": {"title":"$title","rlID":"$releaseID"} }}}]))

    return cur


def getActorDetail(actorName,actorId):

    if actorName == "" :
        return []
    cur = list(collection.aggregate([  {"$match":
    {"$and": [
        {"cast.name":actorName  },
        {"cast.actorId":actorId},
    ]}},
     {
         "$unwind": "$cast"
     }
    ,
                           {"$match":
    {"$and": [
        {"cast.name":actorName  },
        {"cast.actorId":actorId},
    ]}},
        {"$group" : {"_id" : {"actorId":"$cast.actorId","actor":"$cast.actor","img_link": "$cast.img_link"}, "movies": {"$addToSet": {"title":"$title","rlid":"$releaseID",
                                                                                                                                    "poster":"$poster","recettes_totales":"$recettes_totales",
                                                                                                                                    "recettes_inter":"$recettes_inter","genres":"$genres"},
                                                                                                                       }}}]))
    return cur[0]

def getActorEvolution(actorName,actorId) :

    cur = cur = list(collection.aggregate([ 
                           {"$match":
    {"$and": [
        {"mainCast.name":actorName  },
        {"mainCast.actorId":actorId},
    ]}},{"$group" : {"_id" : {"year":"$year","title":"$title"},"recettes" : {"$sum":"$recettes"}}}, {"$group" : {"_id" : "$_id.year","recettes" : {"$sum":"$recettes"}}}, 
    { "$sort" : { "_id" : 1 } }                  
                          ]))

    return cur


def getSumRecettesActor(actorName,actorId):
    if actorName == "" :
        return []
    cur = list(collection.aggregate([  {"$match":{"mainCast.actorId": actorId },},
            {"$group" : {"_id" : {"title":"$title","rlid":"$releaseID", "recettes_totales" : "$recettes_totales","recettes_inter":"$recettes_inter"}}} ]))

    return cur


def getActorRanking(year):
    if int(year)<2007 :
        year_dict = {'year': {"$gt": 0}}
    else : 
        year_dict  = {'year': int(year)}

    cur =list(collection.aggregate( [
        {"$match" :year_dict},
    {
     "$unwind": { "path": "$mainCast" }
    },
    {
     "$group":
       {
         "_id": {"actor":"$mainCast.name","actorId":"$mainCast.actorId"},
           "movies" :{
               "$addToSet" : {"title":"$title","recettes":"$recettes_totales"}
           }
       }
    },
     {
         "$unwind": "$movies"
     }
    ,
    {
     "$group":
       {
         "_id": {"actor":"$_id.actor","actorId":"$_id.actorId"},
           "recettes" :{
               "$sum" : "$movies.recettes"
           }
       }
    },
    { "$sort" : { "recettes" : -1 } }
    
    ] ))

    return cur


def getRecettesByGenres(year):

    if int(year)<2007 :
        year_dict = {'year': {"$gt": 0}}
    else : 
        year_dict  = {'year': int(year)}

    cur = list(collection.aggregate([  {"$match": year_dict },
     {
     "$unwind": { "path": "$genres" }
    },   
        {"$group" : {"_id" : {"rlId":"$releaseID","genres":"$genres"},"recettes":{"$sum":"$recettes"} }},
      {"$group" : {"_id" : "$_id.genres","recettes_totales":{"$sum":"$recettes"}} },
      {"$sort":{"recettes_totales":-1}}]))
    return cur

def getRecettesByNote(year):
    if int(year)<2007 :
        year_dict = {'year': {"$gt": 0}}
    else : 
        year_dict  = {'year': int(year)}

    cur = list(collection.aggregate([  {"$match": year_dict },
            {"$group" : {"_id" : {"rlId":"$releaseID","note":"$note"},"recettes":{"$sum":"$recettes"} }},
      {"$group" : {"_id" : "$_id.note","recettes_totales":{"$avg":"$recettes"}} },  
                          {"$sort":{"_id":1}}]))

    return cur

def getRecettesByWeek(year): 
    if int(year)<2007 :
        year_dict = {'year': {"$gt": 0}}
    else : 
        year_dict  = {'year': int(year)}

    return list(collection.aggregate([  {"$match": year_dict }, 
                            
         {"$group": {"_id": '$week',"recettes_totales":{"$sum":"$recettes"}}},
         {"$sort":{"_id":1}}
      ]))

def getRecettesByDistributor(year): 
    if int(year)<2007 :
        year_dict = {'year': {"$gt": 0}}
    else : 
        year_dict  = {'year': int(year)}

    return list(collection.aggregate([  {"$match": year_dict }, 
        {"$group" : {"_id" : {"rlId":"$releaseID","distributor":"$distributor"},"recettes":{"$sum":"$recettes"} }},
        {"$group": {"_id": '$_id.distributor',"recettes_totales":{"$sum":"$recettes"}}},
        {"$sort":{"recettes_totales":-1}},
        {"$limit":50}
      ]))


### Gestion des pages web

@app.route('/')
def accueil():

    return render_template('accueil.html')


@app.route('/movie-detail/<rlId>')
def movie_detail(rlId):
    details = getMovieDetail(rlId)
    df = pd.DataFrame(details)


    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.line(df, x="week_year", y="recettes_cumul", title='Recettes cumulée par semaine',labels={
                     "recettes_cumul": "Recettes cumulées, en $",
                     "week_year": "Numéro et année de la semaine"
                 })  
    graphJSON_cumul = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.line(df, x="week_year", y="recettes", title='Recettes par semaine',labels={
                     "recettes": "Recettes de la semaine, en $",
                     "week_year": "Numéro et année de la semaine"
                 })  
    graphJSON_recettes = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.line(df, x="week_year", y="rank", title='Evolution du classement par semaine',labels={
                     "rank": "Classement",
                     "week_year": "Numéro et année de la semaine"
                 })  
    graphJSON_rank = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    if (df['nbCinemas'].isnull().values.any()):
        graphJSON_cinemas = None
    else :
        # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
        fig = px.line(df, x="week_year", y="nbCinemas", title='Evolution du nombre de cinémas projetant le film par semaine',labels={
                        "nbCinemas": "Nombre de cinémas",
                        "week_year": "Numéro et année de la semaine"
                    })  
        graphJSON_cinemas = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('movie_detail.html', details=details,graphJSON_cumul=graphJSON_cumul,graphJSON_recettes=graphJSON_recettes,graphJSON_rank=graphJSON_rank,graphJSON_cinemas=graphJSON_cinemas)

@app.route('/movie-ranking', methods= ['GET'])
def movie_ranking():
    form = yearForm()
    year  = request.args.get('input')
    if year ==  None :
        year =  0

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
        title = "Résultats de  recherches pour : "+text+""
        list=searchMovies(text)
    else : 
        text=""
        title  = "Recherche d'un film"
        list = []


    return render_template('movie_search.html',title=title, form=form,list=list)


@app.route('/actor-search', methods= ['GET'])
def actor_search():
    form = textForm()
    
    text  = request.args.get('input')
    if text != None : 
        title = "Résultats de recherches pour : "+text+""
        list=getActorMovies(text)
    else : 
        text=""
        title  = "Recherche d'un acteur"
        list=[]


    return render_template('actor_search.html',title=title, form=form,actor=text,list=list)


@app.route('/actor-detail/<actorName>/<actorId>')
def actor_detail(actorName,actorId):


    details = getActorDetail(actorName,actorId)

    genres_list = []
    for movie in details["movies"]:
        genres_list.append(movie["genres"])

    genres_counter = Counter(list(chain(*genres_list)))

    sum_recettes_fr = sum(movie["_id"]['recettes_totales'] for movie in getSumRecettesActor(actorName,actorId))
    sum_recettes_inter = sum(movie["_id"]['recettes_inter'] for movie in getSumRecettesActor(actorName,actorId))

    dict_genres = {"genres" : genres_counter.keys(),"values":genres_counter.values()}
    fig = px.pie(dict_genres, names="genres", values='values',title="Répartition de ses genres de films favoris",color_discrete_sequence=px.colors.sequential.RdBu)
    graphJSON_genres = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


    evolution = getActorEvolution(actorName,actorId)

    df = pd.DataFrame(evolution)


    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.line(df, x="_id", y="recettes", title='Recettes générée par an',labels={
                     "recettes": "Recettes, en $",
                     "_id": "Année"
                 })  
    graphJSON_evolution = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


    return render_template('actor_detail.html',actorName = actorName,details=details,sum_recettes_fr=sum_recettes_fr,sum_recettes_inter=sum_recettes_inter,genres_counter=genres_counter,graphJSON_genres=graphJSON_genres,graphJSON_evolution=graphJSON_evolution)


@app.route('/actor-ranking', methods= ['GET'])
def actor_ranking():
    form = yearForm()
    year  = request.args.get('input')
    if year ==  None :
        year =  0

    if  int(year) < 2007 :
        title = "Classement des revenus des acteurs depuis 2007"
        year=0
    else:
        title = "Classement des revenus des acteurs pour l'année "+year

    return render_template('ranking_actor.html', form=form,title=title, list=getActorRanking(year))


@app.route('/other-ranking', methods= ['GET'])
def other_ranking():
    form = yearForm()
    year  = request.args.get('input')
    if year ==  None :
        year =  0

    if  int(year) < 2007 :
        title = "Classement divers depuis 2007"
        year=0
    else:
        title = "Classement divers pour l'année "+year

    recettesGenre = getRecettesByGenres(year)
    df = pd.DataFrame(recettesGenre)
    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.bar(df, x="_id", y="recettes_totales", title='Recettes générées par genre',labels={
                     "recettes_totales": "Recettes, en $",
                     "_id": "Genre"
                 })  
    fig.update_xaxes(tickangle=45)
    graphJSON_genres = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    recettesNote = getRecettesByNote(year)
    df = pd.DataFrame(recettesNote)
    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.bar(df, x="_id", y="recettes_totales", title='Recettes générées par note IMDB',labels={
                     "recettes_totales": "Recettes, en $",
                     "_id": "Note"
                 })  
    graphJSON_note = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    recettesWeek = getRecettesByWeek(year)
    df = pd.DataFrame(recettesWeek)
    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.bar(df, x="_id", y="recettes_totales", title='Recettes générées par semaine de l\'année',labels={
                     "recettes_totales": "Recettes, en $",
                     "_id": "Semaine"
                 })  
    graphJSON_week = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    recettesDistributor = getRecettesByDistributor(year)
    df = pd.DataFrame(recettesDistributor)
    df = df.query("_id != 'N/A'")
    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.bar(df, x="_id", y="recettes_totales", title='Recettes générées par distributeur',labels={
                     "recettes_totales": "Recettes, en $",
                     "_id": "Distibuteur"
                 })  
    fig.update_xaxes(tickangle=45)
    graphJSON_distributor = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    
    

    return render_template('other-ranking.html', form=form,title=title,graphJSON_genres=graphJSON_genres,graphJSON_note=graphJSON_note,graphJSON_week=graphJSON_week,graphJSON_distributor=graphJSON_distributor)



@app.errorhandler(404)
def page_not_found(e):
    return 'Nothing to see here'


if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0" ,port=8050) 





    # RELANCER SCRAPP ET V2RIFIE QUE TOUT OK puis finir ranking acteur
