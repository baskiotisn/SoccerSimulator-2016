from soccersimulator import Strategy
import numpy as np
from sklearn.tree import DecisionTreeClassifier
import logging
import sklearn
logger = logging.getLogger("arbrestrategie")

if sklearn.__version__ != "0.18.1":
    print("Updater sklearn !! (pip install -U sklearn --user )")


def build_apprentissage(states_tuple,get_features):
    res = []
    labels = []
    for state,info in states_tuple:
        res.append(get_features(state,info[0],info[1]))
        labels.append(info[2])
    """ transformation en matrice numpy """
    return np.array(res),np.array(labels)

def affiche_arbre(tree):
    long = 10
    sep1="|"+"-"*(long-1)
    sepl="|"+" "*(long-1)
    sepr=" "*long
    def aux(node,sep):
        if tree.tree_.children_left[node]<0:
            ls ="(%s)" % (", ".join( "%s: %d" %(tree.classes_[i],int(x)) for i,x in enumerate(tree.tree_.value[node].flat)))
            return sep+sep1+"%s\n" % (ls,)
        return (sep+sep1+"X%d<=%0.2f\n"+"%s"+sep+sep1+"X%d>%0.2f\n"+"%s" )% \
                    (tree.tree_.feature[node],tree.tree_.threshold[node],aux(tree.tree_.children_left[node],sep+sepl),
                    tree.tree_.feature[node],tree.tree_.threshold[node],aux(tree.tree_.children_right[node],sep+sepr))
    return aux(0,"")




class DTreeStrategy(Strategy):
    def __init__(self,tree,dic,get_features):
        super(DTreeStrategy,self).__init__("Tree Strategy")
        self.dic = dic
        self.tree = tree
        self.get_features= get_features
    def compute_strategy(self, state, id_team, id_player):
        label = self.tree.predict([self.get_features(state,id_team,id_player)])[0]
        if label not in self.dic:
            logger.error("Erreur : strategie %s non trouve" %(label,))
            return SoccerAction()
        return self.dic[label].compute_strategy(state,id_team,id_player)
