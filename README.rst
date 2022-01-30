=========================
Projet de DataEngineering
auteurs : DANG Méline et VAN ROOIJ Théo
=========================


Nous avons choisi d'étudier les données de BoxOffice en France. Ces données sont issues du site suivant :
 `https://www.boxofficemojo.com/ <https://www.boxofficemojo.com/>`_
A ces données, on vient ajouter plus de détails sur le film extraits depuiis sa page IMDB : `https://www.imdb.com/ <https://www.imdb.com/>`_

Lancement de l'application
==========================

Pour lancer notre application il suffit d'éxécuter les commandes suivantes : 

.. code-block:: bash

    $:~/> cd <WORKDIR>
    $:~/<WORKDIR> > git clone https://github.com/theovanrooij/projet_DSIA_4201C.git
    $:~/<WORKDIR> > cd projet_DSIA_4201C/
    $:~/<WORKDIR> > docker-compose up -d


Nous vous conseillons de lancer l'application et de profiter du temps de construction (build) pour lire la documentation suivante.


Developper guide
================

Explication de l'arborescence
-----------------------------

Vous pouvez remarquer la présence de 3 dossiers dans notre arborescence :
    - " app " contient tous les fichiers relatifs à l'application python en elle-même (templates, css, fichier lançant le serveur Flask, ...) ;
    - " scrapy_folder " contient, comme son nom l'indique, tous les fichiers relative au lancement des scraping avec scrapy ;
    - " mongo_feed " contient les fichiers permettant, lors du lancement de l'application, le téléchargement et la restauration de la dernière backup de la base de données stockée à l'adresse suivante : `https://perso.esiee.fr/~vanrooit/DataEngineering/ <https://perso.esiee.fr/~vanrooit/DataEngineering/>`.


Fonctionnement de scrappy 
-------------------------

Notre projet comporte deux spiders :
    - boxoffice vient scrap le site `https://www.boxofficemojo.com/ <https://www.boxofficemojo.com/>` ;
    - imdb vient scrap le site `https://www.imdb.com/ <https://www.imdb.com/>`.

La spider boxoffice est la première à être éxécutée et vient récupérer les données concernant les recettes pour chacune des semaines, à partir de la dernière semaine ayant été scrap (nous récupérons cette information depuis la base de données).
Une fois cette spider exécutée, imdb prend le relais en venant récupérer l'id des releases (=versions d'un film) dont les informations complémentaires sont manquantes afin d'aller les scrap sur le site `https://www.imdb.com/ <https://www.imdb.com/>`.


Structure d'un document de la base de données
---------------------------------------------
Les données précédemment récupérées sont stockées dans une base de données mongoDB. Nous avons choisi de n'utiliser qu'une seule collection. La structure d'un de ses documents est la suivante (chaque document correspond à un film sur une semaine précise) : 

    - year : Année de la semaine scrap ;
    - week : Semaine venant d'être scrap ;
    - week_year : Combinaison des deux champs précédents ;
    - rank : Classement sur la semaine en question ;
    - rank_last_week : Classement de la semaine précédente ;
    - title : Titre du film ;
    - recettes : Recettes en France sur la semaine en question ;
    - boxDiff : Evolution des recettes par rapport à la semaine précédente ;
    - recettes_cumul : Recettes en France cumulées entre la date de sortie et la semaine en question ;
    - nbCinemas : Nombre de cinémas diffusant le film pour cette semaine ;
    - cinemasDiff : Différence du nombre de cinémas par rapport à la semaine précédente ;
    - nbWeeks : Nombre de semaines depuis la première semaine de diffusion.

    Les champs suivants sont issus de l'ajout de données depuis imdb : 

    - distributor : Studio de cinéma du film ;
    - releaseID : Id de la release (version du film) ;
    - budget ;
    - cast : Liste contenant chaque acteur du film avec les champs suivants pour chacun d'entre eux :
      - name : Nom de l'acteur/actrice ;
      - role : Rôle tenu par l'acteur/actrice dans le film ;
      - actorId : ID de l'acteur/actrice ;
      - img_link : Lien vers une photo de l'acteur ;
    - note : Note IMDB du film ;

    - country_origin : Pays d'origine du film ;
    - director : Réalisateur du film ;
    - genres : Liste contenant les genres du film ;
    - poster : Lien vers l'affiche du film ;
    - recettes_inter : Recettes totales en incluant l'Internationale sur toute la durée d'exploitation du film (y compris les semaines futures) ;
    - recettes_totales : Recettes totales en France sur toute la durée d'exploitation du film (y compris les semaines futures) ;
    - releasedate : Date de sortie du film ;
    - resume : Résumé de l'intrigue ;
    
    - runningTime : Durée du film.
    

