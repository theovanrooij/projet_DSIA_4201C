#Importation des packages nécessaires.
from datetime import datetime
from time import sleep
from flask import Flask, flash, send_from_directory,redirect, render_template, request, url_for
import pandas as pd
import json
import plotly
import plotly.express as px
from collections import Counter
from itertools import chain
import os
from forms import yearForm,textForm



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret key'


"""
    Convertit une somme d'argent d'un entier vers une string au format monétaire pour être lisible.
    Le décorateur de la fonction la rend accessible depuis les templates html.

    Args:

        money : somme à convertir. C'est un entier.

    Returns:
        La somme au bon format. Type string.
"""
@app.context_processor
def utility_processor():
    def format_money(money):
        return '${:,.2f}'.format(money)
    return dict(format_money=format_money)

"""
    Convertit une durée en minutes vers le format _h_mins.
    Le décorateur de la fonction la rend accessible depuis les templates html.

    Args:

        time : durée à convertir. C'est un entier.

    Returns:
        La durée au bon format. Type string.
"""
@app.context_processor
def utility_processor():
    def format_time(time):

        return '{hour} h {mins} mins'.format(hour=int(time/60),mins=time%60)
    return dict(format_time=format_time)


"""
    Permet d'obtenir le pourcentage des recettes réalisées en France à partir de la valeur des recettes françaises et mondiales.
    Le décorateur de la fonction la rend accessible depuis les templates html.

    Args:

        recettes_fr : Recettes en France
        recettes_inter : Recettes dans le monde

    Returns:
        Le pourcentage des recettes réalisées en France.
"""
@app.context_processor
def utility_processor():
    def get_percentage(recettes_fr,recettes_inter):

        return int(recettes_fr/recettes_inter*100)
    return dict(get_percentage=get_percentage)




"""
    Permet d'obtenir le classement des films ayant générés le plus d'argent en France pour une année choisie.

    Args:

        year : Année à étudier

    Returns:
        Une liste contenant les éléments des films dans l'ordre souhaité. Chaque élément est un dictionnaire contenant le nom du film, son releaseId et ses recettes.
"""
def getMovieRanking(year=2022):
    
    # Nous commençons par générer le dictionnaire filtrant les éléments selon l'année souhaitée.
    year = int(year)
    # Si l'année est inférieure à la valeur minimale présente dans la base de données, nous sélectionnons toutes les années.
    if year<2007 : # La valeur minimale ici est 2007.
        year_dict = {'year': {"$gt": 0}}
    else : 
        year_dict  = {'year': year}
        year_dict_sub  = {'year': year-1}

    # Nous commençons par récupérer toutes les données de l'année passée en paramètre.
    movieMain = list(collection.aggregate([  
        {"$match": year_dict },
        # Nous sélectionnons la valeur maximale des recettes cumulées sur l'année pour chaque film.
        {"$group" : {"_id" : {"title":"$title","rlid":"$releaseID","rlDate":"$releaseDate"},"recettes":{"$max":"$recettes_cumul"}}},
        # Nuos dégroupons l'ID pour l'exploiter facilement dans un DataFrame.
        {"$group" : {"_id" : "$_id.rlid","title":{ "$first": "$_id.title" },"Recettes totales":{ "$first": "$recettes" },"rlDate":{ "$first": "$_id.rlDate" }}},
        { "$sort" : { "Recettes totales" : -1 } }
            ]))

    # Si on étudie une année en particulier, nous venons récupérer les données de l'année précédente pour soustraire les recettes des films sortis en fin d'année.
    # Nous devons faire cela car, par défaut, la requête précédente inclue les recettes des deux années.
    if year > 2008 :
        movie_id = [movie["_id"]for movie in movieMain]
        movieSub = list(collection.aggregate([  
            {"$match": year_dict_sub },
            {"$match": {"releaseID":{"$in":movie_id}} },
            {"$group" : {"_id" :"$releaseID", "Recettes totales":{"$max":"$recettes_cumul"} }},
            { "$sort" : { "Recettes totales" : -1 } }
                ]))
        

        # Nous venons ensuite réaliser la soustraction des deux années pour avoir les réelles recettes des films chevauchant deux années.

        dfSub = pd.DataFrame(movieSub)

        dfMain = pd.DataFrame(movieMain)
        df = dfMain.merge(dfSub,how="left", on="_id")
        df["Recettes totales_y"] = df["Recettes totales_y"].fillna(0) 
        df["Recettes totales"] = df["Recettes totales_x"] - df["Recettes totales_y"]
        cur = df.sort_values(by="Recettes totales",ascending=False).drop(columns=["Recettes totales_x","Recettes totales_y"]).to_dict(orient="records")
    else :
        cur = list(movieMain)

    return cur

