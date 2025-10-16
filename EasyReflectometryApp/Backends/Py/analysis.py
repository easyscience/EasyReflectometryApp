from typing import List
from typing import Optional

from easyreflectometry import Project as ProjectLib
from PySide6 import QtWidgets
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from .logic.calculators import Calculators as CalculatorsLogic
from .logic.experiments import Experiments as ExperimentLogic
from .logic.fitting import Fitting as FittingLogic
from .logic.minimizers import Minimizers as MinimizersLogic
from .logic.parameters import Parameters as ParametersLogic


class Analysis(QObject):
    minimizerChanged = Signal()
    calculatorChanged = Signal()
    experimentsChanged = Signal()
    parametersChanged = Signal()
    parametersIndexChanged = Signal()
    fittingChanged = Signal()

    externalMinimizerChanged = Signal()
    externalParametersChanged = Signal()
    externalCalculatorChanged = Signal()
    externalFittingChanged = Signal()
    externalExperimentChanged = Signal()

    def __init__(self, project_lib: ProjectLib, parent=None):
        super().__init__(parent)
        self._parameters_logic = ParametersLogic(project_lib)
        self._fitting_logic = FittingLogic(project_lib)
        self._calculators_logic = CalculatorsLogic(project_lib)
        self._experiments_logic = ExperimentLogic(project_lib)
        self._minimizers_logic = MinimizersLogic(project_lib)
        self._chached_parameters = None
        # Add support for multiple selected experiments - initialize to empty first to avoid binding loops
        self._selected_experiment_indices = []

    def _initialize_selected_experiments(self) -> None:
        """Initialize selected experiment indices after object construction to avoid binding loops."""
        available_experiments = self._experiments_logic.available()
        if len(available_experiments) > 0:
            self._selected_experiment_indices = [0]
        else:
            self._selected_experiment_indices = []

    ########################
    ## Fitting
    @Property(str, notify=fittingChanged)
    def fittingStatus(self) -> str:
        return self._fitting_logic.status

    @Property(bool, notify=fittingChanged)
    def fittingRunning(self) -> bool:
        return self._fitting_logic.running

    @Property(bool, notify=fittingChanged)
    def isFitFinished(self) -> bool:
        return self._fitting_logic.fit_finished

    @Slot(None)
    def fittingStartStop(self) -> None:
        # make sure we can run the fitting
        if not self.prefitCheck():
            return
        self._fitting_logic.start_stop()
        self.fittingChanged.emit()
        self._clearCacheAndEmitParametersChanged()
        self.externalFittingChanged.emit()

    def prefitCheck(self) -> bool:
        """
        Perform a pre-fit check to ensure that all parameters are set correctly.
        Returns True if the check passes, False otherwise.
        """
        # 1. wrong bounds on parameters
        for param in self.fitableParameters:
            if not param['fit']:
                continue
            if param['min'] >= param['max']:
                QtWidgets.QMessageBox.warning(
                    None,
                    "Invalid Parameter Bounds",
                    f"Parameter '{param['name']}' has invalid bounds: "
                    f"min ({param['min']}) must be less than max ({param['max']})."
                )
                return False

        # 2. differential evolution needs finite bounds on all parameters
        if 'differential_evolution' in self.minimizersAvailable[self.minimizerCurrentIndex]:
            bad_params = []
            for param in self.fitableParameters:
                if not param['fit']:
                    continue
                if param['min'] == float('-inf') or param['max'] == float('inf'):
                    bad_params.append(param['name'])
            if bad_params:
                joined = '\n' + ',\n'.join(bad_params) + '\n'
                # Show a warning in a message box
                QtWidgets.QMessageBox.warning(
                    None,
                    "Invalid Parameter Bounds",
                    f"Parameters {joined} have infinite bounds, "
                    "which is not allowed for differential evolution minimizer."
                )

                return False

        return True

    ########################
    ## Calculators
    @Property('QVariantList', notify=calculatorChanged)
    def calculatorsAvailable(self) -> List[str]:
        return self._calculators_logic.available()

    @Property(int, notify=calculatorChanged)
    def calculatorCurrentIndex(self) -> int:
        return self._calculators_logic.current_index()

    @Slot(int)
    def setCalculatorCurrentIndex(self, new_value: int) -> None:
        if self._calculators_logic.set_current_index(new_value):
            self.calculatorChanged.emit()
            self.externalCalculatorChanged.emit()

    ########################
    ## Experiments
    @Property('QVariantList', notify=experimentsChanged)
    def experimentsAvailable(self) -> List[str]:
        return self._experiments_logic.available()

    @Property(int, notify=experimentsChanged)
    def experimentCurrentIndex(self) -> int:
        return self._experiments_logic.current_index()

    @Slot(int)
    def setExperimentCurrentIndex(self, new_value: int) -> None:
        if self._experiments_logic.set_current_index(new_value):
            self.experimentsChanged.emit()
            self.externalExperimentChanged.emit()

    @Slot(int)
    def setModelOnExperiment(self, new_value: int) -> None:
        self._experiments_logic.set_model_on_experiment(new_value)
        self.experimentsChanged.emit()

    @Slot(str)
    def setExperimentName(self, new_name: str) -> None:
        self._experiments_logic.set_experiment_name(new_name)
        self.experimentsChanged.emit()
        self.externalExperimentChanged.emit()

    @Slot(int, str)
    def setExperimentNameAtIndex(self, index: int, new_name: str) -> None:
        self._experiments_logic.set_experiment_name_at_index(index, new_name)
        self.experimentsChanged.emit()
        self.externalExperimentChanged.emit()

    @Property(int, notify=experimentsChanged)
    def modelIndexForExperiment(self) -> int:
        # return the model index for the current experiment
        models = self._experiments_logic._project_lib._models
        experiments = self._experiments_logic._project_lib._experiments
        index = self.experimentCurrentIndex
        current_experiment = experiments[index] if 0 <= index < len(experiments) else None
        if current_experiment is not None:
            t = models.index(current_experiment.model)
            return t
        return -1

    @Property('QVariantList', notify=experimentsChanged)
    def modelNamesForExperiment(self) -> list:
        # return a list of model names for each experiment
        mapped_models = []
        experiments = self._experiments_logic._project_lib._experiments
        for ind in experiments:
            mapped_models.append(experiments[ind].model.name)
        return mapped_models

    @Property('QVariantList', notify=experimentsChanged)
    def modelColorsForExperiment(self) -> list:
        # return a list of model colors for each experiment
        mapped_models = []
        experiments = self._experiments_logic._project_lib._experiments
        for ind in experiments:
            mapped_models.append(experiments[ind].model.color)
        return mapped_models

    @Slot(int)
    def removeExperiment(self, index: int) -> None:
        """
        Remove the experiment at the given index.
        """
        if 0 <= index < len(self._experiments_logic.available()):
            self._experiments_logic.remove_experiment(index)
            self.experimentsChanged.emit()
            self.externalExperimentChanged.emit()
        else:
            print(f"Experiment index {index} is out of range.")

    ########################
    ## Multi-experiment selection support
    # (Initialize selected experiments in the existing __init__ method)

    @Property(int, notify=experimentsChanged)
    def experimentsSelectedCount(self) -> int:
        """Return the count of currently selected experiments."""
        return len(self._selected_experiment_indices)

    @Property('QVariantList', notify=experimentsChanged)
    def selectedExperimentIndices(self) -> List[int]:
        """Return the list of selected experiment indices."""
        return self._selected_experiment_indices

    @Slot('QVariantList')
    def setSelectedExperimentIndices(self, indices: List[int]) -> None:
        """Set multiple selected experiment indices."""
        print(f"setSelectedExperimentIndices called with: {indices}")
        
        # Validate indices
        available_count = len(self._experiments_logic.available())
        valid_indices = [i for i in indices if 0 <= i < available_count]
        
        print(f"Available experiments: {available_count}, Valid indices: {valid_indices}")
        print(f"Current selection: {self._selected_experiment_indices}")
        
        if valid_indices != self._selected_experiment_indices:
            previous_selection = self._selected_experiment_indices.copy()
            self._selected_experiment_indices = valid_indices
            print(f"Selection changed from {previous_selection} to {self._selected_experiment_indices}")
            
            # Update current experiment index to first selected (or 0 if no selection)
            if valid_indices:
                self._experiments_logic.set_current_index(valid_indices[0])
                print(f"Set current experiment index to: {valid_indices[0]}")
            elif len(self._experiments_logic.available()) > 0:
                # If no selection but experiments available, default to first experiment
                self._experiments_logic.set_current_index(0)
                self._selected_experiment_indices = [0]  # Auto-select first experiment
                print(f"Auto-selected first experiment, final selection: {self._selected_experiment_indices}")
            
            # Always trigger plotting refresh when selection changes
            print("Triggering plotting system refresh...")
            self._refresh_plotting_system()
            
            self.experimentsChanged.emit()
            self.externalExperimentChanged.emit()
            print("✓ Multi-experiment selection updated and signals emitted")
        else:
            print("No change in selection - skipping update")

    def get_concatenated_experiment_data(self):
        """
        Concatenate data from all selected experiments.
        Returns a combined DataSet1D object.
        """
        import numpy as np
        from easyreflectometry.data import DataSet1D
        
        if not self._selected_experiment_indices:
            return DataSet1D(name='No experiments selected', x=np.empty(0), y=np.empty(0), ye=np.empty(0), xe=np.empty(0))
        
        all_x, all_y, all_ye, all_xe = [], [], [], []
        
        for exp_idx in self._selected_experiment_indices:
            try:
                data = self._experiments_logic._project_lib.experimental_data_for_model_at_index(exp_idx)
                if data.x.size > 0:  # Only include non-empty datasets
                    all_x.extend(data.x)
                    all_y.extend(data.y)
                    all_ye.extend(data.ye if hasattr(data, 'ye') and data.ye.size > 0 else np.zeros_like(data.y))
                    all_xe.extend(data.xe if hasattr(data, 'xe') and data.xe.size > 0 else np.zeros_like(data.x))
            except (IndexError, AttributeError) as e:
                print(f"Error accessing experiment {exp_idx}: {e}")
                continue
        
        if not all_x:
            return DataSet1D(name='No valid experiment data', x=np.empty(0), y=np.empty(0), ye=np.empty(0), xe=np.empty(0))
        
        # Sort by x values to maintain proper order
        combined_data = list(zip(all_x, all_y, all_ye, all_xe))
        combined_data.sort(key=lambda item: item[0])
        
        x_sorted, y_sorted, ye_sorted, xe_sorted = zip(*combined_data) if combined_data else ([], [], [], [])
        
        exp_names = [self._experiments_logic.available()[i] 
                     for i in self._selected_experiment_indices if i < len(self._experiments_logic.available())]
        combined_name = f"Combined: {', '.join(exp_names)}"
        
        return DataSet1D(
            name=combined_name,
            x=np.array(x_sorted),
            y=np.array(y_sorted),
            ye=np.array(ye_sorted),
            xe=np.array(xe_sorted)
        )

    def _refresh_plotting_system(self) -> None:
        """Refresh the plotting system when experiment selection changes."""
        try:
            if hasattr(self.parent(), '_plotting_1d'):
                plotting = self.parent()._plotting_1d
                print("📊 Refreshing plotting system...")
                print(f"   Current selection: {self._selected_experiment_indices}")
                
                # Emit signals to refresh experiment data and ranges
                print("   Emitting experimentDataChanged signal")
                plotting.experimentDataChanged.emit()
                print("   Emitting experimentChartRangesChanged signal")
                plotting.experimentChartRangesChanged.emit()
                print("   Calling refreshExperimentPage()")
                plotting.refreshExperimentPage()
                print("   Calling refreshExperimentRanges()")
                plotting.refreshExperimentRanges()
                print("✓ Plotting system refresh completed")
            else:
                print("⚠️  No plotting system found on parent")
        except Exception as e:
            print(f"❌ Error refreshing plotting system: {e}")

    ########################
    ## Minimizers
    @Property('QVariantList', notify=minimizerChanged)
    def minimizersAvailable(self) -> List[str]:
        return self._minimizers_logic.minimizers_available()

    @Property(int, notify=minimizerChanged)
    def minimizerCurrentIndex(self) -> int:
        return self._minimizers_logic.minimizer_current_index()

    @Slot(int)
    def setMinimizerCurrentIndex(self, new_value: int) -> None:
        if self._minimizers_logic.set_minimizer_current_index(new_value):
            self.minimizerChanged.emit()
            self.externalMinimizerChanged.emit()

    @Property('QVariant', notify=minimizerChanged)
    def minimizerTolerance(self) -> Optional[float]:
        return self._minimizers_logic.tolerance

    @Property('QVariant', notify=minimizerChanged)
    def minimizerMaxIterations(self) -> Optional[int]:
        return self._minimizers_logic.max_iterations

    @Slot(float)
    def setMinimizerTolerance(self, new_value: float) -> None:
        if self._minimizers_logic.set_tolerance(new_value):
            self.minimizerChanged.emit()

    @Slot(int)
    def setMinimizerMaxIterations(self, new_value: int) -> None:
        if self._minimizers_logic.set_max_iterations(new_value):
            self.minimizerChanged.emit()

    #############
    ## Parameters
    @Property('QVariantList', notify=parametersChanged)
    def fitableParameters(self) -> List[dict[str]]:
        if self._chached_parameters is None:
            self._chached_parameters = self._parameters_logic.parameters
        return self._chached_parameters

    @Property(int, notify=parametersIndexChanged)
    def currentParameterIndex(self) -> int:
        return self._parameters_logic.current_index()

    @Slot(int)
    def setCurrentParameterIndex(self, new_value: int) -> None:
        if self._parameters_logic.set_current_index(new_value):
            self.parametersIndexChanged.emit()

    @Property(int, notify=parametersChanged)
    def freeParametersCount(self) -> int:
        result = self._parameters_logic.count_free_parameters()
        return result

    @Property(int, notify=parametersChanged)
    def fixedParametersCount(self) -> int:
        result = self._parameters_logic.count_fixed_parameters()
        return result

    @Property(int, notify=parametersChanged)
    def modelParametersCount(self) -> int:
        return 3

    @Property(int, notify=parametersChanged)
    def experimentParametersCount(self) -> int:
        return 3

    @Slot(float)
    def setCurrentParameterValue(self, new_value: float) -> None:
        if self._parameters_logic.set_current_parameter_value(new_value):
            self._clearCacheAndEmitParametersChanged()
            self.externalParametersChanged.emit()

    @Slot(float)
    def setCurrentParameterMin(self, new_value: float) -> None:
        if self._parameters_logic.set_current_parameter_min(new_value):
            self._clearCacheAndEmitParametersChanged()

    @Slot(float)
    def setCurrentParameterMax(self, new_value: float) -> None:
        if self._parameters_logic.set_current_parameter_max(new_value):
            self._clearCacheAndEmitParametersChanged()

    @Slot(bool)
    def setCurrentParameterFit(self, new_value: bool) -> None:
        if self._parameters_logic.set_current_parameter_fit(new_value):
            self._clearCacheAndEmitParametersChanged()

    def _clearCacheAndEmitParametersChanged(self):
        self._chached_parameters = None
        self.parametersChanged.emit()
