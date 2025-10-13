__author__ = 'github.com/arm61'

from typing import Union
from distutils.util import strtobool
from PySide2.QtCore import QObject
from PySide2.QtCore import Signal
from PySide2.QtCore import Property
from PySide2.QtCore import Slot
import numpy as np

from easyscience.Constraints import ObjConstraint
from easyscience.Constraints import NumericConstraint
from easyscience.Constraints import FunctionalConstraint
from easyscience.utils.io.xml import XMLSerializer
from easyscience import global_object
from easyscience.utils.classTools import generatePath


class ParameterProxy(QObject):

    parametersAsXmlChanged = Signal()
    parametersAsObjChanged = Signal()

    parametersFilterCriteriaChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self._parameters_as_obj = []
        self._n_fit = False
        self._parameters_as_xml = ""

        self._parameters_filter_criteria = ""

        self.parametersFilterCriteriaChanged.connect(
            self._onParametersFilterCriteriaChanged)

    # # #
    # Setters and getters
    # # #

    @Property('QVariant', notify=parametersAsObjChanged)
    def parametersAsObj(self):
        return self._parameters_as_obj

    @Property(bool, notify=parametersAsObjChanged)
    def nFit(self):
        return self._n_fit

    def _setParametersAsObj(self):
        self._parameters_as_obj.clear()

        par_ids, par_paths = generatePath(self.parent._model_proxy._model, True)
        pids = []
        self._n_fit = False
        for par_index, par_path in enumerate(par_paths):
            par_id = par_ids[par_index]
            if par_id in pids:
                continue
            pids.append(par_id)
            par = global_object.map.get_item_by_key(par_id)
            path_split = par_path.split('.')
            if path_split[-1] == 'repetitions' and par.value == 1:
                continue
            if not par.enabled:
                continue
            unit = par.unit
            label = get_label(par_path)
            if label is None:
                continue
            if self._parameters_filter_criteria.lower() not in label.lower():
                continue
            if not par.fixed: 
                self._n_fit = True
            self._parameters_as_obj.append({
                "id": str(par_id),
                "number": par_index + 1,
                "label": label,
                "value": par.value,
                "unit": unit,
                "error": float(par.error),
                "fit": int(not par.fixed),
                "min": float(par.min),
                "max": float(par.max)
            })

        self.parametersAsObjChanged.emit()

    @Property(str, notify=parametersAsXmlChanged)
    def parametersAsXml(self):
        return self._parameters_as_xml

    def _setParametersAsXml(self):
        self._parameters_as_xml = XMLSerializer().encode({"item":self._parameters_as_obj}, data_only=True)
        self.parametersAsXmlChanged.emit()

    @Slot(str)
    def setParametersFilterCriteria(self, new_criteria):
        if self._parameters_filter_criteria == new_criteria:
            return
        self._parameters_filter_criteria = new_criteria
        self.parametersFilterCriteriaChanged.emit()

    # # #
    # Actions
    # # #

    def _onParametersChanged(self):
        self._setParametersAsObj()
        self._setParametersAsXml()
        self.parent._state_proxy.stateChanged.emit(True)

    def _onParametersFilterCriteriaChanged(self):
        self._onParametersChanged()

    @Slot(str, 'QVariant')
    def editParameter(self, obj_id: str,
                      new_value: Union[bool, float,
                                       str]):
        if not obj_id:
            return

        obj = self._parameterObj(obj_id)
        if obj is None:
            return

        if isinstance(new_value, bool):
            if obj.fixed == (not new_value):
                return

            obj.fixed = not new_value
            self._onParametersChanged()
            self.parent._undoredo_proxy.undoRedoChanged.emit()

        else:
            if obj.value == new_value:
                return

            obj.value = new_value
            self.parent.sampleChanged.emit()

    @Slot(str, 'QVariant')
    def editParameterMin(self, obj_id: str, new_value: Union[float, str]):
        if not obj_id:
            return
        
        obj = self._parameterObj(obj_id)
        if obj is None:
            return 
        
        if isinstance(new_value, str):
            new_value = new_value.lower()
            if new_value == '-inf':
                new_value = -np.inf
            if new_value == '+inf':
                new_value = np.inf
            
        new_value = float(new_value)

        if obj.min == new_value:
            return 
        
        obj.min = new_value
        self.parent.sampleChanged.emit()

    @Slot(str, 'QVariant')
    def editParameterMax(self, obj_id: str, new_value: Union[float, str]):
        if not obj_id:
            return
        
        obj = self._parameterObj(obj_id)
        if obj is None:
            return 
        
        if isinstance(new_value, str):
            new_value = new_value.lower()
            if new_value == '-inf':
                new_value = -np.inf
            if new_value == '+inf':
                new_value = np.inf

        new_value = float(new_value)
        
        if obj.min == new_value:
            return 
        
        obj.max = new_value
        self.parent.sampleChanged.emit()

    def _parameterObj(self, obj_id: str):
        if not obj_id:
            return
        obj = global_object.map.get_item_by_key(obj_id)
        return obj

    # Constraints
    @Slot(int, str, float, str, int)
    def addConstraint(self, dependent_par_idx, relational_operator,
                      value, arithmetic_operator, independent_par_idx):
        if dependent_par_idx == -1 or value == "":
            print("Failed to add constraint: Unsupported type")
            return
        # if independent_par_idx == -1:
        #    print(f"Add constraint: {self.fitablesList()[dependent_par_idx]['label']}{relational_operator}{value}")
        # else:
        #    print(f"Add constraint: {self.fitablesList()[dependent_par_idx]['label']}{relational_operator}{value}{arithmetic_operator}{self.fitablesList()[independent_par_idx]['label']}")
        pars = []
        pids = []
        par_ids, par_paths = generatePath(self.parent._model_proxy._model, True)
        for par_index, par_path in enumerate(par_paths):
            par_id = par_ids[par_index]
            if par_id in pids:
                continue
            pids.append(par_id)
            par = global_object.map.get_item_by_key(par_id)
            path_split = par_path.split('.')
            if path_split[-1] == 'repetitions' and par.value == 1:
                continue
            if not par.enabled:
                continue
            label = get_label(par_path)
            if label is None:
                continue
            pars.append(par)
        if arithmetic_operator != "" and independent_par_idx > -1:
            c = ObjConstraint(pars[dependent_par_idx],
                              str(float(value)) + arithmetic_operator,
                              pars[independent_par_idx])
        elif arithmetic_operator == "" and independent_par_idx == -1:
            c = NumericConstraint(pars[dependent_par_idx],
                                  relational_operator.replace("=", "=="),
                                  float(value))
        else:
            print("Failed to add constraint: Unsupported type")
            return
        # print(c)
        pars[independent_par_idx].user_constraints[pars[dependent_par_idx].name] = c
        c()
        self.parent.sampleChanged.emit()
        self.parametersAsObjChanged.emit()

    def constraintsList(self):
        constraint_list = []
        number = 0
        for index, constraint in enumerate(self.parent._model_proxy._model.constraints):
            if type(constraint) is ObjConstraint:
                par = constraint.get_obj(constraint.independent_obj_ids)
                independent_name = get_label(get_par_path(par, self.parent._model_proxy._model))
                relational_operator = "="
                if constraint.operator == '':
                    continue
                else:
                    value = float(constraint.operator[:-1])
                    arithmetic_operator = constraint.operator[-1]
            elif type(constraint) is NumericConstraint:
                independent_name = ""
                relational_operator = constraint.operator.replace("==", "=")
                value = constraint.value
                arithmetic_operator = ""
            elif type(constraint) is FunctionalConstraint:
                continue
            else:
                print(f"Failed to get constraint: Unsupported type {type(constraint)}")
                return
            number += 1
            par = constraint.get_obj(constraint.dependent_obj_ids)
            dependent_name = get_label(get_par_path(par, self.parent._model_proxy._model))
            enabled = int(constraint.enabled)
            constraint_list.append(
                {"number": number,
                 "index": index + 1,
                 "dependentName": dependent_name,
                 "relationalOperator": relational_operator,
                 "value": value,
                 "arithmeticOperator": arithmetic_operator,
                 "independentName": independent_name,
                 "enabled": enabled}
            )
        return constraint_list

    @Property(str, notify=parametersAsObjChanged)
    def constraintsAsXml(self):
        # xml = dicttoxml(self.constraintsList(), attr_type=False)
        xml = XMLSerializer().encode({"item":self.constraintsList()}, data_only=True)
        # xml = xml.decode()
        return xml

    @Slot(int)
    def removeConstraintByIndex(self, index: int):
        constraint = self.parent._model_proxy._model.constraints[index]
        independent_obj = constraint.get_obj(constraint.independent_obj_ids)
        dependent_obj_name = constraint.get_obj(constraint.dependent_obj_ids).name
        del independent_obj.user_constraints[dependent_obj_name] 
        self.parent.sampleChanged.emit()

    @Slot(int, str)
    def toggleConstraintByIndex(self, index, enabled):
        constraint = self.parent._model_proxy._model.constraints[index]
        independent_obj = constraint.get_obj(constraint.independent_obj_ids)
        dependent_obj_name = constraint.get_obj(constraint.dependent_obj_ids).name
        independent_obj.user_constraints[dependent_obj_name].enabled = bool(strtobool(enabled))
        self.parent.sampleChanged.emit()

    def removeAllConstraints(self):
        for _ in range(len(self.eFitter.easy_science_multi_fitter.fit_constraints())):
            self.removeConstraintByIndex(0)
        self.constraintsRemoved.emit()
        self.sampleChanged.emit()