"""
    Permet d'obtenir les détails (si disponibles) sur un film tels que :
        - sa durée ;
        - son distributeur de films ;
        - son réalisateur ;
        - sa note ;
        - son budget ;
        - ses recettes totales ; 
        - ses recettes en France ;
        - son pourcentage des recettes réalisées en France ;
        - son résumé ; 
        - son/ses genre(s) ;
        - sa date de sortie ;
        - son pays d'origine ;
        - son casting.

    Args:

        rlId : release ID du film à étudier

    Returns:
        Une liste contenant les détails du film mentionnées (durée, distributeur, réalisateur, note, budget, recettes, résumé, genre(s), date de sortie, pays d'origine). 
"""
def getMovieDetail(rlId):
    cur = list(collection.find({"releaseID":rlId}).sort( [("year",1),("week",1)]))
    return cur

"""
    Permet d'effectuer une recherche pour retrouver un film.

    Args:

        searchName : nom entré pour lequel nous allons chercher des correspondances dans les noms des films

    Returns:
        Une liste contenant les résultats de recherche du film.
"""
def searchMovies(searchName):
    cur  = list(collection.aggregate( [{"$match": {"title": {'$regex':  searchName} }  },{"$group" : {"_id" : {"title":"$title","rlid":"$releaseID", "runningTime":"$runningTime","poster":"$poster","resume":"$resume", "director":"$director", "releaseDate":"$releaseDate"}}},{ "$sort" : { "_id.title" : 1 } }]))
    return cur

"""
    Permet d'effectuer une recherche pour retrouver un(e) acteur/actrice.

    Args:

        actorName : nom entré pour lequel nous allons chercher des correspondances dans les noms des acteurs

    Returns:
        Une liste contenant les résultats de recherche des acteurs.
"""
def searchActor(actorName):
    if actorName == "" :
        return [0]
    cur = list(collection.aggregate([  {"$match":
        {"cast.name": {'$regex':  actorName}   },
    },
     {
         "$unwind": "$cast"
     }
    ,
    {"$match":
        {"cast.name": {'$regex':  actorName}   },
    },
        {"$group" : {"_id" : {"actorId":"$cast.actorId","actorName":"$cast.name","img_link": "$cast.img_link"},"movies": {"$addToSet": {"title":"$title","rlID":"$releaseID"} }}}]))

    return cur

"""
    Permet d'obtenir les détails sur un(e) acteur/actrice tels que :
        - l'argent généré au total par les films dans lequel il/elle est un(e) acteur/actrice principal(e) ; 
        - l'argent généré en France par les films dans lequel il/elle est un(e) acteur/actrice principal(e) ; 
        - film(s) dans le(s)quel(s) il/elle a fait une apparition (triés dans l'ordre anti-chronologique) ; 
        - répartition de ses genres de films dans le(s)quel(s) il/elle a joué ;
        - un graphique de ses recettes générées par ans.


    Args:

        actorName : nom de l'acteur/actrice dont nous voulons connaître les détails
        actorId : ID de l'acteur/actrice (puisque plusieurs acteurs peuvent avoir le même nom, un ID les différencie)

    Returns:
        Une liste contenant les détails (argent généré, recettes par années, film(s) dans le(s)quel(s) il/elle a joué) de l'acteur/actrice choisi.
"""
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
                                                                                                                                    "poster":"$poster","rlDate":"$releaseDate","recettes_totales":"$recettes_totales",
                                                                                                                                    "recettes_inter":"$recettes_inter","genres":"$genres"},
                                                                                                                       }}}]))
    return cur[0]


