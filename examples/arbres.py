from soccersimulator import settings,SoccerTeam, Simulation, show_simu, KeyboardStrategy
from soccersimulator import Strategy, SoccerAction, Vector2D, load_jsonz,dump_jsonz,Vector2D
import logging
from arbres_utils import build_apprentissage,affiche_arbre,DTreeStrategy
from sklearn.tree 	import export_graphviz
from sklearn.tree import DecisionTreeClassifier
## Strategie aleatoire
class FonceStrategy(Strategy):
    def __init__(self):
        super(FonceStrategy,self).__init__("Fonce")
    def compute_strategy(self,state,id_team,id_player):
        return SoccerAction(state.ball.position-state.player_state(id_team,id_player).position,\
                Vector2D((2-id_team)*settings.GAME_WIDTH,settings.GAME_HEIGHT/2.)-state.ball.position)

class StaticStrategy(Strategy):
    def __init__(self):
        super(StaticStrategy,self).__init__("Static")
    def compute_strategy(self,state,id_team,id_player):
        return SoccerAction()

#######
## Constructioon des equipes
#######

team1 = SoccerTeam("team1")
strat_j1 = KeyboardStrategy()
strat_j1.add('a',FonceStrategy())
strat_j1.add('z',StaticStrategy())
strat_j2 = KeyboardStrategy()
strat_j2.add('q',FonceStrategy())
strat_j2.add('s',StaticStrategy())
team1.add("Jexp 1",strat_j1)
team1.add("Jexp 2",strat_j2)

team2 = SoccerTeam("team2")
team2.add("rien 1", StaticStrategy())
team2.add("rien 2", StaticStrategy())

simu = Simulation(team1,team2)
show_simu(simu)

# recuperation de tous les etats sur les 2 joueurs
training_states = strat_j1.states+strat_j2.states
# sauvegarde dans un fichier
dump_jsonz(training_states,"test_states.jz")

### chargement d'un fichier sauvegarder
states_tuple = load_jsonz("test_states.jz")


### Transformation d'un etat en features
def my_get_features(state,idt,idp):
    """ extraction du vecteur de features d'un etat, ici distance a la balle, distance au but, distance balle but """
    p_pos= state.player_state(idt,idp).position
    f1 = p_pos.distance(state.ball.position)
    f2= p_pos.distance( Vector2D((2-idt)*settings.GAME_WIDTH,settings.GAME_HEIGHT/2.))
    f3 = state.ball.position.distance(Vector2D((2-idt)*settings.GAME_WIDTH,settings.GAME_HEIGHT/2.))
    return [f1,f2,f3]
#Nom des features (optionel)
my_get_features.names = ["ball_dist","goal_dist","ballgoal_dist"]

#####
## Apprentissage de l'arbre
######
data_train, data_labels = build_apprentissage(states_tuple,my_get_features)
dt = DecisionTreeClassifier()
# apprentissage de l'arbre
dt.fit(data_train,data_labels)

####
# Visualisation de l'arbre
###
affiche_arbre(dt)

## exporter l'arbre en .dot
with file("arbre.dot","w") as fn:
        export_graphviz(dt,fn,class_names = dt.classes_,feature_names=getattr(my_get_features,"names",None), filled = True,rounded=True)
    ## puis utiliser ou dot -Tpdf -o tree.pdf tree.dot pour convertir
    ## ou aller sur http://www.webgraphviz.com/ et copier le fichier .dot
    ## puis pour utiliser :


####
# Utilisation de l'arbre
###
dic = {"Fonce":FonceStrategy(),"Static":StaticStrategy()}
treeStrat = DTreeStrategy(dt,dic,my_get_features)
team3 = SoccerTeam("Arbre Team")
team3.add("Joueur 1",treeStrat)
team3.add("Joueur 2",treeStrat)
simu = Simulation(team2,team3)
show_simu(simu)
