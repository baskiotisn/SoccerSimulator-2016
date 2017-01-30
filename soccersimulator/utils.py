# -*- coding: utf-8 -*-<
import math
import string
import random
import json
from . import settings
import zlib
valid_chars = frozenset("%s%s%s" % (string.ascii_letters, string.digits, "_"))

def fmt(x):
    if type(x)==float:
        return round(x,settings.PREC)
    return x
def clean_fn(fn):
    return ''.join(c if c in valid_chars else '' for c in fn)


class MyJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj,'to_dict'):
            tmp = obj.to_dict()
            tmp.update({'__class__':obj.__class__.__name__, '__module__':obj.__module__})
            return tmp
        return json.JSONEncoder.default(self, obj)


class MyJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if '__class__' in obj:
            class_name = obj.pop('__class__')
            module_name = obj.pop('__module__')
            module = __import__(module_name)
            class_ = getattr(module, class_name)
            args = dict( (key, value) for key, value in obj.items())
            inst = class_(**args)
            return inst
        if '_dic_m' in obj:
            obj.pop('_dic_m')
            return dict([(eval(k),v) for k,v in obj.items()])
        return obj

class JSONable(object):
    def to_dict(self):
        return dict([(k,fmt(v)) for k,v in self.__dict__.items()])
    def to_json(self):
        return json.dumps(self,cls = MyJSONEncoder)
    @staticmethod
    def from_json(strg):
        return json.loads(strg,cls=MyJSONDecoder)

def dump(obj,fname):
    with open(fname,"w") as f:
        f.write(zlib.compress(obj.to_json()))
def load(fname):
    with open(fname,"r") as f:
        return JSONable.from_json(zlib.decompress(f.read()))