"""
    Permet d'afficher l'évolution de l'acteur/actrice voulu en France.

    Args:

        actorName : nom de l'acteur/actrice dont nous voulons connaître les détails
        actorId : ID de l'acteur/actrice (puisque plusieurs acteurs peuvent avoir le même nom, un ID les différencie)

    Returns:
        Dataframe sur l'évolution de l'acteur/actrice. ???
"""
def getActorEvolution(actorName,actorId) :

    cur =list(collection.aggregate( [
            {"$match":
    {"$and": [
        {"mainCast.name":actorName  },
        {"mainCast.actorId":actorId},
    ]}},
        {"$group":{
            "_id": {"actor":actorName,"actorId":actorId}, "movies" :{
                "$addToSet" : {"title":"$title","rlId":"$releaseID"}}}
        }
        ] ))
        
    ids = [movie["rlId"] for movie in cur[0]["movies"]]
    curbis = list(collection.aggregate( [
            {"$match": {"releaseID":{"$in":ids}} },
        {"$group":{
            "_id": {"year":"$year","title":"$title","rlId":"$releaseID"},"title":{"$first":"$title"},"year":{"$first":"$year"},"rlId":{"$first":"$releaseID"},"recettes":{"$max":"$recettes_cumul"}}},
    
        ] ))
    
    df = pd.DataFrame(curbis)
    for id in ids : 
        quer = df.query("rlId == '"+id+"'")
        if len(quer) == 2:
            max_year = max(quer["year"])
            row_max = df.query("rlId == '"+id+"' & year == "+str(max_year))["recettes"].index[0]
            row_max_previous = df.query("rlId == '"+id+"' & year == "+str(max_year-1))["recettes"].index[0]
            df.loc[row_max,"recettes"] -= df.loc[row_max_previous,"recettes"]
    df = df.groupby("year").sum().reset_index()

    return df


"""
    Permet d'obtenir les recettes engendrés par un(e) acteur/actrice en France.

    Args:

        actorName : nom de l'acteur/actrice dont nous voulons connaître les recettes
        actorId : ID de l'acteur/actrice (puisque plusieurs acteurs peuvent avoir le même nom, un ID les différencie)

    Returns:
        Une liste contenant les recettes de l'acteur/actrice souhaité(e).
"""
def getSumRecettesActor(actorName,actorId):
    if actorName == "" :
        return []
    cur = list(collection.aggregate([  {"$match":{"mainCast.actorId": actorId },},
            {"$group" : {"_id" : {"title":"$title","rlid":"$releaseID", "recettes_totales" : "$recettes_totales","recettes_inter":"$recettes_inter"}}} ]))

    return cur

