# -*- coding: utf-8 -*-
import pyglet
# pyglet.options["debug_gl"]=True
# pyglet.options["debug_trace"]=True
# pyglet.options["debug_gl_trace"]=True

from pyglet import gl
import time
import traceback
from . import settings
from .guiutils import *
import logging
from .guisettings import *

FPS = 50.
FPS_MOD = 5.
logger = logging.getLogger("soccersimulator.gui")

class SimuGUI(pyglet.window.Window):
    AUTO = 0
    MANUAL = 1
    NOWAIT = -1
    key_handlers = {
        pyglet.window.key.ESCAPE: lambda w: w.exit(),
        pyglet.window.key.P: lambda w: w.play(),
        pyglet.window.key.PLUS: lambda w: w._increase_fps(),
        pyglet.window.key.MINUS: lambda w: w._decrease_fps(),
        pyglet.window.key.NUM_0: lambda w: w._switch_hud_names(),
        pyglet.window.key._0: lambda w: w._switch_hud_names(),
        pyglet.window.key.NUM_ADD: lambda w: w._increase_fps(),
        pyglet.window.key.NUM_SUBTRACT: lambda w: w._decrease_fps(),
        pyglet.window.key.BACKSPACE: lambda w: w._switch_manual_step_flag(),
        pyglet.window.key.SPACE: lambda w: w._switch_manual_step(),
    }

    def __init__(self,simu=None,width=1200,height=800):
        pyglet.window.Window.__init__(self, width=width, height=height, resizable=True)
        self.set_size(width, height)
        self.focus()
        self.clear()
        self._fps = FPS
        self._sprites = dict()
        self._background = BackgroundSprite()
        self._state = None
        self._mode_next = self.AUTO
        self._waiting_key = False
        self._hud_names = True
        self.hud = Hud()
        pyglet.clock.schedule_interval(self.update, 1. / 25)
        self.set(simu)
        if simu:
            self.play()

    @property
    def state(self):
        return self.get_state()

    def update(self, dt=None):
        self.draw()

    def _wait_next(self):
        if self._mode_next == self.NOWAIT:
            return
        if self._mode_next == self.AUTO:
            time.sleep(1. / self._fps)
        if self._mode_next == self.MANUAL:
            self._waiting_key = True
            while self._waiting_key:
                time.sleep(0.0001)

    def _switch_manual_step_flag(self):
        self._waiting_key = False

    def _switch_manual_step(self):
        if self._mode_next == self.MANUAL:
            self._mode_next = self.AUTO
            self._waiting_key = False
        else:
             self._mode_next = self.MANUAL


    def _switch_hud_names(self):
        self._hud_names = not self._hud_names

    def create_drawable_objects(self):
        if not self.state:
            return
        self._sprites = dict()
        self._sprites["ball"] = BallSprite()
        for k, v in self.state.players:
            if not self.get_team(k):
                name_p = '%d %d|' % (k, v)
            else:
                name_p = self.get_team(k).player_name(v)
            self._sprites[(k, v)] = PlayerSprite(name_p, color=TEAM1_COLOR if k == 1 else TEAM2_COLOR)
        if hasattr(self.state,"zones_1"):
            for i,z in enumerate(self.state.zones_1):
                self._sprites[(i,"z1")]=RectSprite(z.l, GREEN_COLOR if self.state.zones_1_bool[i] else RED_COLOR)
        if hasattr(self.state,"zones_2"):
            for i,z in enumerate(self.state.zones_2):
                self._sprites[(i,"z2")]=RectSprite(z.l, GREEN_COLOR if self.state.zones_2_bool[i] else RED2_COLOR)
    def _update_sprites(self):
        team1 = team2 = ongoing = ""
        if not self.state:
            return
        if len(self._sprites) ==0:
            self.create_drawable_objects()
        if self.get_team(1):
            team1 = "%s %s - %s" % (self.get_team(1).name,self.get_team(1).login, self.get_score(1))
        if self.get_team(2):
            team2 = "%s %s - %s" % (self.get_team(2).name, self.get_team(2).login, self.get_score(2))
        ongoing = "Round : %d/%d" % (self.state.step, self.get_max_steps())
        self.hud.set_val(team1=team1, team2=team2, ongoing=ongoing)
        for k in self.state.players:
            self._sprites[k].position = self.state.player_state(k[0], k[1]).position
            self._sprites[k].vitesse= self.state.player_state(k[0], k[1]).vitesse
        if hasattr(self.state,"zones_1"):
            for i,z in enumerate(self.state.zones_1):
                self._sprites[(i,"z1")].position=z.position
                self._sprites[(i,"z1")].set_color( GREEN_COLOR if self.state.zones_1_bool[i] else RED_COLOR)
        if hasattr(self.state,"zones_2"):
            for i,z in enumerate(self.state.zones_2):
                self._sprites[(i,"z2")].position=z.position
                self._sprites[(i,"z2")].set_color( GREEN_COLOR if self.state.zones_2_bool[i] else RED2_COLOR)
        self._sprites["ball"].position = self.state.ball.position
        self._sprites["ball"].vitesse = self.state.ball.vitesse

    def reset(self):
        self._state = None
        self._sprites = dict()
        self._background = BackgroundSprite()
        self.hud = Hud()
        try:
            self.simu.listeners -= self
        except Exception:
            pass
        self.simu = None
    def draw(self):
        try:
            if self.state:
                self._update_sprites()
                gl.glClear(gl.GL_COLOR_BUFFER_BIT)
                self._background.draw()
                for d in self._sprites.values():
                    d.draw()
                self.hud.draw()
        except Exception as e:
            time.sleep(0.0001)
            logger.error("%s\n\t%s" %(e, traceback.format_exc()))
            raise e

    def _increase_fps(self):
        self._fps = min(self._fps + FPS_MOD, 200)
    def _decrease_fps(self):
        self._fps = max(self._fps - FPS_MOD, 1)
    def on_draw(self):
        self.draw()

    def on_key_press(self, symbol, modifiers):
        if symbol in self.key_handlers:
            handler = self.key_handlers.get(symbol, lambda w: None)
            handler(self)
            return pyglet.event.EVENT_HANDLED
        k=pyglet.window.key.symbol_string(symbol)
        if modifiers & pyglet.window.key.MOD_SHIFT:
                k=k.capitalize()
        else:
                k=k.lower()
        try:
            self.simu.send_strategy(k)
        except  Exception:
            pass
        return pyglet.event.EVENT_HANDLED

    def on_resize(self, width, height):
        pyglet.window.Window.on_resize(self, width, height)
        self.focus()
        return pyglet.event.EVENT_HANDLED

    def focus(self):
        try:
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()
            gl.gluOrtho2D(0, settings.GAME_WIDTH, 0, settings.GAME_HEIGHT + HUD_HEIGHT)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()
        except Exception as e:
            time.sleep(0.0001)
            logger.error("%s\n\t%s"  %(e, traceback.format_exc()))

    def on_close(self):
        pyglet.window.Window.on_close(self)
        return pyglet.event.EVENT_HANDLED

    def exit(self):
        if hasattr(self.simu, "kill"):
            self.simu.kill()
        self.simu.listeners -= self
        pyglet.clock.unschedule(self.update)
        self.close()
        pyg_stop()
        return pyglet.event.EVENT_HANDLED

    def change_state(self, state):
        self._state = state.copy()

    def set(self, simu):
        self.simu = simu
        try:
            self.simu.listeners += self
        except Exception:
            pass
    def show(self,state):
        self._state = state
        self.update()
    def play(self):
        try:
            self.simu.start_thread()
        except Exception:
            pass

    def get_state(self):
        try:
            return self._state
        except Exception:
            return None
    def get_team(self, i):
        try:
            return self.simu.get_team(i)
        except Exception:
            return None
    def get_score(self,i):
        try:
            return self.state.get_score_team(i)
        except Exception:
            return 0

    def get_max_steps(self):
        try:
            return self.max_steps
        except Exception:
            pass
        try:
            return self.state.max_steps
        except Exception:
            pass
        return settings.MAX_GAME_STEPS

    def update_round(self, team1, team2, state):
        self.change_state(state)
        self._wait_next()

    def begin_match(self, team1, team2, state):
        pass

    def begin_round(self, team1, team2, state):
        self.change_state(state)

    def end_round(self, team1, team2, state):
        self.change_state(state)
        pass

    def end_match(self, team1, team2, state):
        pass


def show_simu(simu):
    gui = SimuGUI(simu)
    pyg_start()

def show_state(state):
    gui = SimuGUI()
    gui.show(state)
    pyg_start()

def pyg_start():
    pyglet.app.run()

def pyg_stop():
    pyglet.app.exit()
