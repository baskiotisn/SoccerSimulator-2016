# -*- coding: utf-8 -*-

from . import settings
from functools import total_ordering
from collections import namedtuple
from .mdpsoccer import Simulation
from .utils import to_jsonz,dict_to_json,from_jsonz
from .events import SoccerEvents
from . import settings
import logging
###############################################################################
# Tournament
###############################################################################
logger = logging.getLogger("soccersimulator.matches")

@total_ordering
class Score(object):
    def __init__(self,win=0,draw=0,loose=0,gf=0,ga=0,**kwargs):
        self.win = win
        self.loose = loose
        self.draw = draw
        self.gf = gf
        self.ga = ga
        self.__dict__.update(kwargs)
    def to_dict(self):
        return {"win":self.win,"loose":self.loose,"draw":self.draw,"gf":self.gf,"ga":self.ga}
    @property
    def diff(self):
        return self.gf - self.ga

    @property
    def points(self):
        return 3 * self.win + self.draw

    @property
    def score(self):
        return self.points, self.win, self.draw, self.loose, self.gf, self.ga

    def set(self, score=None):
        if score is None:
            self.win, self.loose, self.draw, self.gf, self.ga = 0, 0, 0, 0, 0
            return
        self.win, self.loose, self.draw, self.gf, self.ga = score.win, score.loose, score.draw, score.gf, score.ga

    def add(self, gf, ga):
        self.gf += gf
        self.ga += ga
        if gf > ga:
            self.win += 1
        if gf == ga:
            self.draw += 1
        if gf < ga:
            self.loose += 1

    def __str__(self):
        return "\033[96m\033[94m%d\033[0m (\033[92m%d\033[0m,\033[93m%d\033[0m,\033[91m%d\033[0m) - (%d,%d)" % \
               (self.points, self.win, self.draw, self.loose, self.gf, self.ga)

    def str_nocolor(self):
        return "%d (%d,%d,%d) - [%d,%d] " % (self.points, self.win, self.draw, self.loose, self.gf, self.ga)

    def __lt__(self, other):
        return (self.points, self.diff, self.gf, -self.ga) < (other.points, other.diff, other.gf, -other.ga)

    def __eq__(self, other):
        return (self.points, self.diff, self.gf, -self.ga) == (other.points, other.diff, other.gf, -other.ga)

    def __repr__(self):
        return "Score(%d,%d,%d,%d,%d)" % (self.win, self.draw, self.loose, self.gf, self.ga)