Fonctionnement des containers Docker
------------------------------------

Comme indiqué précédemment, nous utilisons docker pour lancer notre application.
Notre application comporte 4 containers : 
    - " mongo " permet comme son nom l'indique de lancer la base de donnée MongoDB ;
    - " app " lance l'application web ;
    - " mongo_feed" télécharge la dernière backup de la base de donnée et la charge dans le container mongo ;
    - " notebook " permet le lancement d'un environnement jupyter notebook.

Ces containers sont tous lancés par le fichier docker-compose.yml, présent à la racine de notre répertoire.
Tous les containers, à l'exception de "mongo", contiennent un DockerFile présent dans leur dossier respectif permettant l'installation de leurs dépendances.

Les containers "app" et "mongo_feed" se lancent chacun sur un fichier bash permettant le lancement des actions nécessaires au bon fonctionnement de l'application.

Comme expliqué précédemment le fichier bash de "mongo_feed" vient peupler la base de données. Au lancement de "app", le fichier launchApp est éxécuté. ce fichier va éxécuter deux scripts python. Le premier, launchSpider.py présent dans scrapy_folder, va vérifier que la base de données est complète puis va venir réaliser un nouveau scrap pour les semaines écoulées depuis la dernière mise à jour. Une fois ce scrap réalisé, le script bash vient lancer notre application en éxécutant app.py, présent dans le dossier app.


User Guide
==========

Plusieurs fonctionalitées sont disponibles.

Classement des films
--------------------

Sur cette page vous allez retrouver, comme son nom l'indique, un classement des films en fonction de leurs recettes au box office.
Pour chaque film, vous pouvez voir son nom, sa date de sortie ainsi que les recettes générées. 
Vous pouvez également choisir, à l'aide du menu en haut à droite de votre écran, l'année d'étude souhaitée. Par défaut, les recettes depuis 2007 sont affichées (premières données disponibles dans notre base de données).
Enfin, en cliquant sur le nom du film, vous êtes redirigés vers une page affichant plus de détails sur le film en question.

Classement des acteurs et actrices
-----------------------

Cette page est similaire à la précédente à la différence que ce sont les acteurs et non les films qui sont affichés.


Recherche de film
-----------------

Sur cette page vous pouvez chercher un film en particulier par son nom. Tous les films ayant un nom contenant la valeur voulue sont affichés. 
En cliquant sur le film, vous êtes redirigés vers sa page détaillée.
Ex : En recherchant "Star Wars", cela vient afficher tous les Star Wars sortis depuis 2007. 


Recherche d'acteur
-----------------

Cette page est similaire à la précédente à la différence que ce sont les acteurs et non les films qui sont affichés.
En cliquant sur le nom de l'acteur, vous êtes redirigés vers sa page détaillée.
En cliquant sur un nom de film, vous êtes redirigés vers sa page détaillée.

Détails d'un film
----------------

Comme son nom l'indique cette page affiche toutes les informations que nous avons sur le film en question, à savoir :
    - Résumé de l'intrigue ;
    - Durée du film ;
    - Recettes françaises et pourcentage réalisés en France ;
    - Recettes Totales ;
    - Budget estimé ;
    - Réalisateur ;
    - Note IMDB ;
    - Distributeur ;
    - Date de sortie ;
    - Pays d'origine ;
    - Genres du film ;
    - Liste des acteurs (en cliquant sur un acteur nous sommes envoyés sur sa page détaillée).

Nous retrouvons en plus de cela des graphiques : 
    - Le premier affiche l'évolution des recettes cumulées pour chaque semaine ;
    - Le second affiche les recettes par semaine ;
    - Le troisième affiche l'évolution du classement du film au box office ;
    - Le dernier graphique affiche l'évolution du nombre de cinémas diffusant le film. Il n'est en revanche pas toujours affiché car certaines données ne sont pas disponibles sur le site d'origine.

Détails d'un acteur
------------------

Cette page affiche toutes les données disponibles d'un(e) acteur/actrice.

Nous y retrouvons : 
    - Les recettes qu'il/elle a généré en France et à l'Internationale ;
    - La liste des films, classés par ordre anti-chronologique, dans lesquels il/elle a joué (en cliquant sur un film vous êtes redirigés vers sa page détaillée) ;
    - Un pie chart affichant la répartition des genres de films dans lesquels l'acteur/atrice a le plus joué ;
    - L'évolution des recettes générées en France par année.


Autres classements
------------------

Sur cette page vous pouvez retrouver 4 graphiques affichant les recettes générés par : 
    - les différents genres ;
    - les différents distributeurs ;
    - les différentes notes ;
    - les différentes semaine de l'année.

Comme pour les autres classements, vous pouvez choisir l'année d'étude.

