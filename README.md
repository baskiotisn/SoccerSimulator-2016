UE 2I013 - Projet - UPMC
==================================

Le dépôt contient :
* [soccersimulator](https://github.com/baskiotisn/SoccerSimulator/tree/master/soccersimulator) : le module python coeur du projet (objets, simulation, visualisation)
* [docs](https://github.com/baskiotisn/SoccerSimulator/tree/master/docs) : le cours et les tutoriels.
* [examples](https://github.com/baskiotisn/SoccerSimulator/tree/master/docs) : scripts d'exemples
* [resultats](https://github.com/baskiotisn/SoccerSimulator/tree/master/resultats) : le progres hebdomadaire et les liens vers les replays.

Installation
============
Une installation "editable" est conseillée vu les mises-à-jour très régulières du module
```
pip install -e <path/url> --user 
```

Soumission
===========
Votre dépôt github doit obligatoirement être sous la forme d'un module python (donc avec un fichier `__init__.py`) qui contient une fonction `get_team(i)` qui renvoie l'équipe à `i` joueurs.
