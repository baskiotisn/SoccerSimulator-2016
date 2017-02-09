import os
import sys
import imp
import shutil
import argparse
import pickle
from collections import namedtuple
import traceback
Groupe = namedtuple("Groupe",["login","projet","noms"])

def dl_from_github(groupe, path):
    if type(groupe)==list:
        for g in groupe: dl_from_github(g,path)
        return
    print("Debut import github %s %s" % (groupe.login, groupe.projet))
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


def load_teams(path,login,nbps):
    mymod = None
    if not os.path.exists(os.path.join(path,login,"__init__.py")):
        print("\033[93m Erreur pour \033[94m%s : \033[91m%s \033[0m" % (login, "__init__.py non trouve"))
        return None
    try:
        sys.path.insert(0, path)
        mymod = __import__(login)
    except Exception as e:
        print("\033[93m Erreur pour \033[94m%s : \033[91m%s \033[0m" % (login, str(e)))
    finally:
        del sys.path[0]
    if mymod is None:
        return None
    teams = dict()#{1:[],2:[],4:[]}
    try:
        if hasattr(mymod,"get_team"):
            for nbp in nbps:
                teams[nbp] = mymod.get_team(nbp)
    except Exception as e:
        print(traceback.print_exc())
    #if hasattr(mymod,"team1"):
    #    teams[1].append(mymod.team1)
    #if hasattr(mymod,"team2"):
    #    teams[2].append(mymod.team2)
    #if hasattr(mymod,"team4"):
    #    teams[4].append(mymod.team4)
    for nbp,t in teams.items():
        if t is None or not hasattr(t,"nb_players"):
            print("\033[93m Pas d'equipe a %d joueurs pour \033[94m%s\033[0m" % (nbp,login))
            del teams[nbp]
            continue
        if t.nb_players != nbp:
            print("\033[93m Erreur pour \033[94m%s : \033[0m mauvais nombre de joueurs (%d au lieu de %d)"\
                        % (login, t.nb_players, nbp))
            del teams[nbp]
            continue
        t.login = login
    print("Equipe de \033[92m%s\033[0m charge, \033[92m%s equipes\033[0m" % (login, len(teams)))
    return teams



def import_directory(path,nbps,logins = None):
    teams = dict()
    for i in nbps:
        teams[i] = []
    path = os.path.realpath(path)
    logins = [login for login in os.listdir(path)
              if os.path.isdir(os.path.join(path, login)) and (logins is None or login in logins)]
    for l in sorted(logins):
        tmp=load_teams(path,l,nbps)
        if tmp is not None:
            for nbp in tmp.keys():
                teams[nbp].append(tmp[nbp])
    return teams
