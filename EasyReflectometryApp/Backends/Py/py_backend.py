from EasyApp.Logic.Logging import LoggerLevelHandler
from easyreflectometry import Project as ProjectLib
from PySide6.QtCore import Property
from PySide6.QtCore import QObject

from .analysis import Analysis
from .experiment import Experiment
from .home import Home
from .plotting_1d import Plotting1d
from .project import Project
from .sample import Sample
from .status import Status
from .summary import Summary


class PyBackend(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._project_lib = ProjectLib()
        self._project_lib.default_model()

        # Page and Status bar backend parts
        self._home = Home()
        self._project = Project(self._project_lib)
        self._sample = Sample(self._project_lib)
        self._experiment = Experiment(self._project_lib)
        self._analysis = Analysis(self._project_lib)
        self._summary = Summary(self._project_lib)
        self._status = Status(self._project_lib)

        # Plotting backend part
        self._plotting = Plotting1d(self._project_lib)

        self._logger = LoggerLevelHandler(self)

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
        return self._plotting

    @Property('QVariant', constant=True)
    def logger(self):
        return self._logger

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
        self._sample.modelsTableChanged.connect(self._analysis.parametersChanged)

    def _connect_experiment_page(self) -> None:
        self._experiment.externalExperimentChanged.connect(self._relay_experiment_page_experiment_changed)
        self._experiment.externalExperimentChanged.connect(self._refresh_plots)

    def _connect_analysis_page(self) -> None:
        self._analysis.externalMinimizerChanged.connect(self._relay_analysis_page)
        self._analysis.externalCalculatorChanged.connect(self._relay_analysis_page)
        self._analysis.externalParametersChanged.connect(self._relay_analysis_page)
        self._analysis.externalParametersChanged.connect(self._refresh_plots)
        self._analysis.externalFittingChanged.connect(self._refresh_plots)
        self._analysis.externalExperimentChanged.connect(self._relay_experiment_page_experiment_changed)
        self._analysis.externalExperimentChanged.connect(self._refresh_plots)

    def _relay_project_page_name(self):
        self._status.statusChanged.emit()

    #        self._summary.asHtmlChanged.emit()

    def _relay_project_page_created(self):
        self._summary.createdChanged.emit()
        self._summary.summaryChanged.emit()

    def _relay_project_page_project_changed(self):
        self._sample.materialsTableChanged.emit()
        self._sample.modelsTableChanged.emit()
        self._sample.assembliesTableChanged.emit()
        self._sample._clearCacheAndEmitLayersChanged()
        self._experiment.experimentChanged.emit()
        self._analysis.experimentsChanged.emit()
        self._analysis._clearCacheAndEmitParametersChanged()
        self._status.statusChanged.emit()
        self._summary.summaryChanged.emit()
        self._refresh_plots()

    def _relay_sample_page_sample_changed(self):
        self._analysis._clearCacheAndEmitParametersChanged()
        self._status.statusChanged.emit()
        self._summary.summaryChanged.emit()

    def _relay_experiment_page_experiment_changed(self):
        self._analysis.experimentsChanged.emit()
        self._analysis._clearCacheAndEmitParametersChanged()
        self._status.statusChanged.emit()
        self._summary.summaryChanged.emit()

    def _relay_analysis_page(self):
        self._status.statusChanged.emit()
        self._experiment.experimentChanged.emit()
        self._summary.summaryChanged.emit()

    def _refresh_plots(self):
        self._plotting.sampleChartRangesChanged.emit()
        self._plotting.sldChartRangesChanged.emit()
        self._plotting.experimentChartRangesChanged.emit()
        self._plotting.refreshSamplePage()
        self._plotting.refreshExperimentPage()
        self._plotting.refreshAnalysisPage()
