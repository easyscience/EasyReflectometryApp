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
from .logic.helpers import get_original_name
from .logic.minimizers import Minimizers as MinimizersLogic
from .logic.parameters import Parameters as ParametersLogic
from .workers import FitterWorker


class Analysis(QObject):
    minimizerChanged = Signal()
    calculatorChanged = Signal()
    experimentsChanged = Signal()
    parametersChanged = Signal()
    parametersIndexChanged = Signal()
    fittingChanged = Signal()
    fitFailed = Signal(str)  # Emitted with error message when fitting fails
    stopFit = Signal()  # Signal to request fitting stop

    externalMinimizerChanged = Signal()
    externalParametersChanged = Signal()
    externalCalculatorChanged = Signal()
    externalFittingChanged = Signal()
    externalExperimentChanged = Signal()

    def __init__(self, project_lib: ProjectLib, parent=None):
        super().__init__(parent)
        self._project_lib = project_lib
        self._parameters_logic = ParametersLogic(project_lib)
        self._fitting_logic = FittingLogic(project_lib)
        self._calculators_logic = CalculatorsLogic(project_lib)
        self._experiments_logic = ExperimentLogic(project_lib)
        self._minimizers_logic = MinimizersLogic(project_lib)
        self._chached_parameters = None
        self._chached_enabled_parameters = None
        # Thread management for background fitting
        self._fitter_thread = None
        # Connect stopFit signal to slot
        self.stopFit.connect(self._onStopFit)
        # Add support for multiple selected experiments - initialize to empty first to avoid binding loops
        self._selected_experiment_indices = []
        # Initialize selected experiments after construction to avoid binding loops
        self._initialize_selected_experiments()

    def _initialize_selected_experiments(self) -> None:
        """Initialize selected experiment indices after object construction to avoid binding loops."""
        available_experiments = self._experiments_logic.available()
        if len(available_experiments) > 0:
            self._selected_experiment_indices = [0]
        else:
            self._selected_experiment_indices = []

    def _ordered_experiments(self) -> list:
        """Return experiments as an ordered list of experiment objects.

        Handles mapping-like storage without assuming contiguous integer keys.
        """
        experiments = self._experiments_logic._project_lib._experiments
        if not experiments:
            return []

        if hasattr(experiments, 'items'):
            items = list(experiments.items())
            try:
                items.sort(key=lambda item: item[0])
            except TypeError:
                pass
            return [experiment for _, experiment in items]

        return list(experiments)

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

    @Property(bool, notify=fittingChanged)
    def showFitResultsDialog(self) -> bool:
        return self._fitting_logic.show_results_dialog

    @Slot(bool)
    def setShowFitResultsDialog(self, value: bool) -> None:
        self._fitting_logic.show_results_dialog = value
        self.fittingChanged.emit()

    @Property(bool, notify=fittingChanged)
    def fitSuccess(self) -> bool:
        return self._fitting_logic.fit_success

    @Property(str, notify=fittingChanged)
    def fitErrorMessage(self) -> str:
        return self._fitting_logic.fit_error_message

    @Property(int, notify=fittingChanged)
    def fitNumRefinedParams(self) -> int:
        return self._fitting_logic.fit_n_pars

    @Property(float, notify=fittingChanged)
    def fitChi2(self) -> float:
        return self._fitting_logic.fit_chi2

    @Property('QVariant', notify=fittingChanged)
    def fitResults(self) -> dict:
        """Return fit results as a dict for QML consumption."""
        return {
            'success': self._fitting_logic.fit_success,
            'nvarys': self._fitting_logic.fit_n_pars,
            'chi2': self._fitting_logic.fit_chi2,
        }

    @Slot(None)
    def fittingStartStop(self) -> None:
        # If already running, stop the fit
        if self._fitting_logic.running:
            self.stopFit.emit()
            return

        # Make sure we can run the fitting
        if not self.prefitCheck():
            return

        # Use threaded fitting for non-blocking UI
        self._start_threaded_fit()

    def _start_threaded_fit(self) -> None:
        """Start fitting in a background thread."""
        # Reset flags and prepare for fit using proper encapsulation
        self._fitting_logic.reset_stop_flag()
        self._fitting_logic.prepare_for_threaded_fit()
        self.fittingChanged.emit()

        # TODO: Thread-safety: prevent model/parameter edits during fitting or snapshot state before starting the worker.

        # Prepare fit data for all experiments
        fitter, x_data, y_data, weights, method = self._fitting_logic.prepare_threaded_fit(self._minimizers_logic)

        if fitter is None:
            # Error already set in fitting logic
            self.fittingChanged.emit()
            if self._fitting_logic.fit_error_message:
                self.fitFailed.emit(self._fitting_logic.fit_error_message)
            return

        # Create and configure worker
        self._fitter_thread = FitterWorker(
            fitter=fitter,
            method_name='fit',
            args=(x_data, y_data),
            kwargs={'weights': weights, 'method': method},
            parent=self,
        )
        self._fitter_thread.setTerminationEnabled(True)
        self._fitter_thread.finished.connect(self._on_fit_finished)
        self._fitter_thread.failed.connect(self._on_fit_failed)
        self._fitter_thread.finished.connect(self._fitter_thread.deleteLater)
        self._fitter_thread.failed.connect(self._fitter_thread.deleteLater)
        self._fitter_thread.start()

    @Slot(list)
    def _on_fit_finished(self, results: list) -> None:
        """Handle successful completion of threaded fit."""
        self._fitting_logic.on_fit_finished(results)
        self._fitter_thread = None
        self.fittingChanged.emit()
        self._clearCacheAndEmitParametersChanged()
        self.externalFittingChanged.emit()

    @Slot(str)
    def _on_fit_failed(self, error_message: str) -> None:
        """Handle failed threaded fit."""
        self._fitting_logic.on_fit_failed(error_message)
        self._fitter_thread = None
        self.fittingChanged.emit()
        self._clearCacheAndEmitParametersChanged()
        self.externalFittingChanged.emit()
        self.fitFailed.emit(error_message)

    @Slot()
    def _onStopFit(self) -> None:
        """Stop fitting and clean up."""
        self._fitting_logic.stop_fit()
        if self._fitter_thread is not None:
            self._fitter_thread.stop()
            self._fitter_thread.deleteLater()
            self._fitter_thread = None
        self.fittingChanged.emit()
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
                    'Invalid Parameter Bounds',
                    f"Parameter '{param['name']}' has invalid bounds: "
                    f'min ({param["min"]}) must be less than max ({param["max"]}).',
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
                    'Invalid Parameter Bounds',
                    f'Parameters {joined} have infinite bounds, which is not allowed for differential evolution minimizer.',
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
        self.externalExperimentChanged.emit()

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
        experiments = self._ordered_experiments()
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
        experiments = self._ordered_experiments()
        for experiment in experiments:
            name = get_original_name(experiment.model)
            mapped_models.append(name)
        return mapped_models

    @Property('QVariantList', notify=experimentsChanged)
    def modelColorsForExperiment(self) -> list:
        # return a list of model colors for each experiment
        mapped_models = []
        experiments = self._ordered_experiments()
        for experiment in experiments:
            mapped_models.append(experiment.model.color)
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
            print(f'Experiment index {index} is out of range.')

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
        # Validate indices
        available_count = len(self._experiments_logic.available())
        valid_indices = [i for i in indices if 0 <= i < available_count]

        if valid_indices != self._selected_experiment_indices:
            # previous_selection = self._selected_experiment_indices.copy()
            self._selected_experiment_indices = valid_indices
            # Update current experiment index to first selected (or 0 if no selection)
            if valid_indices:
                self._experiments_logic.set_current_index(valid_indices[0])
                self._project_lib.current_experiment_index = valid_indices[0]
            elif len(self._experiments_logic.available()) > 0:
                # If no selection but experiments available, default to first experiment
                self._experiments_logic.set_current_index(0)
                self._selected_experiment_indices = [0]  # Auto-select first experiment

            # Always trigger plotting refresh when selection changes
            self._refresh_plotting_system()

            self.experimentsChanged.emit()
            self.externalExperimentChanged.emit()

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
                print(f'Error accessing experiment {exp_idx}: {e}')
                continue

        if not all_x:
            return DataSet1D(name='No valid experiment data', x=np.empty(0), y=np.empty(0), ye=np.empty(0), xe=np.empty(0))

        # Sort by x values to maintain proper order
        combined_data = list(zip(all_x, all_y, all_ye, all_xe))
        combined_data.sort(key=lambda item: item[0])

        x_sorted, y_sorted, ye_sorted, xe_sorted = zip(*combined_data) if combined_data else ([], [], [], [])

        exp_names = [
            self._experiments_logic.available()[i]
            for i in self._selected_experiment_indices
            if i < len(self._experiments_logic.available())
        ]
        combined_name = f'Combined: {", ".join(exp_names)}'

        return DataSet1D(
            name=combined_name, x=np.array(x_sorted), y=np.array(y_sorted), ye=np.array(ye_sorted), xe=np.array(xe_sorted)
        )

    def get_individual_experiment_data_list(self):
        """
        Get individual experiment data for each selected experiment.
        Returns a list of dictionaries with data, name, and color for each experiment.
        """

        if not self._selected_experiment_indices:
            return []

        experiment_data_list = []

        # Define a color palette for experiments
        color_palette = [
            '#1f77b4',  # Blue
            '#ff7f0e',  # Orange
            '#2ca02c',  # Green
            '#d62728',  # Red
            '#9467bd',  # Purple
            '#8c564b',  # Brown
            '#e377c2',  # Pink
            '#7f7f7f',  # Gray
            '#bcbd22',  # Olive
            '#17becf',  # Cyan
        ]

        for idx, exp_idx in enumerate(self._selected_experiment_indices):
            try:
                data = self._experiments_logic._project_lib.experimental_data_for_model_at_index(exp_idx)
                if data.x.size > 0:  # Only include non-empty datasets
                    exp_name = (
                        self._experiments_logic.available()[exp_idx]
                        if exp_idx < len(self._experiments_logic.available())
                        else f'Experiment {exp_idx + 1}'
                    )
                    color = color_palette[idx % len(color_palette)]

                    experiment_data_list.append({'data': data, 'name': exp_name, 'color': color, 'index': exp_idx})
            except (IndexError, AttributeError) as e:
                print(f'Error accessing experiment {exp_idx}: {e}')
                continue

        return experiment_data_list

    @Property('QVariantList', notify=experimentsChanged)
    def selectedExperimentDataList(self) -> List[dict]:
        """Return individual experiment data for plotting separate lines."""
        return self.get_individual_experiment_data_list()

    def _refresh_plotting_system(self) -> None:
        """Refresh the plotting system when experiment selection changes."""
        # Emit signal to notify parent/listeners that experiment selection changed
        # Parent (PyBackend) connects this signal to plotting refresh
        self.experimentsChanged.emit()

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

    @Slot(str)
    def setMinimizerTolerance(self, new_value: str) -> None:
        try:
            value = float(new_value)
        except (ValueError, TypeError):
            return
        if self._minimizers_logic.set_tolerance(value):
            self.minimizerChanged.emit()

    @Slot(str)
    def setMinimizerMaxIterations(self, new_value: str) -> None:
        try:
            value = int(float(new_value))
        except (ValueError, TypeError):
            return
        if self._minimizers_logic.set_max_iterations(value):
            self.minimizerChanged.emit()

    #############
    ## Parameters
    @Property('QVariantList', notify=parametersChanged)
    def fitableParameters(self) -> List[dict[str]]:
        if self._chached_parameters is None:
            self._chached_parameters = self._parameters_logic.parameters
        return self._chached_parameters

    @Property('QVariantList', notify=parametersChanged)
    def enabledParameters(self) -> list[dict[str]]:
        if self._chached_enabled_parameters is not None:
            return self._chached_enabled_parameters
        enabled_parameters = []
        for parameter in self._parameters_logic.parameters:
            if not parameter['enabled']:
                continue
            enabled_parameters.append(parameter)
        self._chached_enabled_parameters = enabled_parameters
        return enabled_parameters

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
        self._chached_enabled_parameters = None
        self.parametersChanged.emit()
