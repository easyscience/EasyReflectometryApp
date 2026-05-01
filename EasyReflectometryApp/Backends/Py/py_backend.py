from EasyApplication.Logic.Logging import LoggerLevelHandler
from EasyApplication.Logic.Logging import console
from easyreflectometry import Project as ProjectLib
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from .analysis import Analysis
from .experiment import Experiment
from .home import Home
from .plotting_1d import Plotting1d
from .project import Project
from .sample import Sample
from .status import Status
from .summary import Summary


class PyBackend(QObject):
    # Signal for multi-experiment selection changes
    multiExperimentSelectionChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._project_lib = ProjectLib()

        # Page and Status bar backend parts
        self._home = Home()
        self._project = Project(self._project_lib)
        self._sample = Sample(self._project_lib)
        self._experiment = Experiment(self._project_lib)
        self._analysis = Analysis(self._project_lib, parent=self)
        self._summary = Summary(self._project_lib)
        self._status = Status(self._project_lib)

        # Plotting backend part
        self._plotting_1d = Plotting1d(self._project_lib, parent=self)

        self._logger = LoggerLevelHandler(self)

        # Wire cross-cutting references before connecting signals
        self._status._status_logic.set_minimizers_logic(self._analysis._minimizers_logic)

        # Must be last to ensure all backend parts are created
        self._connect_backend_parts()

    # Enable dot access in QML code to the page specific backend parts
    # Pages
    @Property('QVariant', constant=True)
    def home(self) -> Home:
        return self._home

    @Property('QVariant', constant=True)
    def project(self) -> Project:
        return self._project

    @Property('QVariant', constant=True)
    def sample(self) -> Project:
        return self._sample

    @Property('QVariant', constant=True)
    def experiment(self) -> Experiment:
        return self._experiment

    @Property('QVariant', constant=True)
    def analysis(self) -> Analysis:
        return self._analysis

    @Property('QVariant', constant=True)
    def summary(self) -> Summary:
        return self._summary

    # Other elements
    @Property('QVariant', constant=True)
    def status(self) -> Status:
        return self._status

    @Property('QVariant', constant=True)
    def plotting(self) -> Plotting1d:
        return self._plotting_1d

    @Property('QVariant', constant=True)
    def logger(self):
        return self._logger

    # Analysis properties and methods for multi-experiment selection
    @Property(int, notify=multiExperimentSelectionChanged)
    def analysisExperimentsSelectedCount(self) -> int:
        """Return the count of currently selected experiments."""
        return self._analysis.experimentsSelectedCount

    @Property('QVariantList', notify=multiExperimentSelectionChanged)
    def analysisSelectedExperimentIndices(self) -> list:
        """Return the list of selected experiment indices."""
        return self._analysis.selectedExperimentIndices

    @Slot('QVariantList')
    def analysisSetSelectedExperimentIndices(self, indices) -> None:
        """Set multiple selected experiment indices."""
        console.debug(f'PyBackend.analysisSetSelectedExperimentIndices called with: {indices}')
        console.debug(f'Type of indices: {type(indices)}')

        # Convert QVariantList to Python list if needed
        python_indices = list(indices) if hasattr(indices, '__iter__') else []
        console.debug(f'Converted to Python list: {python_indices}')

        if hasattr(self._analysis, 'setSelectedExperimentIndices'):
            self._analysis.setSelectedExperimentIndices(python_indices)
            console.debug('Successfully called analysis.setSelectedExperimentIndices')
        else:
            console.debug('ERROR: analysis.setSelectedExperimentIndices method not found')

        # Emit our local signal to notify QML properties
        self.multiExperimentSelectionChanged.emit()

    # Plotting properties for multi-experiment support
    @Property(bool, notify=multiExperimentSelectionChanged)
    def plottingIsMultiExperimentMode(self) -> bool:
        """Return whether multiple experiments are selected for plotting."""
        return self._plotting_1d.isMultiExperimentMode

    @Property('QVariantList', notify=multiExperimentSelectionChanged)
    def plottingIndividualExperimentDataList(self) -> list:
        """Return list of individual experiment data for multi-experiment plotting."""
        return self._plotting_1d.individualExperimentDataList

    @Slot(int, result='QVariantList')
    def plottingGetExperimentDataPoints(self, experiment_index: int) -> list:
        """Get data points for a specific experiment for plotting."""
        return self._plotting_1d.getExperimentDataPoints(experiment_index)

    @Slot(int, result='QVariantList')
    def plottingGetAnalysisDataPoints(self, experiment_index: int) -> list:
        """Get measured and calculated data points for a specific experiment for analysis plotting."""
        return self._plotting_1d.getAnalysisDataPoints(experiment_index)

    @Slot(int, result='QVariantList')
    def plottingGetResidualDataPoints(self, experiment_index: int) -> list:
        """Get residual data points for a specific experiment for residual plotting."""
        return self._plotting_1d.getResidualDataPoints(experiment_index)

    ######### Connections to relay info between the backend parts
    def _connect_backend_parts(self) -> None:
        self._connect_project_page()
        self._connect_sample_page()
        self._connect_experiment_page()
        self._connect_analysis_page()

    ######### Forming connections between the backend parts
    def _connect_project_page(self) -> None:
        self._project.externalNameChanged.connect(self._relay_project_page_name)
        self._project.externalCreatedChanged.connect(self._relay_project_page_created)
        self._project.externalProjectLoaded.connect(self._relay_project_page_project_changed)
        self._project.externalProjectReset.connect(self._relay_project_page_project_changed)

    def _connect_sample_page(self) -> None:
        self._sample.externalSampleChanged.connect(self._relay_sample_page_sample_changed)
        self._sample.externalRefreshPlot.connect(self._refresh_plots)
        self._sample.modelsTableChanged.connect(self._analysis._clearCacheAndEmitParametersChanged)
        self._sample.modelsTableChanged.connect(self._analysis.experimentsChanged)
        # Connect sample changes to multi-experiment selection signal
        self._sample.modelsTableChanged.connect(self.multiExperimentSelectionChanged)

    def _connect_experiment_page(self) -> None:
        self._experiment.externalExperimentChanged.connect(self._relay_experiment_page_experiment_changed)
        self._experiment.externalExperimentChanged.connect(self._refresh_plots)
        if hasattr(self._experiment, 'qRangeUpdated') and hasattr(self._sample, 'qRangeChanged'):
            self._experiment.qRangeUpdated.connect(self._sample.qRangeChanged)

    def _connect_analysis_page(self) -> None:
        self._analysis.externalMinimizerChanged.connect(self._relay_analysis_page)
        self._analysis.externalCalculatorChanged.connect(self._relay_analysis_page)
        self._analysis.externalParametersChanged.connect(self._relay_analysis_page)
        self._analysis.externalParametersChanged.connect(self._refresh_plots)
        self._analysis.externalFittingChanged.connect(self._refresh_plots)
        self._analysis.externalExperimentChanged.connect(self._relay_experiment_page_experiment_changed)
        self._analysis.externalExperimentChanged.connect(self._refresh_plots)
        # Update status bar when parameters change (e.g. fit checkbox toggle, post-fit)
        self._analysis.parametersChanged.connect(self._status.statusChanged)
        # Connect multi-experiment selection changes
        self._analysis.experimentsChanged.connect(self.multiExperimentSelectionChanged)

    def _relay_project_page_name(self):
        self._status.statusChanged.emit()

    #        self._summary.asHtmlChanged.emit()

    def _relay_project_page_created(self):
        self._summary.createdChanged.emit()
        self._summary.summaryChanged.emit()

    def _relay_project_page_project_changed(self):
        # Clear layers cache first so that subsequent signal handlers
        # (e.g. ComboBox onModelChanged / onCurrentAssemblyNameChanged in
        # MultiLayer.qml) read up-to-date layer data.
        self._sample._clearCacheAndEmitLayersChanged()
        self._sample.materialsTableChanged.emit()
        self._sample.modelsTableChanged.emit()
        self._sample.modelsIndexChanged.emit()
        self._sample.assembliesTableChanged.emit()
        self._sample.assembliesIndexChanged.emit()
        self._experiment.experimentChanged.emit()
        self._analysis.experimentsChanged.emit()
        self._status.statusChanged.emit()
        self._summary.summaryChanged.emit()
        self._plotting_1d.reset_data()
        self._refresh_plots()

    def _relay_sample_page_sample_changed(self):
        self._plotting_1d.reset_data()
        self._analysis._clearCacheAndEmitParametersChanged()
        self._status.statusChanged.emit()
        self._summary.summaryChanged.emit()
        self._plotting_1d.samplePageResetAxes.emit()

    def _relay_experiment_page_experiment_changed(self):
        self._analysis.experimentsChanged.emit()
        self._analysis._clearCacheAndEmitParametersChanged()
        self._status.statusChanged.emit()
        self._summary.summaryChanged.emit()

    def _relay_analysis_page(self):
        self._plotting_1d.reset_data()
        self._status.statusChanged.emit()
        self._experiment.experimentChanged.emit()
        self._summary.summaryChanged.emit()
        self._plotting_1d.samplePageResetAxes.emit()

    def _refresh_plots(self):
        self._plotting_1d.sampleChartRangesChanged.emit()
        self._plotting_1d.sldChartRangesChanged.emit()
        self._plotting_1d.experimentChartRangesChanged.emit()
        self._plotting_1d.refreshSamplePage()
        self._plotting_1d.refreshExperimentPage()
        self._plotting_1d.refreshAnalysisPage()
        self._plotting_1d.samplePageResetAxes.emit()
        # Emit signal for multi-experiment changes
        self.multiExperimentSelectionChanged.emit()