class Vector2D(JSONable):
    """ Vecteur 2D : peut etre creer soit par ses coordonnees (x,y) soit par ses coordonnees polaire
    angle et norme.
    """

    def __init__(self, x=0., y=0., angle=None, norm=None):
        """ create a vector
        :param x: 1ere coordonnee
        :param y: 2nd coordonnee
        :param angle: angle en radian
        ;param norm: norme du vecteur
        """
        if angle is not None and norm is not None:
            self._x = math.cos(angle) * norm
            self._y = math.sin(angle) * norm
            return
        self._x = float(x)
        self._y = float(y)

    @property
    def x(self):
        """
        1ere coordonnee
        """
        return self._x

    @x.setter
    def x(self, value):
        self._x = float(value)

    @property
    def y(self):
        """
        2nd coordonnee
        """
        return self._y

    @y.setter
    def y(self, value):
        self._y = float(value)

    @property
    def norm(self):
        """
        norme du vecteur
        :return : la norme
        """
        return math.sqrt(self.dot(self))

    @norm.setter
    def norm(self, n):
        if self.norm == 0:
            return
        self.normalize()
        self *= n

    @property
    def angle(self):
        """
        angle du vector
        """
        return math.atan2(self.y, self.x)

    @angle.setter
    def angle(self, a):
        n = self.norm
        self.x = math.cos(a) * n
        self.y = math.sin(a) * n

    def set(self, v):
        """ Fixe la valeur du vecteur
        :param v: Vecteur
        :return:
        """
        self.x = v.x
        self.y = v.y
        return self

    def random(self, low=0., high=1.):
        """
        Randomize the vector
        :param float low: low limit
        :param float high: high limit
        """
        self.x = random.random() * (high - low) + low
        self.y = random.random() * (high - low) + low
        return self

    def distance(self, v):
        """ distance au vecteur
        :param v: vecteur
        ;return : distance
        """
        return (v - self).norm

    def dot(self, v):
        """ produit scalaire
            ;param v: vecteur
        """
        return self.x * v.x + self.y * v.y

    def normalize(self):
        """
        Normalise le vecteur
        """
        n = self.norm
        if n != 0:
            self *= 1. / n
        return self

    def scale(self, a):
        """
        Multiplie par a le vecteur
        :param float a: facteur
        """
        self.x *= a
        self.y *= a
        return self

    def norm_max(self, n):
        """ Normalise le vecteur a la norme n si supérieur
        :param n:
        :return: vecteur normalise
        """
        n_old = self.norm
        if n_old == 0:
            return self
        if n_old <= n:
            return self
        return self.scale(n*1./n_old)

    def copy(self):
        """ operateur de copie
        """
        return Vector2D(self.x, self.y)

    @classmethod
    def from_polar(cls, angle, norm):
        """
        Cree le vecteur a partir des coordonnees polaires
        :param float angle: angle
        :param float norm: norme
        :return: vecteur
        """
        return cls(angle=angle, norm=norm)

    @classmethod
    def create_random(cls, low=0, high=1.):
        """
        Cree un vecteur aleatoire entre lov et high
        :param float low: valeur minimale
        :param float high: valeur maximale exclue
        :return: vecteur
        """
        res = cls()
        res.random(low, high)
        return res

    @classmethod
    def from_str(cls, strg):
        """ Cree un vecteur a partir de la representation texte (x,y)
        :param strg: representation texte
        :return: vecteur
        """
        l_pos = strg.split(",")
        if len(l_pos) != 2 or l_pos[0][0] != "(" or l_pos[1][-1] != ")":
            raise DecodeException("Wrong format for %s : %s", (cls, strg))
        return cls(float(l_pos[0][1:]), float(l_pos[1][:-1]))

    @classmethod
    def from_list_str(cls, strg):
        """ Cree une liste de vecteur a partir de la representation texte (x1,y1)(x2,y2)...
        :param strg: representation texte
        :return: vecteur
        """
        res = []
        idx = 0
        nidx = strg.find(")", idx)
        while nidx != -1:
            res.append(cls.from_str(strg[idx:(nidx + 1)]))
            idx = nidx + 1
            nidx = strg.find(")", idx)
        return res

    def __repr__(self):
        return "Vector2D(%f,%f)" % (self.x,self.y)
    def __str__(self):
        return "(%f,%f)" % (self.x, self.y)
    def to_dict(self):
        return dict(x=fmt(self.x),y=fmt(self.y))

    def __eq__(self, other):
        return (other.x == self.x) and (other.y == self.y)

    def __add__(self, other):
        if isinstance(other, Vector2D):
            return Vector2D(self.x + other.x, self.y + other.y)
        return Vector2D(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, Vector2D):
            return Vector2D(self.x - other.x, self.y - other.y)
        return Vector2D(self.x - other, self.y - other)

    def __iadd__(self, other):
        if isinstance(other, Vector2D):
            self.x += other.x
            self.y += other.y
        else:
            self.x += other
            self.y += other
        return self

    def __isub__(self, other):
        if isinstance(other, Vector2D):
            self.x -= other.x
            self.y -= other.y
        else:
            self.x -= other
            self.y -= other
        return self

    def __imul__(self, other):
        if isinstance(other, Vector2D):
            self.x *= other.x
            self.y *= other.y
        else:
            self.x *= other
            self.y *= other
        return self

    def __mul__(self, other):
        if isinstance(other, Vector2D):
            return Vector2D(self.x * other.x, self.y * other.y)
        return Vector2D(self.x * other, self.y * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __idiv__(self, other):
        if isinstance(other, Vector2D):
            self.x /= other.x
            self.y /= other.y
        else:
            self.x /= other
            self.y /= other
        return self

    def __div__(self, other):
        if isinstance(other, Vector2D):
            return Vector2D(self.x / other.x, self.y / other.y)
        return Vector2D(self.x / other, self.y / other)
    def __truediv__(self,other):
        return self.__div__(other)

class MobileMixin(JSONable):
    """ Mixin pour représenter un objet mobile. Dispose d'un vecteur position et d'un vecteur vitesse.
    """
    def __init__(self, position=None, vitesse=None, *args, **kwargs):
        """
        :param position: position du mobile (Vector2D)
        :param vitesse: vitesse du mobile (Vector2D)
        :return:
        """
        if position is None:
            position = Vector2D()
        if vitesse is None:
            vitesse = Vector2D()
        self._position = position
        self._vitesse = vitesse
    @property
    def vitesse(self):
        return self._vitesse
    @vitesse.setter
    def vitesse(self, v):
        self._vitesse.set(v)
    @property
    def position(self):
        return self._position
    @position.setter
    def position(self, v):
        self._position.set(v)

    @classmethod
    def from_position(cls, x, y):
        """ Construit a partir de deux reels (x,y)
        :param x:
        :param y:
        :return:
        """
        return cls(position=Vector2D(x, y))

    def to_str(self):
        """
        :return: representation texte du mobile
        """
        return self.__str__()

    @classmethod
    def from_json(cls, strg):
        """ Construit le mobile a partir de la description texte
        :param strg:
        :return:
        """
        return cls(x=Vector2D.strg["x"])
    def __str__(self):
        return "%s,%s" % (self.position, self.vitesse)
    def __repr__(self):
        return self.__str__()
    def to_dict(self):
        return dict(position=self.position,vitesse=self.vitesse)
