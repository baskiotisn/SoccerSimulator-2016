# -*- coding: utf-8 -*-<
import math
import threading
from collections import namedtuple
from threading import Lock
from copy import deepcopy
from .utils import Vector2D, MobileMixin, JSONable
from .events import SoccerEvents
from . import settings
import random
import time
import zipfile
import traceback


###############################################################################
# SoccerAction
###############################################################################


class SoccerAction(JSONable):
    """ Action d'un joueur : comporte un vecteur acceleration et un vecteur shoot.
    """
    def __init__(self, acceleration=None, shoot=None):
        self.acceleration = acceleration or Vector2D()
        self.shoot = shoot or Vector2D()
    def copy(self):
        return deepcopy(self)
    def to_str(self):
        return self.__str__()
    def __str__(self):
        return "Acc:%s, Shoot:%s" % (str(self.acceleration), str(self.shoot))
    def __repr__(self):
        return "SoccerAction(%s,%s)" % (self.acceleration.__repr__(),self.shoot.__repr__())
    def __eq__(self, other):
        return (other.acceleration == self.acceleration) and (other.shoot == self.shoot)
    def __add__(self, other):
        return SoccerAction(self.acceleration + other.acceleration, self.shoot + other.shoot)
    def __sub__(self, other):
        return Vector2D(self.acceleration - other.acceleration, self.shoot - other.shoot)
    def __iadd__(self, other):
        self.acceleration += other.acceleration
        self.shoot += other.shoot
        return self
    def __isub__(self, other):
        self.acceleration -= other.acceleration
        self.shoot -= other.shoot
        return self

###############################################################################
# Ball
###############################################################################
class Ball(MobileMixin):
    def __init__(self,*args,**kwargs):
        MobileMixin.__init__(self,*args,**kwargs)

    def next(self,sum_of_shoots):
        vitesse = self.vitesse.copy()
        vitesse.norm = self.vitesse.norm - settings.ballBrakeSquare * self.vitesse.norm ** 2 - settings.ballBrakeConstant * self.vitesse.norm
        ## decomposition selon le vecteur unitaire de ball.speed
        snorm = sum_of_shoots.norm
        if snorm > 0:
            u_s = sum_of_shoots.copy()
            u_s.normalize()
            u_t = Vector2D(-u_s.y, u_s.x)
            speed_abs = abs(vitesse.dot(u_s))
            speed_ortho = vitesse.dot(u_t)
            speed_tmp = Vector2D(speed_abs * u_s.x - speed_ortho * u_s.y, speed_abs * u_s.y + speed_ortho * u_s.x)
            speed_tmp += sum_of_shoots
            vitesse = speed_tmp
        self.vitesse = vitesse.norm_max(settings.maxBallAcceleration).copy()
        self.position += self.vitesse
    def inside_goal(self):
        return (self.position.x <= 0 or self.position.x >= settings.GAME_WIDTH) and abs(self.position.y - (settings.GAME_HEIGHT / 2.)) < settings.GAME_GOAL_HEIGHT / 2.
    def __repr__(self):
        return "Ball(%s,%s)" % (self.position.__repr__(),self.vitesse.__repr__())
    def __str__(self):
        return "Ball: pos: %s, vit: %s" %(str(self.position),str(self.vitesse))

###############################################################################
# PlayerState
###############################################################################

