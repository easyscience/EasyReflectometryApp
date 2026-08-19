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
        self._analysis.set_plotting(self._plotting_1d)

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

    @Property('QVariantList', notify=multiExperimentSelectionChanged)
    def plottingIndividualExperimentChannelDataList(self) -> list:
        """Multi-experiment data with polarized experiments split per visible spin channel."""
        return self._plotting_1d.individualExperimentChannelDataList

    @Slot(int, result='QVariantList')
    def plottingGetExperimentDataPoints(self, experiment_index: int) -> list:
        """Get data points for a specific experiment for plotting."""
        return self._plotting_1d.getExperimentDataPoints(experiment_index)

    @Slot(int, result='QVariantList')
    @Slot(int, str, result='QVariantList')
    def plottingGetAnalysisDataPoints(self, experiment_index: int, channel: str = '') -> list:
        """Get measured and calculated data points for a specific experiment for analysis plotting.

        `channel` picks one spin channel of a polarized experiment.
        """
        return self._plotting_1d.getAnalysisDataPoints(experiment_index, channel)

    @Slot(int, result='QVariantList')
    @Slot(int, str, result='QVariantList')
    def plottingGetResidualDataPoints(self, experiment_index: int, channel: str = '') -> list:
        """Get residual data points for a specific experiment for residual plotting."""
        return self._plotting_1d.getResidualDataPoints(experiment_index, channel)

    @Property(bool, notify=multiExperimentSelectionChanged)
    def plottingAnalysisUsesChannelSeries(self) -> bool:
        """Whether the analysis/residual charts must draw one series per spin channel."""
        return self._plotting_1d.analysisUsesChannelSeries

    # Polarized experiment support
    @Slot(int, str, result='QVariantList')
    def plottingGetExperimentChannelDataPoints(self, experiment_index: int, channel: str) -> list:
        """Get data points of one spin channel of a polarized experiment."""
        return self._plotting_1d.getExperimentChannelDataPoints(experiment_index, channel)

    @Slot(int, result='QVariantList')
    def plottingGetExperimentChannels(self, experiment_index: int) -> list:
        """Measured spin channels of an experiment ({channel, label, color, visible} rows)."""
        return self._plotting_1d.getExperimentChannels(experiment_index)

    @Slot(str, bool)
    def plottingSetChannelVisible(self, channel: str, visible: bool) -> None:
        """Show or hide one spin channel on the charts."""
        self._plotting_1d.setChannelVisible(channel, visible)

    ######### Magnetic depth profiles (SLD chart, both pages)
    @Slot(int, result=bool)
    def plottingModelHasMagnetism(self, model_index: int) -> bool:
        """Whether one model carries magnetism."""
        return self._plotting_1d.modelHasMagnetism(model_index)

    @Slot(int, str, result='QVariantList')
    def plottingGetMagneticSldDataPointsForModel(self, model_index: int, curve: str) -> list:
        """Points of one magnetic profile curve ('spin_up', 'spin_down', 'rho_m', 'theta_m')."""
        return self._plotting_1d.getMagneticSldDataPointsForModel(model_index, curve)

    @Slot(int, str, result='QVariantList')
    def plottingGetMagneticSldSegmentsForModel(self, model_index: int, curve: str) -> list:
        """The contiguous pieces of one magnetic profile curve."""
        return self._plotting_1d.getMagneticSldSegmentsForModel(model_index, curve)

    @Slot(int, str, int, result='QVariantList')
    def plottingGetMagneticSldSegment(self, model_index: int, curve: str, segment: int) -> list:
        """Points of one piece of a magnetic profile curve."""
        return self._plotting_1d.getMagneticSldSegment(model_index, curve, segment)

    @Slot(str, result=bool)
    def plottingSldCurveVisible(self, curve: str) -> bool:
        """Whether one magnetic profile curve is shown."""
        return self._plotting_1d.sldCurveVisible(curve)

    @Slot(str, bool)
    def plottingSetSldCurveVisible(self, curve: str, visible: bool) -> None:
        """Show or hide one magnetic profile curve on both SLD tabs."""
        self._plotting_1d.setSldCurveVisible(curve, visible)

    ######### Spin asymmetry
    @Slot(int, result='QVariantList')
    def plottingGetSpinAsymmetryPoints(self, experiment_index: int) -> list:
        """Measured spin-asymmetry points with error bounds."""
        return self._plotting_1d.getSpinAsymmetryPoints(experiment_index)

    @Slot(int, result='QVariantList')
    def plottingGetSpinAsymmetryCalculatedPoints(self, experiment_index: int) -> list:
        """Calculated spin-asymmetry points ([] without a magnetic model)."""
        return self._plotting_1d.getSpinAsymmetryCalculatedPoints(experiment_index)

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
        # Bayesian posteriors belong to one project state: discard them on
        # create/load/reset so stale results are never shown against new data.
        self._project.externalCreatedChanged.connect(self._analysis.clearBayesianResults)
        self._project.externalProjectLoaded.connect(self._analysis.clearBayesianResults)
        self._project.externalProjectReset.connect(self._analysis.clearBayesianResults)

    def _connect_sample_page(self) -> None:
        self._sample.externalSampleChanged.connect(self._relay_sample_page_sample_changed)
        # Enabling magnetism can switch the project's calculation engine; the
        # Analysis page's selector and every calculated curve must follow.
        self._sample.calculationEngineChanged.connect(self._analysis.calculatorChanged)
        self._sample.calculationEngineChanged.connect(self._analysis.externalCalculatorChanged)
        self._sample.externalRefreshPlot.connect(self._refresh_plots)
        self._sample.modelsTableChanged.connect(self._analysis._clearCacheAndEmitParametersChanged)
        self._sample.modelsTableChanged.connect(self._analysis.experimentsChanged)
        # Connect sample changes to multi-experiment selection signal
        self._sample.modelsTableChanged.connect(self.multiExperimentSelectionChanged)

    def _connect_experiment_page(self) -> None:
        self._experiment.externalExperimentChanged.connect(self._relay_experiment_page_experiment_changed)
        self._experiment.externalExperimentChanged.connect(self._refresh_plots)
        # Loading/removing an experiment can change whether the current one is
        # polarized and which channels it has.
        self._experiment.externalExperimentChanged.connect(self._plotting_1d.notifyExperimentChannelsChanged)
        # A freshly imported experiment becomes the current (and only selected)
        # one, so the charts show what was just loaded.
        self._experiment.experimentLoaded.connect(self._analysis.selectExperimentAtIndex)
        if hasattr(self._experiment, 'qRangeUpdated') and hasattr(self._sample, 'qRangeChanged'):
            self._experiment.qRangeUpdated.connect(self._sample.qRangeChanged)

    def _connect_analysis_page(self) -> None:
        self._analysis.externalMinimizerChanged.connect(self._relay_analysis_page)
        self._analysis.externalCalculatorChanged.connect(self._relay_analysis_page)
        self._analysis.externalParametersChanged.connect(self._relay_analysis_page)
        self._analysis.externalParametersChanged.connect(self._refresh_plots)
        self._analysis.externalFittingChanged.connect(self._refresh_plots)
        self._analysis.externalFittingChanged.connect(self._sample.magnetismChanged)

        # A finished fit updates the goodness-of-fit; refresh the Summary tab's
        # HTML binding so it stops showing the stale pre-fit value.
        self._analysis.externalFittingChanged.connect(self._summary.summaryChanged)
        self._analysis.externalExperimentChanged.connect(self._relay_experiment_page_experiment_changed)
        self._analysis.externalExperimentChanged.connect(self._refresh_plots)
        # Selecting another experiment changes the polarization state and the
        # channel list QML binds to, and with it whether spin asymmetry exists.
        self._analysis.experimentsChanged.connect(self._plotting_1d.notifyExperimentChannelsChanged)
        self._analysis.experimentsChanged.connect(self._plotting_1d.notifySpinAsymmetryChanged)
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
        # Notify summary that paths have changed (project path changed)
        self._summary.refreshPaths()
        self._sample.modelsIndexChanged.emit()
        self._sample.assembliesTableChanged.emit()
        self._sample.assembliesIndexChanged.emit()
        self._experiment.experimentChanged.emit()
        self._analysis.experimentsChanged.emit()
        self._status.statusChanged.emit()
        self._summary.summaryChanged.emit()
        # _refresh_plots drops the plot caches itself before recomputing.
        self._refresh_plots()

    def _relay_sample_page_sample_changed(self):
        # Non-plot consequences of a sample edit only. Every edit that changes
        # a curve also emits externalRefreshPlot (handled by _refresh_plots,
        # which invalidates and recomputes everything once); when this relay
        # also dropped the plot caches and re-notified the magnetic/spin
        # asymmetry charts, each edit computed every refl1d curve twice.
        self._analysis._clearCacheAndEmitParametersChanged()
        self._status.statusChanged.emit()
        self._summary.summaryChanged.emit()

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
        # Switching the calculator changes whether magnetism can be modelled at
        # all, which gates the Sample page's magnetism editor.
        self._sample.magnetismChanged.emit()

    def _refresh_plots(self):
        # The single invalidate-and-recompute pass: drop every plot cache
        # first, then notify each chart exactly once.
        self._plotting_1d.reset_data()
        # The magnetic profile and the spin asymmetry follow both the sample
        # (a layer became magnetic, a parameter moved) and the data, so they are
        # refreshed wherever the ordinary plots are.
        self._plotting_1d.notifyMagneticProfileChanged()
        self._plotting_1d.notifySpinAsymmetryChanged()
        self._plotting_1d.sampleChartRangesChanged.emit()
        self._plotting_1d.sldChartRangesChanged.emit()
        self._plotting_1d.experimentChartRangesChanged.emit()
        self._plotting_1d.refreshSamplePage()
        self._plotting_1d.refreshExperimentPage()
        self._plotting_1d.refreshAnalysisPage()
        self._plotting_1d.samplePageResetAxes.emit()
        # Emit signal for multi-experiment changes
        self.multiExperimentSelectionChanged.emit()
