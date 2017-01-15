# -*- coding: utf-8 -*-

from . import settings
from functools import total_ordering
from collections import namedtuple
from .mdpsoccer import Simulation
from . import settings
class SoccerMatch(Simulation):
    """ Match de foot.
    """
    def __init__(self, team1=None, team2=None, max_steps=settings.MAX_GAME_STEPS):
        """
        :param team1: premiere equipe
        :param team2: deuxieme equipe
        :return:
        """
        Simulation.__init__(self,team1=team1,team2=team2,max_steps=max_steps)
        self._thread = None
        self._on_going = False
        self._kill = False

    def reset(self):
        self.kill()
        Simulation.reset(self)
        self._thread = None
        self._on_going = False

    def kill(self):
        """ arrete le match
        :return:
        """
        self._kill = True
        time.sleep(0.1)
        self._kill = False

    def play(self, join=True):
        """ joue le match
        :param join: attend que le match soit fini avant de sortir
        :return:
        """
        if not self._thread or not self._thread.isAlive():
            self._thread = threading.Thread(target=lambda :Simulation.play(self))
            self._thread.start()
            if join:
                self._thread.join()
                return self.state.score_team1, self.state.score_team2
        return (None, None)

    def send_strategy(self, cmd):
        self.listeners.send_strategy(cmd)


###############################################################################
# Tournament
###############################################################################


@total_ordering
class Score(object):
    def __init__(self):
        self.win = 0
        self.loose = 0
        self.draw = 0
        self.gf = 0
        self.ga = 0

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
        return "\033[92m\033[34m%d\033[0m (\033[32m%d\033[0m,\033[31m%d\033[0m,\033[93m%d\033[0m) - (%d,%d)" % \
               (self.points, self.win, self.draw, self.loose, self.gf, self.ga)

    def str_nocolor(self):
        return "%d (%d,%d,%d) - [%d,%d] " % (self.points, self.win, self.draw, self.loose, self.gf, self.ga)

    def __lt__(self, other):
        return (self.points, self.diff, self.gf, -self.ga) < (other.score, other.diff, other.gf, -other.ga)

    def __eq__(self, other):
        return (self.points, self.diff, self.gf, -self.ga) == (other.score, other.diff, other.gf, -other.ga)

    def to_str(self):
        return "(%d,%d,%d,%d,%d)" % (self.win, self.draw, self.loose, self.gf, self.ga)

    @classmethod
    def from_str(cls, strg):
        res = cls()
        res.win, res.draw, res.loose, res.gf, res.ga = [int(x) for x in strg.lstrip("(").rstrip(")").split(",")]
        return res


