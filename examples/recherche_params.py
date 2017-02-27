
from soccersimulator import settings
from soccersimulator import SoccerTeam, Simulation, Strategy, show_simu, Vector2D, SoccerAction


import numpy as np
import logging

logger = logging.getLogger("simuExpe")

"""
Controleur de simulation pour le test d'une liste de parametres
Exemple sur le tir
"""

class ShootSearch(object):
    """ nombre d'iterations maximales jusqu'a l'arret d'un round
        discr_step  : pas de discretisation du parametre
        nb_essais : nombre d'essais par parametre
    """
    MAX_STEP = 40
    def __init__(self):
        self.strat = ShootExpe()
        team1 = SoccerTeam("test")
        team1.add("Expe",self.strat)
        team2 = SoccerTeam("test2")
        team2.add("Nothing",Strategy())
        self.simu = Simulation(team1,team2,max_steps=1000000)
        self.simu.listeners+=self
        self.discr_step = 10
        self.nb_essais = 10
    def start(self,visu=True):
        """ demarre la visualisation avec ou sans affichage"""
        if visu :
            show_simu(self.simu)
        else:
            self.simu.start()
    def begin_match(self,team1,team2,state):
        """ initialise le debut d'une simulation
            res : dictionnaire des Resultats
            last : step du dernier round pour calculer le round de fin avec MAX_STEP
            but : nombre de but pour ce parametre
            cpt : nombre d'essais pour ce parametre
            params : liste des parametres a tester
            idx : identifiant du parametre courant
        """
        self.res = dict()
        self.last = 0
        self.but = 0
        self.cpt = 0
        self.params = [x for x in  np.linspace(1,settings.maxPlayerShoot,self.discr_step)]
        self.idx=0

    def begin_round(self,team1,team2,state):
        """ engagement : position random du joueur et de la balle """
        position = Vector2D(np.random.random()*settings.GAME_WIDTH/2.+settings.GAME_WIDTH/2.,np.random.random()*settings.GAME_HEIGHT)
        self.simu.state.states[(1,0)].position = position.copy()
        self.simu.state.states[(1,0)].vitesse = Vector2D()
        self.simu.state.ball.position = position.copy()
        self.strat.norm = self.params[self.idx]
        self.last = self.simu.step
    def update_round(self,team1,team2,state):
        """ si pas maximal atteint, fin du tour"""
        if state.step>self.last+self.MAX_STEP:
            self.simu.end_round()
    def end_round(self,team1,team2,state):
        if state.goal>0:
            self.but+=1
        self.cpt+=1
        if self.cpt>=self.nb_essais:
            self.res[self.params[self.idx]] = self.but*1./self.cpt
            logger.debug("parametre %s : %f" %((str(self.params[self.idx]),self.res[self.params[self.idx]])))
            self.idx+=1
            self.but=0
            self.cpt=0
        """ si plus de parametre, fin du match"""
        if self.idx>=len(self.params):
            self.simu.end_match()


class ShootExpe(Strategy):
    def __init__(self,shoot=None):
        self.name = "simple action"
        self.norm = 0
    def compute_strategy(self,state,id_team,id_player):
        shoot = Vector2D(settings.GAME_WIDTH,settings.GAME_HEIGHT/2.)-state.player_state(id_team,id_player).position
        shoot = shoot.normalize()*self.norm
        return SoccerAction(Vector2D(),shoot)

expe = ShootSearch()
expe.start()
