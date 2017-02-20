# -*- coding: utf-8 -*-<
import math
import string
import random
import json
from . import settings
import zlib
import base64
valid_chars = frozenset("%s%s%s" % (string.ascii_letters, string.digits, "_"))

def fmt(x):
    if type(x)==float:
        return round(x,settings.PREC)
    return x
def clean_fn(fn):
    return ''.join(c if c in valid_chars else '' for c in fn)


def to_json(obj):
    return json.dumps(obj,cls = MyJSONEncoder,ensure_ascii=False,encoding="utf-8")
def from_json(strg):
    return json.loads(strg,cls=MyJSONDecoder)
def from_jsonz(strg):
    return from_json(zlib.decompress(base64.b64decode(strg)))
def to_jsonz(obj):
    return base64.b64encode(zlib.compress(to_json(obj)))
def dump_jsonz(obj,fname):
    with open(fname,"w") as f:
        f.write(to_jsonz(obj))
def load_jsonz(fname):
    with open(fname,"r") as f:
        return from_jsonz(f.read())

def dict_to_json(obj):
    return dict( [("_dic_m",0)]+[(k.__repr__(),v) for k,v in obj.items()])

class MyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'to_dict'):
            tmp = obj.to_dict()
            tmp.update({'__class__':obj.__class__.__name__, '__module__':obj.__module__})
            return tmp
        return json.JSONEncoder.default(self, obj)

class MyJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super(MyJSONDecoder,self).__init__(object_hook=self.object_hook, *args, **kwargs)
    def object_hook(self, obj):
        if '__class__' in obj:
            class_name = obj.pop('__class__')
            module_name = obj.pop('__module__')
            module = __import__(module_name)
            class_ = getattr(module, class_name)
            args = dict((key, value) for key, value in obj.items())
            inst = class_(**args)
            return inst
        if '_dic_m' in obj:
            obj.pop('_dic_m')
            return dict([(eval(k),v) for k,v in obj.items()])
        return obj


class Vector2D(object):
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

class MobileMixin(object):
    """ Mixin pour représenter un objet mobile. Dispose d'un vecteur position et d'un vecteur vitesse.
    """
    def __init__(self, position=None, vitesse=None, *args, **kwargs):
        """
        :param position: position du mobile (Vector2D)
        :param vitesse: vitesse du mobile (Vector2D)
        :return:
        """
        self._position = position or Vector2D()
        self._vitesse = vitesse or Vector2D()
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
    def __str__(self):
        return "%s,%s" % (self.position, self.vitesse)
    def __repr__(self):
        return self.__str__()
    def to_dict(self):
        return dict(position=self.position,vitesse=self.vitesse)