class PlayerState(MobileMixin):
    """ Represente la configuration d'un joueur : un etat  mobile (position, vitesse), et une action SoccerAction
    """

    def __init__(self, **kwargs):
        """
        :param position: position du  joueur
        :param acceleration: acceleration du joueur
        :param action: action SoccerAction du joueur
        :return:
        """
        MobileMixin.__init__(self,kwargs.pop('position',Vector2D()),kwargs.pop('vitesse',Vector2D()))
        self.action = kwargs.pop('action', SoccerAction())
        self._last_shoot = kwargs.pop('last_shoot', 0)
        self.__dict__.update(kwargs)

    def __str__(self):
        return "vit: %s, acc:%s, action:%s" %(str(self.position),str(self.acceleration),str(self.action))
    def __repr__(self):
        return "PlayerState(position=%s,acceleration=%s,action=%s,last_shoot=%d)" %  \
                            (self.position.__repr__(),self.acceleration.__repr__(),self.action.__repr__(),self._last_shoot)
    @property
    def acceleration(self):
        """
        :return: Vector2D Action acceleration du joueur
        """
        return self.action.acceleration.norm_max(settings.maxPlayerAcceleration)

    @acceleration.setter
    def acceleration(self,v):
        self.action.acceleration = v

    @property
    def shoot(self):
        """ Vector2D Action shoot du joueur
        :return:
        """
        return self.action.shoot.norm_max(settings.maxPlayerShoot)

    @shoot.setter
    def shoot(self,v):
        self.action.shoot = v

    def next(self, ball, action=None):
        """ Calcul le prochain etat en fonction de l'action et de la position de la balle
        :param ball:
        :param action:
        :return: Action shoot effectue
        """
        if not (hasattr(action,"acceleration") and hasattr(action,"shoot")):
            action = SoccerAction()
            #print("Warning : mauvais SoccerAction")
        self.action = action.copy()
        self.vitesse *= (1 - settings.playerBrackConstant)
        self.vitesse = (self.vitesse + self.acceleration).norm_max(settings.maxPlayerSpeed)
        self.position += self.vitesse
        if self.position.x < 0 or self.position.x > settings.GAME_WIDTH \
                or self.position.y < 0 or self.position.y > settings.GAME_HEIGHT:
            self.position.x = max(0, min(settings.GAME_WIDTH, self.position.x))
            self.position.y = max(0, min(settings.GAME_HEIGHT, self.position.y))
            self.vitesse = Vector2D()
        if self.shoot.norm == 0 or not self.can_shoot():
            self._dec_shoot()
            return Vector2D()
        self._reset_shoot()
        if self.position.distance(ball.position) > (settings.PLAYER_RADIUS + settings.BALL_RADIUS):
            return Vector2D()
        return self._rd_angle(self.shoot,(self.vitesse.angle-self.shoot.angle),self.position.distance(ball.position)/(settings.PLAYER_RADIUS+settings.BALL_RADIUS))

    @staticmethod
    def _rd_angle(shoot,dangle,dist):
        eliss = lambda x, alpha: (math.exp(alpha*x)-1)/(math.exp(alpha)-1)
        dangle = abs((dangle+math.pi*2) %(math.pi*2) -math.pi)
        dangle_factor =eliss(1.-max(dangle-math.pi/2,0)/(math.pi/2.),5)
        norm_factor = eliss(shoot.norm/settings.maxPlayerShoot,4)
        dist_factor = eliss(dist,10)
        angle_prc = (1-(1.-dangle_factor)*(1.-norm_factor)*(1.-0.5*dist_factor))*settings.shootRandomAngle*math.pi/2.
        norm_prc = 1-0.3*dist_factor*dangle_factor
        return Vector2D(norm=shoot.norm*norm_prc,
                        angle=shoot.angle+2*(random.random()-0.5)*angle_prc)

    def can_shoot(self):
        """ Le joueur peut-il shooter
        :return:
        """
        return self._last_shoot <= 0

    def _dec_shoot(self):
        self._last_shoot -= 1

    def _reset_shoot(self):
        self._last_shoot = settings.nbWithoutShoot

    def copy(self):
        return deepcopy(self)

###############################################################################
# SoccerState
###############################################################################

