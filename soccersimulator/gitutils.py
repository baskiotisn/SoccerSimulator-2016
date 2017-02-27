import os
import sys
import imp
import shutil
import argparse
import pickle
from collections import namedtuple
import traceback
import logging
from soccersimulator import SoccerTeam, Strategy, Simulation

logger = logging.getLogger("soccersimulator.gitutils")

MAX_TEST_STEPS = 50
Groupe = namedtuple("Groupe",["login","projet","noms"])

def dl_from_github(groupe, path):
    if type(groupe)==list:
        for g in groupe: dl_from_github(g,path)
        return
    logger.info("Debut import github %s %s" % (groupe.login, groupe.projet))
    if not os.path.exists(path):
        os.mkdir(path)
    tmp_path = os.path.join(path, groupe.login)
    shutil.rmtree(tmp_path, ignore_errors=True)
    os.mkdir(tmp_path)
    os.system("git clone https://github.com/%s/%s %s " % (groupe.login, groupe.projet, tmp_path))


def check_date(groupe, path):
    if type(groupe)==list:
        for g in groupe: check_date(g,path)
        return
    print(groupe.login)
    os.system("git --git-dir=%s/.git log  --format=\"%%Cgreen%%cd %%Creset \"| cut -d \" \" -f 1-3,7| uniq" %
              (os.path.join(path, groupe.login),))


def check_team(team):
    teamDefault = SoccerTeam()
    for nb in range(team.nb_players):
        teamDefault.add(str(nb),Strategy())
    if Simulation(team,teamDefault,max_steps=MAX_TEST_STEPS).start().error or \
            Simulation(teamDefault,team,max_steps=MAX_TEST_STEPS).start().error:
        return False
    return True

def load_teams(path,login,nbps):
    mymod = None
    if not os.path.exists(os.path.join(path,login,"__init__.py")):
        logger.info("\033[93m Erreur pour \033[94m%s : \033[91m%s \033[0m" % (login, "__init__.py non trouve"))
        return None
    try:
        sys.path.insert(0, path)
        mymod = __import__(login)
    except Exception as e:
        logger.debug(traceback.format_exc())
        logger.info("\033[93m Erreur pour \033[94m%s : \033[91m%s \033[0m" % (login, e))
    finally:
        del sys.path[0]
    if mymod is None:
        return None
    teams = dict()
    if not hasattr(mymod,"get_team"):
        logger.info("\033[93m Pas de get_team pour \033[94m%s\033[0m" % (login,))
        return teams
    for nbp in nbps:
        try:
            tmpteam = mymod.get_team(nbp)
            if tmpteam is None or not hasattr(tmpteam,"nb_players"):
                logger.info("\033[93m Pas d'equipe a %d joueurs pour \033[94m%s\033[0m" % (nbp,login))
                continue
            if tmpteam.nb_players != nbp:
                logger.info("\033[93m Erreur pour \033[94m%s : \033[0m mauvais nombre de joueurs (%d au lieu de %d)"\
                    % (login, tmpteam.nb_players, nbp))
                continue
            if not check_team(tmpteam):
                logger.info("\033[93m Error for \033[91m(%s,%d)\033[0m" % (login,nbp))
                continue
            tmpteam.login = login
            teams[nbp] = (tmpteam,mymod.get_team)
        except Exception as e:
            logger.debug(traceback.format_exc())
            logger.info("\033[93m Erreur pour \033[94m%s: \033[91m%s \033[0m" % (login,e))
    logger.info("Equipes de \033[92m%s\033[0m charge, \033[92m%s equipes\033[0m" % (login, len(teams)))
    return teams



def import_directory(path,nbps,logins = None):
    teams = dict()
    for i in nbps:
        teams[i] = []
    path = os.path.realpath(path)
    logins = [login for login in os.listdir(path)\
              if os.path.isdir(os.path.join(path,login)) and (logins is None or login in logins)]
    for l in sorted(logins,key=lambda x : x.lower()):
        tmp=load_teams(path,l,nbps)
        if tmp is not None:
            for nbp in tmp.keys():
                teams[nbp].append(tmp[nbp])
    return teams