class SoccerTournament(object):

    def __init__(self, nb_players=None, max_steps=settings.MAX_GAME_STEPS, retour=True,**kwargs):
        self.nb_players, self.max_steps, self.retour = nb_players, max_steps, retour
        self.matches = kwargs.pop("matches",dict())
        self.teams = kwargs.pop("teams",dict())
        self.scores = kwargs.pop("scores",dict())
        self.cur_match = None
        self.cur_i, self.cur_j = -1, -1
        self._over, self._on_going = False, False
        self.listeners = SoccerEvents()
        self._kill = False
        self._replay = False
        self._join = True

    def to_dict(self):
        return {"nb_players":self.nb_players, "max_steps":self.max_steps, "retour":self.retour, \
                    "matches":dict_to_json(self.matches),"scores":dict_to_json(self.scores), "teams":dict_to_json(self.teams)}

    def add_team(self, team, score=None):
        if score is None:
            score = Score()
        if self.nb_players and self.nb_players != team.nb_players:
            return -1
        self.teams[self.nb_teams]=team
        self.scores[self.nb_teams-1]=score
        if self.nb_teams > 1:
             for i, t in sorted(self.teams.items()[:-1]):
                 self.matches[(i, self.nb_teams - 1)] = None
                 if self.retour: self.matches[(self.nb_teams - 1, i)] = None
        return self.nb_teams-1

    def get_team(self, i):
        if type(i) == str:
            i = self.find_team(i)
        return self.teams[i]

    def reset(self):
        self.cur_match = None
        self._on_going = False
        self.cur_i,self.cur_j = -1,-1
        for score in self.scores.values():
            score.set()
        for m in self.matches:
            self.matches[m]=None
        self._kill = False
        self._replay = False

    @property
    def nb_teams(self):
        return len(self.teams)

    @property
    def nb_matches(self):
        return len(self.matches)
    @property
    def not_played(self):
        return sorted([ k for k,m in self.matches.items() if m is None])
    @property
    def played(self):
        return sorted([k for k,m in self.matches.items() if m is not None])
    def _get_next(self):
        return self.not_played[0]
    def play(self):
        if self._on_going:
            return
        self._on_going = True
        while not self.stop():
            self.play_next()

    def kill(self):
        self._kill = True
        if hasattr(self.cur_match, "kill"):
            self.cur_match.kill()

    def stop(self):
        return len(self.not_played) == 0 or self._kill

    def play_next(self):
        if self.stop():
            return
        self.cur_i,self.cur_j = self._get_next()
        self.cur_match = Simulation(self.get_team(self.cur_i),self.get_team(self.cur_j),max_steps=self.max_steps)
        self.cur_match.listeners += self
        self.cur_match.start()

    def find_team(self, name):
        for i, team in self.teams.items():
            if team.name == name:
                return i
        return -1

    def get_score(self, i):
        return self.scores[i]

    def get_match(self, i, j):
        if type(i) == str and type(j) == str:
            i = self.find_team(i)
            j = self.find_team(j)
        if self.matches[(i,j)] is not None:
            return from_jsonz(self.matches[(i, j)])
        return None
    def get_matches(self, i):
        if type(i) == str:
            i = self.find_team(i)
        return [from_jsonz(m) for k, m in self.matches.items() if (k[0] == i or k[1] == i) and (m is not None)]

    def format_scores(self,with_id=True):
        sc = sorted([(score, i) for i,score  in self.scores.items()], reverse=True)
        res = ["[%d]   \033[92m%s\033[0m (\033[93m%s\033[m) : %s"\
                    % (i,self.teams[i].name, self.teams[i].login, str(score)) for score, i in sc]
        return "\033[93m***\033[0m \033[95m Resultats pour le tournoi \033[92m%d joueurs\033[0m : \033[93m***\33[0m \n\t%s\n\n" % \
               (self.nb_teams, "\n\t".join(res))
    def format_scores_latex(self,with_id=True):
        sc = sorted([(score, i) for i,score  in self.scores.items()], reverse=True)
        res = ["\\rowcolor{%s} %s (%s) & %d & (%d,%d,%d) & (%d,%d)\\\\" \
            % ("lg" if j%2==0 else "hg", self.teams[i].name, self.teams[i].login,score.points,score.win,\
               score.draw,score.loose,score.gf,score.ga) for j,(score, i) in enumerate(sc)]
        return  "\n".join(res)

    def print_scores(self,with_id=False):
        print(self.format_scores(with_id))
    def __str__(self):
        return "Tournoi %d joueurs,  %d equipes, %d matches" %(self.nb_players,self.nb_teams,self.nb_matches)
    def __repr__(self):
        return self.__str__()
    def update_round(self, *args, **kwargs):
        self.listeners.update_round(*args, **kwargs)

    def begin_round(self, *args, **kwargs):
        self.listeners.begin_round(*args, **kwargs)

    def end_round(self, *args, **kwargs):
        self.listeners.end_round(*args, **kwargs)

    def begin_match(self, *args, **kwargs):
        logger.info("\033[33mDebut match : \033[0m%d/%d : \033[94m%s (%s) \033[0mvs \033[94m%s (%s)\033[0m" % (len(self.played)+1, self.nb_matches,
                                                    self.cur_match.get_team(1).name,self.cur_match.get_team(1).login,
                                                    self.cur_match.get_team(2).name,self.cur_match.get_team(2).login))
        self.listeners.begin_match(*args, **kwargs)

    def end_match(self, *args, **kwargs):
        if not self._replay:
            self.scores[self.cur_i].add(self.cur_match.states[-1].get_score_team(1), self.cur_match.states[-1].get_score_team(2))
            self.scores[self.cur_j].add(self.cur_match.states[-1].get_score_team(2), self.cur_match.states[-1].get_score_team(1))
            self.matches[(self.cur_i,self.cur_j)]=to_jsonz(self.cur_match)
        cm1 = cm2 = "\033[37m"
        if self.cur_match.get_score_team(1)>self.cur_match.get_score_team(2):
            cm1 = "\033[92m"
            cm2 = "\033[91m"
        if self.cur_match.get_score_team(1)<self.cur_match.get_score_team(2):
            cm1 = "\033[91m"
            cm2 = "\033[92m"
        logger.info("\033[93mResultat : %s%s (%s) \033[0mvs %s%s (%s) : %s%d - %s%d\033[0m" % \
            (cm1,self.cur_match.get_team(1).name, self.cur_match.get_team(1).login,\
              cm2,self.cur_match.get_team(2).name, self.cur_match.get_team(2).login, \
            cm1,self.cur_match.get_score_team(1),cm2, self.cur_match.get_score_team(2)))
        self.listeners.end_match(*args, **kwargs)
        self.cur_match.listeners -= self
        self.cur_i,self.cur_j = -1,-1