class SoccerTournament(object):
    TeamTuple = namedtuple("TeamTuple", ["team", "score"])
    SEP_MATCH = "#####MATCH#####\n"

    def __init__(self, nb_players=None, max_steps=settings.MAX_GAME_STEPS, retour=True,verbose=True):
        self.nb_players, self.max_steps, self._retour = nb_players, max_steps, retour
        self._matches = dict()
        self._teams = []
        self._listeners = SoccerEvents()
        self.cur_match, self._list_matches = None, None
        self._over, self._on_going = False, False
        self.cur_i, self.cur_j = -1, -1
        self.verbose = verbose
        self._kill = False
        self._replay = False
        self._join = True

    def add_team(self, team, score=None):
        if score is None:
            score = Score()
        if self.nb_players and self.nb_players != team.nb_players:
            return False
        self._teams.append(self.TeamTuple(team, score))
        if self.nb_teams > 1:
            for i, t in enumerate(self.teams[:-1]):
                self._matches[(i, self.nb_teams - 1)] = SoccerMatch(t, team, self.max_steps)
                if self._retour: self._matches[(self.nb_teams - 1, i)] = SoccerMatch(team, t, self.max_steps)
        return True

    def get_team(self, i):
        if type(i) == str:
            i = self.find_team(i)
        return self._teams[i].team

    def reset(self):
        self.cur_match = None
        self._list_matches = None
        self._on_going = False
        for t in self._teams:
            t.score.set()
        for m in self._matches.values():
            m.reset()
        self._kill = False
        self._replay = False

    @property
    def nb_teams(self):
        return len(self.teams)

    @property
    def teams(self):
        return [t.team for t in self._teams]

    @property
    def nb_matches(self):
        return len(self._matches)

    def play(self, join=True):
        if self._on_going:
            return
        for m in self._matches.values():
            m.max_steps = self.max_steps
        self._on_going = True
        self._join = join
        self._list_matches = sorted(self._matches.items())
        self.play_next()

    def kill(self):
        self._kill = True
        if hasattr(self.cur_match, "kill"):
            self.cur_match.kill()

    def play_next(self):
        if len(self._list_matches) == 0 or self._kill:
            self._on_going = False
            self._kill = False
            if self.verbose:
                print("Fin tournoi")
            return
        (self.cur_i, self.cur_j), self.cur_match = self._list_matches.pop(0)
        self.cur_match._listeners += self
        self.cur_match.play(self._join)

    def find_team(self, name):
        for i, t in enumerate(self._teams):
            if t.team.name == name:
                return i
        return -1

    def get_score(self, i):
        return self._teams[i].score

    def get_match(self, i, j):
        if type(i) == str and type(j) == str:
            i = self.find_team(i)
            j = self.find_team(j)
        return self._matches[(i, j)]

    def get_matches(self, i):
        if type(i) == str:
            i = self.find_team(i)
        return [m for k, m in self._matches.items() if k[0] == i or k[1] == i]

    def format_scores(self):
        sc = sorted([(t.score, t.team) for t in self._teams], reverse=True)
        res = ["\033[92m%s\033[0m (\033[93m%s\033[m) : %s" % (team.name, team.login, str(score)) for score, team in sc]
        return "\033[93m***\033[0m \033[95m Resultats pour le tournoi \033[92m%d joueurs\033[0m : \033[93m***\33[0m \n\t%s\n\n" % \
               (self.nb_teams, "\n\t".join(res))

    def __str__(self):
        return "Tournoi %d joueurs,  %d equipes, %d matches" %(self.nb_players,self.nb_teams,self.nb_matches)

    def to_str(self):
        res = "%d|%d|%d\n" % (
            self.nb_players if self.nb_players is not None else 0, len(self._teams), int(self._retour))
        res += "\n".join(
                "%d,%s\n%s" % (i, team.score.to_str(), team.team.to_str()) for i, team in enumerate(self._teams))
        res += "\n%s" % (self.SEP_MATCH,)
        res += self.SEP_MATCH.join("%d,%d\n%s\n" % (k[0], k[1], match.to_str()) for k, match in sorted(self._matches.items()))
        return res


    @classmethod
    def load(cls, filename):
        res = None
        if zipfile.is_zipfile(filename):
            zf = zipfile.ZipFile(filename)
            fn = zf.infolist()[0].filename
            res = cls.from_str(zf.read(fn))
            return res
        with open(filename, "r") as f:
            res = cls.from_str(f.read())
        return res


    @classmethod
    def from_str(cls, strg):
        res = cls()
        l_strg = strg.split(cls.SEP_MATCH)
        cur_l = l_strg[0].split("\n")
        res.nb_players, nb_teams, res._retour = [int(x) for x in cur_l.pop(0).split("|")]
        while len(cur_l) > 0:
            info = cur_l.pop(0)
            if len(info) == 0:
                continue
            fvir = info.index(",")
            idx, sc_str = info[:fvir], info[fvir + 1:]
            assert (len(res._teams) == int(idx))
            score = Score.from_str(sc_str)
            team = SoccerTeam.from_str(cur_l.pop(0))
            res.add_team(team, score)
        for l in l_strg[1:]:
            if len(l) == 0:
                continue
            t1 = int(l[:l.index(",")])
            t2 = int(l[l.index(",") + 1:l.index("\n")])
            match = SoccerMatch.from_str(l[l.index("\n") + 1:])
            res._matches[(t1, t2)] = match
        res._replay = True
        return res

    def update_round(self, *args, **kwargs):
        self._listeners.update_round(*args, **kwargs)

    def begin_match(self, *args, **kwargs):
        if self.verbose:
            print("Debut match %d/%d : %s (%s) vs %s (%s)" % (self.nb_matches - len(self._list_matches), self.nb_matches,
                                                    self.cur_match.get_team(1).name,self.cur_match.get_team(1).login,
                                                    self.cur_match.get_team(2).name,self.cur_match.get_team(2).login))
        self._listeners.begin_match(*args, **kwargs)

    def begin_round(self, *args, **kwargs):
        self._listeners.begin_round(*args, **kwargs)

    def end_round(self, *args, **kwargs):
        self._listeners.end_round(*args, **kwargs)

    def end_match(self, *args, **kwargs):
        if not self._replay:
            self._teams[self.cur_i].score.add(self.cur_match.get_score(1), self.cur_match.get_score(2))
            self._teams[self.cur_j].score.add(self.cur_match.get_score(2), self.cur_match.get_score(1))
        if self.verbose:
            print("Fin match  %s vs %s : %d - %d" % (self.cur_match.get_team(1).name, self.cur_match.get_team(2).name, \
                                                     self.cur_match.get_score(1), self.cur_match.get_score(2)))
        self._listeners.end_match(*args, **kwargs)
        self.cur_match._listeners -= self
        self.play_next()