class SoccerState(JSONable):
    """ Etat d'un tour du jeu. Contient la balle, l'ensemble des etats des joueurs, le score et
    le numero de l'etat.
    """
    def __init__(self, **kwargs):
        self.states = kwargs.pop('states', dict())
        self.strategies = kwargs.pop('strategies',dict())
        self.ball = kwargs.pop('ball', Ball())
        self._score = kwargs.pop('score', {"1": 0, "2": 0})
        self.step = kwargs.pop('step', 0)
        self.max_steps = kwargs.pop('max_steps', settings.MAX_GAME_STEPS)
        self._goal = kwargs.pop('goal', 0)
        self.__dict__.update(kwargs)

    def __str__(self):
        return ("Step: %d, %s " %(self.step,str(self.ball)))+\
               " ".join("(%d,%d):%s" %(k[0],k[1],str(p)) for k,p in sorted(self.states.items()))+\
               (" score : %d-%d" %(self.score_team1,self.score_team2))
    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return dict(states=dict( [("_dic_m",0)]+[(k.__repr__(),v) for k,v in self.states.items()]),
                strategies=dict([('_dic_m',0)]+[(k.__repr__(),v) for k,v in self.strategies.items()]),
                ball=self.ball,score=self._score,step=self.step,
                max_steps=self.max_steps,goal=self._goal)
    def player_state(self, id_team, id_player):
        """ renvoie la configuration du joueur
        :param id_team: numero de la team du joueur
        :param id_player: numero du joueur
        :return:
        """
        return self.states[(id_team, id_player)]

    @property
    def players(self):
        """ renvoie la liste des cles des joueurs (idteam,idplayer)
        :return: liste des cles
        """
        return sorted(self.states.keys())

    def nb_players(self, team):
        """ nombre de joueurs de la team team
        :param team: 1 ou 2prit fauve
        :return:
        """
        return len([x for x in self.states.keys() if x[0] == team])

    def get_score_team(self, idx):
        """ score de la team idx : 1 ou 2
        :param idx: numero de la team
        :return:
        """
        return self._score[str(idx)]

    @property
    def score_team1(self):
        return self.get_score_team(1)

    @property
    def score_team2(self):
        return self.get_score_team(2)

    @property
    def goal(self):
        """
        :return: id de la team qui vient de marquer le but, 0 sinon
        """
        return self._goal

    def copy(self):
        return deepcopy(self)


    def apply_actions(self, actions=None,strategies=None):
        if strategies: self.strategies.update(strategies)
        sum_of_shoots = Vector2D()
        self._goal = 0
        if actions:
            for k, c in self.states.items():
                if k in actions:
                    sum_of_shoots += c.next(self.ball, actions[k])
        self.ball.next(sum_of_shoots)
        self.step += 1
        if self.ball.inside_goal():
            self._do_goal(2 if self.ball.position.x <= 0 else 1)
            return
        if self.ball.position.x < 0:
            self.ball.position.x = -self.ball.position.x
            self.ball.vitesse.x = -self.ball.vitesse.x
        if self.ball.position.y < 0:
            self.ball.position.y = -self.ball.position.y
            self.ball.vitesse.y = -self.ball.vitesse.y
        if self.ball.position.x > settings.GAME_WIDTH:
            self.ball.position.x = 2 * settings.GAME_WIDTH - self.ball.position.x
            self.ball.vitesse.x = -self.ball.vitesse.x
        if self.ball.position.y > settings.GAME_HEIGHT:
            self.ball.position.y = 2 * settings.GAME_HEIGHT - self.ball.position.y
            self.ball.vitesse.y = -self.ball.vitesse.y


    def _do_goal(self, idx):
        self._score[str(idx)]+=1
        self._goal = idx


    @classmethod
    def create_initial_state(cls, nb_players_1=0, nb_players_2=0):
        """ Creer un etat initial avec le nombre de joueurs indique
        :param nb_players_1: nombre de joueur de la team 1
        :param nb_players_2: nombre de joueur de la teamp 2
        :return:
        """
        state = cls()
        state.reset_state(nb_players_1, nb_players_2)
        return state

    def reset_state(self, nb_players_1=0, nb_players_2=0):
        if nb_players_1 == 0 and self.nb_players(1) > 0:
            nb_players_1 = self.nb_players(1)
        if nb_players_2 == 0 and self.nb_players(2) > 0:
            nb_players_2 = self.nb_players(2)
        quarters = [i * settings.GAME_HEIGHT / 4. for i in range(1, 4)]
        rows = [settings.GAME_WIDTH * 0.1, settings.GAME_WIDTH * 0.35, settings.GAME_WIDTH * (1 - 0.35),
                settings.GAME_WIDTH * (1 - 0.1)]
        if nb_players_1 == 1:
            self.states[(1, 0)] = PlayerState(position=Vector2D(rows[0], quarters[1]))
        if nb_players_2 == 1:
            self.states[(2, 0)] = PlayerState(position=Vector2D(rows[3], quarters[1]))
        if nb_players_1 == 2:
            self.states[(1, 0)] = PlayerState(position=Vector2D(rows[0], quarters[0]))
            self.states[(1, 1)] = PlayerState(position=Vector2D(rows[0], quarters[2]))
        if nb_players_2 == 2:
            self.states[(2, 0)] = PlayerState(position=Vector2D(rows[3], quarters[0]))
            self.states[(2, 1)] = PlayerState(position=Vector2D(rows[3], quarters[2]))
        if nb_players_1 == 3:
            self.states[(1, 0)] = PlayerState(position=Vector2D(rows[0], quarters[1]))
            self.states[(1, 1)] = PlayerState(position=Vector2D(rows[0], quarters[0]))
            self.states[(1, 2)] = PlayerState(position=Vector2D(rows[0], quarters[2]))
        if nb_players_2 == 3:
            self.states[(2, 0)] = PlayerState(position=Vector2D(rows[3], quarters[1]))
            self.states[(2, 1)] = PlayerState(position=Vector2D(rows[3], quarters[0]))
            self.states[(2, 1)] = PlayerState(position=Vector2D(rows[3], quarters[2]))
        if nb_players_1 == 4:
            self.states[(1, 0)] = PlayerState(position=Vector2D(rows[0], quarters[0]))
            self.states[(1, 1)] = PlayerState(position=Vector2D(rows[0], quarters[2]))
            self.states[(1, 2)] = PlayerState(position=Vector2D(rows[1], quarters[0]))
            self.states[(1, 3)] = PlayerState(position=Vector2D(rows[1], quarters[2]))
        if nb_players_2 == 4:
            self.states[(2, 0)] = PlayerState(position=Vector2D(rows[3], quarters[0]))
            self.states[(2, 1)] = PlayerState(position=Vector2D(rows[3], quarters[2]))
            self.states[(2, 2)] = PlayerState(position=Vector2D(rows[2], quarters[0]))
            self.states[(2, 3)] = PlayerState(position=Vector2D(rows[2], quarters[2]))
        self.ball = Ball.from_position(settings.GAME_WIDTH / 2, settings.GAME_HEIGHT / 2)
        self._goal = 0



