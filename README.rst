AJOUTER %age fr vs inter pour film / acteur
regex acteur
regardez pour vrai sous par an pour acteur

=========================
Projet de DataEngineering
=========================


Lancement de l'application
==========================

Pour lancer notre application rien de plus que d'éxécuter les commandes suivantes : 

.. code-block:: bash

    $:~/> cd <WORKDIR>
    $:~/<WORKDIR> > git clone https://github.com/theovanrooij/projet_DSIA_4201C.git
    $:~/<WORKDIR> > cd projet_DSIA_4201C/
    $:~/<WORKDIR> > docker-compose up -d


Developper guide
================

- dossier app contient tout l'aspect en lien avec l'utilisateur et un docker file permettant de dockerisé l'app au lancement elle vient lancer un scrap des dernière données disponible puis après lance l'appli

- scrapy_folder contient les deux spiiders + fichier permettant le scrapping auto
 - box office commence par récupérer toutes les données concernant les recettes engendrés
 - imdb va ensuite récupéré tous les ids de films récupérés précédemment et scraap imdb pour ajouter donnée complémentaire

une seule collection est utilisé
structure d'un document : 
 - title
 - id de la release
 - ...

mongo_feed = docker file + fichier bash permettant le téléchargement de la dernièire backup de la BDD


User Guide
==========

plusieurs fonction : 
 - classement des acteurs en fonction de l'année voulu
 - classement des films en fonction de l'année voulu
 - recherche d'un film en particulier par son nom
 - recherche d'un acteur en particulier par son nom
 - pour un film donné list des acteurs, résumé, durée, recettes fr et inter et quelques graphiques
 - pour un acteur liste des films, recettes par année, ses genres préférés

- other ranking