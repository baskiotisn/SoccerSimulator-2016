from .utils import  dump_jsonz, load_jsonz, fmt,clean_fn, to_json, to_jsonz, from_json, from_jsonz,dict_to_json
from .utils import  Vector2D, MobileMixin
from .strategies import Strategy,  KeyboardStrategy
from .mdpsoccer import SoccerAction, Ball, PlayerState, SoccerState
from .golf import GolfState,Golf,Parcours1,Parcours2,Parcours3,Parcours4
from .mdpsoccer import  Player, SoccerTeam, Simulation
from .matches import Score, SoccerTournament
from .gui import SimuGUI, show_simu, show_state, pyg_start, pyg_stop, pyglet
from . import  settings
from . import gitutils
import logging
__version__ = '1.2017.02.05'
__project__ = 'soccersimulator'

logging.basicConfig(format='%(name)s:%(levelname)s - %(message)s', level=logging.DEBUG)