###############################################################################
# SoccerTeam
###############################################################################

class Player(JSONable):
    def __init__(self,name=None,strategy=None):
        self.name = name or ""
        self.strategy = strategy
    def to_dict(self):
        return dict(name=self.name)
    def __str__(self):
        return "%s, %s" %(self.name,str(self.strategy))
    def __repr__(self):
        return self.__str__()

class SoccerTeam(JSONable):
    """ Equipe de foot. Comporte une  liste ordonnee de  Player.
    """

    def __init__(self, name=None, players=None, login=None):
        """
        :param name: nom de l'equipe
        :param players: liste de joueur Player(name,strategy)
        :return:
        """
        self.name, self.players, self.login = name or "", players or [], login or ""

    def __iter__(self):
        return iter(self.players)

    def __str__(self):
        return str(self.name)+": "+" ".join(str(p) for p in self.players)
    def __repr__(self):
        return self.__str__()

    def add(self,name,strategy):
        self.players.append(Player(name,strategy))
        return self
    @property
    def players_name(self):
        """
        :return: liste des noms des joueurs de l'equipe
        """
        return [x.name for x in self.players]

    def player_name(self, idx):
        """
        :param idx: numero du joueur
        :return: nom du joueur
        """
        return self.players[idx].name

    @property
    def strategies(self):
        """
        :return: liste des strategies des joueurs
        """
        return [x.strategy for x in self.players]

    def strategy(self, idx):
        """
        :param idx: numero du joueur
        :return: strategie du joueur
        """
        return self.players[idx].strategy

    def compute_strategies(self, state, id_team):
        """ calcule les actions de tous les joueurs
        :param state: etat courant
        :param id_team: numero de l'equipe
        :return: dictionnaire action des joueurs
        """
        return dict([((id_team, i), x.strategy.compute_strategy(state.copy(), id_team, i)) for i, x in
                     enumerate(self.players) if  hasattr( x.strategy,"compute_strategy")])

    @property
    def nb_players(self):
        """
        :return: nombre de joueurs
        """
        return len(self.players)
    def copy(self):
        return deepcopy(self)