def get_label(par_path: str) -> str:
    """
    Generate the label
    
    :param par_path: Path for the parameter.
    
    :return: The label.
    """
    path_split = par_path.split('.')
    model = [(' ').join(path_split[0:1] + ['-'])]
    # Handle sld and isld
    if path_split[-1][-3:] == 'sld':
        label = (' ').join(par_path.split('.')[-2:])
        label = label[:-3] + 'SLD'
    elif path_split[-1] == 'thickness':
        label = (' ').join(model + par_path.split('.')[-2:])
        label = label[:-9] + 'Thickness'
    elif path_split[-1] == 'roughness':
        label = (' ').join(model + par_path.split('.')[-2:])
        label = label[:-9] + 'Roughness'
    elif path_split[-1] == 'repetitions':
        label = (' ').join(model + par_path.split('.')[-2:])
        label = label[:-11] + 'Repetitions'
    elif path_split[-1] =='scale':
        label =  model[0] + ' Scaling'
    elif path_split[-1] == 'background':
        label =  model[0] + ' Background'
    elif path_split[-1] == 'resolution':
        label =  model[0] + ' Resolution (dq/q)'
        unit = '%'
    elif path_split[-1] == 'solvent_fraction':
        label = model[0] + ' Fractional '
        label += par_path.split('.')[-2]
    elif path_split[-1] == 'area_per_molecule':
        label = model[0] + ' ' + par_path.split('.')[-2].split('/')[0]
        label = label + ' APM'
    elif path_split[-1][:-5] == 'scattering_length': 
        label = None
    return label

def get_par_path(par, model):
    route = global_object.map.reverse_route(par.unique_name, model.unique_name)
    objs = [getattr(global_object.map.get_item_by_key(r), "name") for r in route]
    objs.reverse()
    return ".".join(objs[1:]) 