"""
    Permet d'obtenir le classement de l'acteur/actrice en France pour une année choisie.

    Args:

        year : année à étudier

    Returns:
        Classement de l'acteur/actrice pour l'année choisie.
"""
def getActorRanking(year):
    year=int(year)
    if year<2007 :
        year_dict = {'year': {"$gt": 0}}
        return list(collection.aggregate( [
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
    else : 
        year_dict  = {'year': year}

    main =list(collection.aggregate( [
            {"$match" :year_dict},
        {"$unwind": { "path": "$mainCast" }},
        {"$group":{
            "_id": {"actor":"$mainCast.name","actorId":"$mainCast.actorId"}, "movies" :{
                "$addToSet" : {"title":"$title","rlId":"$releaseID"}}}
        }
        ] ))

    movie_ranking = pd.DataFrame(getMovieRanking(year))

    for actor in main :
        recettes = 0
        for movie in actor["movies"] :
            recettes += movie_ranking.query("_id == '"+movie["rlId"]+"'")["Recettes totales"].values[0]
        actor["recettes"] = recettes
    main = sorted(main, key=lambda d: d['recettes'],reverse=True) 
    return main
    

"""
    Permet d'obtenir les recettes générées par genre en France pour une année choisie.

    Args:

        year : année à étudier

    Returns:
        Une liste contenant les recettes engendrées pour chaque genre en France selon l'année passée en argument.
"""    
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

"""
    Permet d'obtenir les recettes générées par note en France pour une année choisie.

    Args:

        year : année à étudier

    Returns:
        Une liste contenant les recettes engendrées en fonction de la note du film pour l'année sélectionnée.
"""
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

"""
    Permet d'obtenir les recettes générées par semaine en France pour une année choisie.

    Args:

        year : année à étudier

    Returns:
        Une liste contenant les recettes par semaines des films en France selon l'année sélectionnée.
"""
def getRecettesByWeek(year): 
    if int(year)<2007 :
        year_dict = {'year': {"$gt": 0}}
    else : 
        year_dict  = {'year': int(year)}

    return list(collection.aggregate([  {"$match": year_dict }, 
                            
         {"$group": {"_id": '$week',"recettes_totales":{"$sum":"$recettes"}}},
         {"$sort":{"_id":1}}
      ]))

"""
    Permet d'obtenir les recettes générées par distributeur de films en France pour une année choisie.
    Args:

        year : année à étudier

    Returns:
        Une liste contenant les recettes des films par distributeur de films.
"""
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

"""
    Page "movie-detail".
    Permet d'afficher les détails (durée, distributeur, réalisateur, note, budget, recettes, résumé, genre(s), date de sortie, pays d'origine) du film choisi.
    Affiche aussi trois graphes : 
        - les recettes cumulées par semaine du film ;
        - les recettes par semaine du film ;
        - l'évolution de son classement par semaine.
    Ainsi que l'affichage du casting des acteurs.
"""
@app.route('/movie-detail/<rlId>')
def movie_detail(rlId):
    details = getMovieDetail(rlId)
    df = pd.DataFrame(details)


    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.line(df, x="week_year", y="recettes_cumul", title='Recettes cumulée par semaine',labels={
                     "recettes_cumul": "Recettes cumulées, en $",
                     "week_year": "Numéro et année de la semaine"
                 }, markers=True)  
    graphJSON_cumul = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.line(df, x="week_year", y="recettes", title='Recettes par semaine',labels={
                     "recettes": "Recettes de la semaine, en $",
                     "week_year": "Numéro et année de la semaine"
                 }, markers=True)  
    graphJSON_recettes = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.line(df, x="week_year", y="rank", title='Evolution du classement par semaine',labels={
                     "rank": "Classement",
                     "week_year": "Numéro et année de la semaine"
                 }, markers=True)  
    graphJSON_rank = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    if (df['nbCinemas'].isnull().values.any()):
        graphJSON_cinemas = None
    else :
        # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
        fig = px.line(df, x="week_year", y="nbCinemas", title='Evolution du nombre de cinémas projetant le film par semaine',labels={
                        "nbCinemas": "Nombre de cinémas",
                        "week_year": "Numéro et année de la semaine"
                    }, markers=True)  
        graphJSON_cinemas = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('movie_detail.html', details=details,graphJSON_cumul=graphJSON_cumul,graphJSON_recettes=graphJSON_recettes,graphJSON_rank=graphJSON_rank,graphJSON_cinemas=graphJSON_cinemas)


"""
    Page "Classement des films".
    Permet d'afficher le classement des films en fonction de l'année à étudier qui se choisie en déroulant le menu en haut à droite et à valider en cliquant sur "Go".
    Il est aussi possible de choisir "Tous les temps" pour avoir le classement général toutes années confondues.
"""
@app.route('/movie-ranking', methods= ['GET'])
def movie_ranking():
    form = yearForm()
    year  = request.args.get('input')
    if year ==  None :
        year =  0

    if  int(year) < 2007 :
        title = "Classement des revenus depuis 2007"
    else:
        title = "Classement des revenus pour l'année "+year

    return render_template('ranking_movies.html', form=form,title=title, list=getMovieRanking(year))

"""
    Page "Recherche des films".
    Permet d'effectuer une recherche pour avoir une correspondance entre le nom cherché est ceux dans la base de données.
    Affiche les films correspondants au nom mis en recherche.
"""
@app.route('/movie-search', methods= ['GET'])
def movie_search():
    form = textForm()
    
    text  = request.args.get('input')
    if text != None : 
        title = "Résultats de recherche pour : "+text+""
        list=searchMovies(text)
    else : 
        text=""
        title  = "Recherche d'un film"
        list = []


    return render_template('movie_search.html',title=title, form=form,list=list)

"""
    Page "Recherche d'acteurs".
    Permet d'effectuer une recherche pour avoir une correspondance entre le nom cherché est ceux dans la base de données.
    Affiche les acteurs correspondants au nom mis en recherche.
"""
@app.route('/actor-search', methods= ['GET'])
def actor_search():
    form = textForm()
    
    text  = request.args.get('input')
    if text != None : 
        title = "Résultats de recherches pour : "+text+""
        list=searchActor(text)
    else : 
        text=""
        title  = "Recherche d'un(e) acteur/actrice"
        list=[]


    return render_template('actor_search.html',title=title, form=form,actor=text,list=list)


def orderMovieDetail(movies):
    movies = sorted(movies, key=lambda d: datetime.strptime(d["rlDate"], '%b %d, %Y'),reverse=True)     
    return movies

"""
    Page "actor-detail".
    Permet d'afficher les détails sur l'acteur/actrice choisi(e).
"""
@app.route('/actor-detail/<actorName>/<actorId>')
def actor_detail(actorName,actorId):


    details = getActorDetail(actorName,actorId)

    details["movies"] = orderMovieDetail(details["movies"])

    genres_list = []
    for movie in details["movies"]:
        genres_list.append(movie["genres"])

    genres_counter = Counter(list(chain(*genres_list)))

    sum_recettes_fr = sum(movie["_id"]['recettes_totales'] for movie in getSumRecettesActor(actorName,actorId))
    sum_recettes_inter = sum(movie["_id"]['recettes_inter'] for movie in getSumRecettesActor(actorName,actorId))

    dict_genres = {"genres" : genres_counter.keys(),"values":genres_counter.values()}
    fig = px.pie(dict_genres, names="genres", values='values',title="Répartition de ses genres de films favoris",color_discrete_sequence=px.colors.sequential.RdBu)
    graphJSON_genres = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


    df = getActorEvolution(actorName,actorId)


    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.line(df, x="year", y="recettes", title='Recettes générées par an',labels={
                     "recettes": "Recettes, en $",
                     "year": "Année"
                 }, markers=True)  
    graphJSON_evolution = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


    return render_template('actor_detail.html',actorName = actorName,details=details,sum_recettes_fr=sum_recettes_fr,sum_recettes_inter=sum_recettes_inter,genres_counter=genres_counter,graphJSON_genres=graphJSON_genres,graphJSON_evolution=graphJSON_evolution)

"""
    Page "Classement des acteurs".
    Permet d'afficher le classement des films en fonction de l'année à étudier qui se choisie en déroulant le menu en haut à droite et à valider en cliquant sur "Go".
    Il est aussi possible de choisir "Tous les temps" pour avoir le classement général toutes années confondues.
"""
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

"""
    Page "Autres classements".
    Permet d'afficher des bar charts en fonction de l'année tels que : 
        - les recettes générées par genre ;
        - les recettes générées en fonction de la note IMDB des films ;
        - les recettes générées par semaine ;
        - les recettes générées par distributeur de films.
    Il est possible de sélectionner l'année pour laquelle nous voulons tracer les bar charts, il est aussi possible de tracer ces bar charts pour tous les temps.
"""
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

    # Trace un bar chart des recettes générées en fonction du genre des films.
    recettesGenre = getRecettesByGenres(year)
    df = pd.DataFrame(recettesGenre)
    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.bar(df, x="_id", y="recettes_totales", title='Recettes générées par genre',labels={
                     "recettes_totales": "Recettes, en $",
                     "_id": "Genre"
                 })  
    fig.update_xaxes(tickangle=45)
    graphJSON_genres = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Trace un bar chart des recettes générées en fonction de la note IMDB du film.
    recettesNote = getRecettesByNote(year)
    df = pd.DataFrame(recettesNote)
    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.bar(df, x="_id", y="recettes_totales", title='Recettes générées par note IMDB',labels={
                     "recettes_totales": "Recettes, en $",
                     "_id": "Note"
                 })  
    graphJSON_note = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Trace un bar chart des recettes générées en fonction des semaines.
    recettesWeek = getRecettesByWeek(year)
    df = pd.DataFrame(recettesWeek)
    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.bar(df, x="_id", y="recettes_totales", title='Recettes générées par semaine de l\'année',labels={
                     "recettes_totales": "Recettes, en $",
                     "_id": "Semaine"
                 })  
    graphJSON_week = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Trace un bar chart des recettes générées en fonction du distributeur de films.
    recettesDistributor = getRecettesByDistributor(year)
    df = pd.DataFrame(recettesDistributor)
    df = df.query("_id != 'N/A'")
    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    fig = px.bar(df, x="_id", y="recettes_totales", title='Recettes générées par distributeur de films',labels={
                     "recettes_totales": "Recettes, en $",
                     "_id": "Distibuteur"
                 })  
    fig.update_xaxes(tickangle=45)
    graphJSON_distributor = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    
    

    return render_template('other-ranking.html', form=form,title=title,graphJSON_genres=graphJSON_genres,graphJSON_note=graphJSON_note,graphJSON_week=graphJSON_week,graphJSON_distributor=graphJSON_distributor)



@app.errorhandler(404)
def page_not_found(e):
    return redirect("/")


def loginDataBase():
    
    import pymongo
    client = pymongo.MongoClient("mongo_app")
    database = client['boxoffice']
    collection = database['scrapy_items']
    return collection



if __name__ == '__main__':
    collection = loginDataBase()
    
    app.run(debug=True,host="0.0.0.0" ,port=8050) 
