from flask import Flask, flash, send_from_directory, render_template, request, url_for
import pandas as pd
import json
import plotly
import plotly.express as px
from collections import Counter
from itertools import chain

from forms import yearForm,textForm
from flask_bootstrap import Bootstrap



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret key'
Bootstrap(app)

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
    cur  = list(collection_box.aggregate( [{"$match": {"title": {'$regex':  searchName} }  },{"$group" : {"_id" : {"title":"$title","rlid":"$releaseID", "runningTime":"$runningTime","poster":"$poster","resume":"$resume", "director":"$director", "releaseDate":"$releaseDate"}}},{ "$sort" : { "_id.title" : 1 } }]))
    return cur


def getActorMovies(actorName):
    if actorName == "" :
        return []
    cur = list(collection_box.aggregate([  {"$match":
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
    cur = list(collection_box.aggregate([  {"$match":
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
    print(cur)
    return cur[0]

def getSumRecettesActor(actorName,actorId):
    if actorName == "" :
        return []

       


    cur = list(collection_box.aggregate([  {"$match":{"mainCast.actorId": actorId },},
            {"$group" : {"_id" : {"title":"$title","rlid":"$releaseID", "recettes_totales" : "$recettes_totales","recettes_inter":"$recettes_inter"}}} ]))

    return cur


def getActorRanking(year):
    if int(year)<2007 :
        year_dict = {'year': {"$gt": 0}}
    else : 
        year_dict  = {'year': int(year)}

    cur =list(collection_box.aggregate( [
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

### Gestion des pages web

@app.route('/')
def accueil():

    return render_template('accueil.html')


@app.route('/movie-detail/<rlId>')
def movie_detail(rlId):
    details = getMovieDetail(rlId)
    df = pd.DataFrame(details)

    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.line(df, x="week_year", y="recettes_cumul", title='Recette par semaine')  
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('movie_detail.html', details=details,graphJSON=graphJSON)

@app.route('/movie-ranking', methods= ['GET'])
def movie_ranking():
    form = yearForm()
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

    return render_template('actor_detail.html',actorName = actorName,details=details,sum_recettes_fr=sum_recettes_fr,sum_recettes_inter=sum_recettes_inter,genres_counter=genres_counter)


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
        title = "Classement des revenus pour l'année "+year

    return render_template('ranking_actor.html', form=form,title=title, list=getActorRanking(year))



@app.route('/css/<path:path>')
def send_css(path):
  return send_from_directory('css', path)


@app.errorhandler(404)
def page_not_found(e):
    return 'Nothing to see here'

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0" ,port=8050) 





    # RELANCER SCRAPP ET V2RIFIE QUE TOUT OK puis finir ranking acteur
