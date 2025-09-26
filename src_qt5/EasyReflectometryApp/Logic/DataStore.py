__author__ = 'github.com/wardsimon'

from typing import Union
from typing import TypeVar

import numpy as np
from collections.abc import Sequence

from easyscience.Objects.core import ComponentSerializer
from easyscience.utils.io.dict import DictSerializer
from easyreflectometry.model import Model

T = TypeVar('T')


class ProjectData(ComponentSerializer):
    def __init__(self, name='DataStore', exp_data=None, sim_data=None):
        self.name = name
        if exp_data is None:
            exp_data = DataStore(name='Exp Datastore')
        if sim_data is None:
            sim_data = DataStore(name='Sim Datastore')
        self.exp_data = exp_data
        self.sim_data = sim_data


class DataStore(Sequence, ComponentSerializer):

    def __init__(self, *args, name='DataStore'):
        self.name = name
        self.items = list(args)
        self.show_legend = False

    def __getitem__(self, i: int) -> T:
        return self.items.__getitem__(i)

    def __len__(self) -> int:
        return len(self.items)

    def __setitem__(self, key, value):
        self.items[key] = value

    def __delitem__(self, key):
        del self.items[key]

    def append(self, *args):
        self.items.append(*args)

    def as_dict(self, skip: list = []) -> dict:
        this_dict = super(DataStore, self).as_dict(self)
        this_dict['items'] = [
            item.as_dict() for item in self.items if hasattr(item, 'as_dict')
        ]

    @classmethod
    def from_dict(cls, d):
        items = d['items']
        del d['items']
        obj = cls.from_dict(d)
        decoder = DictSerializer()
        obj.items = [decoder.decode(item) for item in items]
        return obj

    @property
    def experiments(self):
        return [self[idx] for idx in range(len(self)) if self[idx].is_experiment]

    @property
    def simulations(self):
        return [self[idx] for idx in range(len(self)) if self[idx].is_simulation]


class DataSet1D(ComponentSerializer):

    def __init__(self, name: str = 'Series',
                 x: Union[np.ndarray, list] = None,
                 y: Union[np.ndarray, list] = None,
                 ye: Union[np.ndarray, list] = None,
                 xe: Union[np.ndarray, list] = None,
                 model: Model = None,
                 x_label: str = 'x',
                 y_label: str = 'y'):

        self._model = model
        self._model.background = np.min(y)

        if x is None:
            x = np.array([])
        if y is None:
            y = np.array([])
        if ye is None:
            ye = np.zeros_like(x)
        if xe is None: 
            xe = np.zeros_like(x)

        self.name = name
        if not isinstance(x, np.ndarray):
            x = np.array(x)
        if not isinstance(y, np.ndarray):
            y = np.array(y)

        self.x = x
        self.y = y
        self.ye = ye
        self.xe = xe

        self.x_label = x_label
        self.y_label = y_label

        self._color = None

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, new_model):
        self._model = new_model
        self._model.background = np.min(self.y)

    @property
    def is_experiment(self) -> bool:
        return self._model is not None

    @property
    def is_simulation(self) -> bool:
        return self._model is None

    def __repr__(self) -> str:
        return "1D DataStore of '{:s}' Vs '{:s}' with {} data points".format(self.x_label, self.y_label, len(self.x))
