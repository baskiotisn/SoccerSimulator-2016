# -*- coding: utf-8 -*-
from .mdpsoccer import SoccerAction
from .utils import Vector2D
##############################################################################
# SoccerStrategy
##############################################################################

class Strategy(object):
    """ Strategie : la fonction compute_strategie est interroge a chaque tour de jeu, elle doit retourner un objet
    SoccerAction
    """
    def __init__(self, name="Vide"):
        """
        :param name: nom de la strategie
        :return:
        """
        self.name = name

    def compute_strategy(self, state, id_team, id_player):
        """ Fonction a implementer pour toute strategie
        :param state: un objet SoccerState
        :param id_team: 1 ou 2
        :param id_player: numero du joueur interroge
        :return:
        """
        return SoccerAction()

    def begin_match(self, team1, team2, state):
        """  est appelee en debut de chaque match
        :param team1: nom team1
        :param team2: nom team2
        :param state: etat initial
        :return:
        """
        pass

    def begin_round(self, team1, team2, state):
        """ est appelee au debut de chaque coup d'envoi
        :param team1: nom team 1
        :param team2: nom team 2
        :param state: etat initial
        :return:
        """
        pass

    def end_round(self, team1, team2, state):
        """ est appelee a chaque but ou fin de match
        :param team1: nom team1
        :param team2: nom team2
        :param state: etat initial
        :return:
        """
        pass

    def update_round(self, team1, team2, state):
        """ est appelee a chaque tour de jeu
        :param team1: nom team 1
        :param team2: nom team 2
        :param state: etat courant
        :return:
        """
        pass

    def end_match(self, team1, team2, state):
        """ est appelee a la fin du match
        :param team1: nom team 1
        :param team2: nom team 2
        :param state: etat courant
        :return:
        """
        pass

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self.__class__).split(".")[-1]+": "+ self.__str__()

class KeyboardStrategy(Strategy):

    def __init__(self,name="KBCommande",fn=None,reset=True):
        super(Strategy,self).__init__(name)
        self.fn = fn
        self.dic_keys=dict()
        self.cur = None
        self.states=[]
        self.state=None

    def add(self,key,strategy):
        self.dic_keys[key]=strategy
        if not self.cur:
            self.cur = key
            self.name = strategy.name

    def compute_strategy(self,state,id_team,id_player):
        self.state = state
        return self.dic_keys[self.cur].compute_strategy(state,id_team,id_player)

    def listen(self,key,teamid,player):
        if not self.state:
            return
        if key in self.dic_keys.keys():
            self.cur=key
            self.name = self.dic_keys[self.cur].name
            self.states.append((self.state, (teamid,player,self.name)))

    def begin_match(self,team1,team2,state):
        if self.reset:
            self.states=[]

    def end_match(self, team1, team2, state):
        self.write()

    def to_str(self):
        ### A REFAIRE #####
        return "\n".join("%d,%d,%s|%s" % (k[0],k[1],k[2],s.to_str()) for s,k in self.states)

    def write(self,fn=None,append = True):
        mode = "w"
        if append:
            mode = "a"
        if not fn:
            fn = self.fn
        if not fn:
            return
        with open(fn,mode) as f:
            f.write(self.to_str()+"\n")

    @classmethod
    def from_str(cls,strg):
        res = []
        for l in strg.split("\n") :
            if len(l):
                info=l[:l.index("|")].split(",")
                state=l[l.index("|")+1:]
                res.append(((int(info[0]),int(info[1]),info[2]),SoccerState.from_str(state)))
        return res
    @classmethod
    def read(cls,fn):
        with open(fn) as f:
            return cls.from_str(f.read())
