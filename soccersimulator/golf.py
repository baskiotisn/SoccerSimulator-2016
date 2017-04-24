from .settings import *
from .mdpsoccer import *
from .utils import *

class Carre(object):
    def __init__(self,position,l,**kwarg):
        self.position,self.l = position.copy(),l
    def dedans(self,point):
        return (point.x-self.position.x)<self.l and (point.y-self.position.y)<self.l and (point.x-self.position.x)>=0 and (point.y-self.position.y)>=0

class GolfState(SoccerState):
    def __init__(self,**kwargs):
        self.zones_1 = []
        self.zones_2 = []
        self.zone_1_bool = []
        self.zone_2_bool = []
        self.vitesse = 0.01
        super(GolfState,self).__init__(**kwargs)
    def add_zone(self,idteam,zone):
        if idteam==1:
            self.zones_1.append(zone)
            self.zones_1_bool.append(False)
        if  idteam==2:
            self.zones_2.append(zone)
            self.zones_2_bool.append(False)
    def apply_actions(self,actions=None,strategies=None):
        super(GolfState,self).apply_actions(actions,strategies)
        if self.ball.vitesse.norm <self.vitesse:
            for i,z in enumerate(self.zones_1):
                if z.dedans(self.ball.position):
                    self.zones_1_bool[i]=True
                    self.score[1]=sum(self.zones_1_bool)
            for i,z in enumerate(self.zones_2):
                if z.dedans(self.ball.position):
                    self.zones_2_bool[i]=True
                    self.score[2] = sum(self.zones_2_bool)

    def _do_goal(self,idx):
        if idx==1:
            if sum(self.zones_1_bool)==len(self.zones_1):
                self.score[idx]=self.max_steps-self.step
                self.goal = idx
        if idx==2:
            if sum(self.zones_2_bool)==len(self.zones_2):
                self.score[idx]=self.max_steps-self.step
                self.goal = idx
    def reset_state(self,**kwargs):
        super(GolfState,self).reset_state(**kwargs)
        self.zones_1_bool = [False for x in self.zones_1]
        self.zones_2_bool = [False for x in self.zones_2]

    def get_zones(self,idteam):
        if idteam==1:
            return [z for  (z,b) in zip(self.zones_1,self.zones_1_bool) if not b]
        if idteam==2:
            return [z for (z,b) in zip(self.zones_2,self.zones_2_bool) if not b]


class Golf(Simulation):
    def __init__(self,team1=None,team2=None,max_steps=settings.MAX_GAME_STEPS,initial_state=None,vitesse=0.001,**kwargs):
        super(Golf,self).__init__(team1,team2,max_steps,initial_state,**kwargs)
        self.initial_state = GolfState.create_initial_state(self.team1.nb_players,self.team2.nb_players,self.max_steps)
        self.initial_state.vitesse=vitesse
    def stop(self):
        return super(Golf,self).stop() or self.state.goal > 0

class Parcours1(Golf):
    def __init__(self,**kwargs):
        super(Parcours1,self).__init__(**kwargs)
        self.initial_state.add_zone(1,Carre(Vector2D(GAME_WIDTH*7/10.,GAME_HEIGHT/2.),10))
        if self.team2.nb_players>0:
            self.initial_state.add_zone(2,Carre(Vector2D(GAME_WIDTH-GAME_WIDTH*7/10.,GAME_HEIGHT/2.),10))
        self.state = self.initial_state.copy()


class Parcours2(Golf):
    def __init__(self,**kwargs):
        super(Parcours2,self).__init__(**kwargs)
        self.initial_state.add_zone(1,Carre(Vector2D(GAME_WIDTH*7/10.,3*GAME_HEIGHT/4.),10))
        self.initial_state.add_zone(1,Carre(Vector2D(GAME_WIDTH*7/10.,1*GAME_HEIGHT/4.),10))
        if self.team2.nb_players>0:
            self.initial_state.add_zone(2,Carre(Vector2D(GAME_WIDTH-GAME_WIDTH*7/10.,3*GAME_HEIGHT/4.),10))
            self.initial_state.add_zone(2,Carre(Vector2D(GAME_WIDTH-GAME_WIDTH*7/10.,1*GAME_HEIGHT/4.),10))
        self.state = self.initial_state.copy()

class Parcours3(Golf):
    def __init__(self,**kwargs):
        super(Parcours3,self).__init__(**kwargs)
        self.initial_state.add_zone(1,Carre(Vector2D(GAME_WIDTH*7/10.,3*GAME_HEIGHT/4.),10))
        self.initial_state.add_zone(1,Carre(Vector2D(GAME_WIDTH*2/10.,1*GAME_HEIGHT/4.),10))
        if self.team2.nb_players>0:
            self.initial_state.add_zone(2,Carre(Vector2D(GAME_WIDTH-GAME_WIDTH*7/10.,3*GAME_HEIGHT/4.),10))
            self.initial_state.add_zone(2,Carre(Vector2D(GAME_WIDTH-GAME_WIDTH*2/10.,1*GAME_HEIGHT/4.),10))
        self.state = self.initial_state.copy()

class Parcours4(Golf):
    def __init__(self,**kwargs):
        super(Parcours4,self).__init__(**kwargs)
        for i in range(5):
            for j in range(5):
                self.initial_state.add_zone(1,Carre(Vector2D(GAME_WIDTH/2.+GAME_WIDTH*(2*i+1)/24.,GAME_HEIGHT*(2*j+2)/12.),4))
        if self.team2.nb_players>0:
            for i in range(5):
                for j in range(5):
                    self.initial_state.add_zone(2,Carre(Vector2D(GAME_WIDTH-GAME_WIDTH/2.-GAME_WIDTH*(2*i+1)/24.,GAME_HEIGHT*(2*j+2)/12.),4))
        self.state = self.initial_state.copy()