###############################################################################
# Simulation
###############################################################################


class Simulation(JSONable):
    def __init__(self,team1=None,team2=None, max_steps = settings.MAX_GAME_STEPS,state=None,**kwargs):
        self.team1, self.team2 = team1 or SoccerTeam(),team2 or SoccerTeam()
        self.state = state or SoccerState.create_initial_state(self.team1.nb_players,self.team2.nb_players)
        self.max_steps = max_steps
        self.listeners = SoccerEvents()
        self._thread = None
        self._on_going = False
        self._thread = None
        self._kill = False
        self.initial_state = self.state.copy()
        self.states = []
        for s in self.team1.strategies + self.team2.strategies:
            self.listeners += s
        self.__dict__.update(kwargs)

    def reset(self):
        self.states = []
        self.state = self.initial_state.copy()
        self._thread = None
        self._kill = False
        self._on_going = False
    def to_dict(self):
        return dict(team1=self.team1,team2=self.team2,state=self.state,max_steps=self.max_steps,states=self.states)

    def start_thread(self):
        if not self._thread or not self._thread.isAlive():
            self._kill = False
            self._thread = threading.Thread(target=self.start)
            self._thread.start()
    def kill(self):
        self._kill = True

    def start(self):
        if self._on_going:
            return
        self.begin_match()
        while not self.stop():
            self.next_step()
        self.end_match()
        self._on_going = False
        return self.state.score_team1, self.state.score_team2
    def next_step(self):
        actions=dict()
        strategies=dict()
        for i,t in enumerate([self.team1,self.team2]):
            try:
                actions.update(t.compute_strategies(self.state, i+1))
                strategies.update(dict([((i,j),s.name) for j,s in enumerate(t.strategies)]))
            except Exception as e:
                time.sleep(0.0001)
                print(e, traceback.print_exc())
                self.state.step=self.max_steps
                self.state._score[2-i]=100
                print("Error for team %d -- loose match" % ((i+1),))
        self.state.apply_actions(actions,strategies)
        self.states.append(self.state.copy())
        self.update_round()
        if self.state.goal > 0:
            self.end_round()
            self.begin_round()
    def get_team(self,idx):
        if idx==1:
            return self.team1
        if idx == 2:
            return self.team2
    def stop(self):
        return self._kill or self.state.step >= self.max_steps
    def update_round(self):
        self.listeners.update_round(self.team1,self.team2,self.state)
    def begin_round(self):
        score=dict(self.state._score)
        self.state = self.initial_state.copy()
        self.state._score = score
        self.state.step = len(self.states)
        self.states.append(self.state)
        self.listeners.begin_round(self.team1,self.team2,self.state)
    def end_round(self):
        self.listeners.end_round(self.team1, self.team2, self.state)
    def begin_match(self):
        self.reset()
        self._on_going = True
        self.listeners.begin_match(self.team1,self.team2,self.state)
        self.begin_round()
    def end_match(self):
        self.listeners.end_match(self.team1,self.team2,self.state)
    def send_strategy(self,key):
        self.listeners.send_strategy(key)
