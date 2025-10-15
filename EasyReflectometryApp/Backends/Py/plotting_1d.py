import numpy as np
from EasyApp.Logic.Logging import console
from easyreflectometry import Project as ProjectLib
from easyreflectometry.data import DataSet1D
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from .helpers import IO

PLOT_BACKEND = 'QtCharts'


class Plotting1d(QObject):
    chartRefsChanged = Signal()
    sldChartRangesChanged = Signal()
    sampleChartRangesChanged = Signal()
    experimentChartRangesChanged = Signal()
    experimentDataChanged = Signal()

    def __init__(self, project_lib: ProjectLib, parent=None):
        super().__init__(parent)
        self._project_lib = project_lib
        self._proxy = parent
        self._currentLib1d = 'QtCharts'
        self._sample_data = {}
        self._sld_data = {}
        self._chartRefs = {
            'QtCharts': {
                'samplePage': {
                    'sampleSerie': None,
                    'sldSerie': None,
                },
                'experimentPage': {
                    'measuredSerie': None,
                    'errorUpperSerie': None,
                    'errorLowerSerie': None,
                },
                'analysisPage': {
                    'calculatedSerie': None,
                    'measuredSerie': None,
                },
            }
        }

    def reset_data(self):
        self._sample_data = {}
        self._sld_data = {}
        console.debug(IO.formatMsg('sub', 'Sample and SLD data cleared'))

    @property
    def sample_data(self) -> DataSet1D:
        idx = self._project_lib.current_model_index
        if idx in self._sample_data and self._sample_data[idx] is not None:
            return self._sample_data[idx]
        try:
            data = self._project_lib.sample_data_for_model_at_index(idx)
        except IndexError:
            data = DataSet1D(
                name='Sample Data empty',
                x=np.empty(0),
                y=np.empty(0),
            )
        self._sample_data[idx] = data
        return data

    @property
    def sld_data(self) -> DataSet1D:
        idx = self._project_lib.current_model_index
        if idx in self._sld_data and self._sld_data[idx] is not None:
            return self._sld_data[idx]
        try:
            data = self._project_lib.sld_data_for_model_at_index(idx)
        except IndexError:
            data = DataSet1D(
                name='SLD Data empty',
                x=np.empty(0),
                y=np.empty(0),
            )
        self._sld_data[idx] = data
        return data

    @property
    def experiment_data(self) -> DataSet1D:
        try:
            # Check if multi-experiment selection is enabled
            if hasattr(self._proxy, '_analysis') and hasattr(self._proxy._analysis, '_selected_experiment_indices'):
                selected_indices = self._proxy._analysis._selected_experiment_indices
                print(f"🔍 experiment_data property accessed, selected_indices: {selected_indices}")
                if len(selected_indices) > 1:
                    # Return concatenated data for multiple experiments
                    print("   → Returning concatenated data for multiple experiments")
                    return self._proxy._analysis.get_concatenated_experiment_data()
                else:
                    print(f"   → Single experiment. Index: "
                          f"{selected_indices[0] if selected_indices else 'current'}")

            # Default single experiment behavior
            current_index = self._project_lib.current_experiment_index
            print(f"   → Loading single experiment data for index: {current_index}")
            data = self._project_lib.experimental_data_for_model_at_index(current_index)
            print(f"   → Single experiment data loaded: {data.name}, {len(data.x)} points")
        except IndexError as e:
            print(f"   → IndexError in experiment_data: {e}")
            data = DataSet1D(
                name='Experiment Data empty',
                x=np.empty(0),
                y=np.empty(0),
                ye=np.empty(0),
                xe=np.empty(0),
            )
        return data

    # Sample
    @Property(float, notify=sampleChartRangesChanged)
    def sampleMaxX(self):
        return self.sample_data.x.max()

    @Property(float, notify=sampleChartRangesChanged)
    def sampleMinX(self):
        return self.sample_data.x.min()

    @Property(float, notify=sampleChartRangesChanged)
    def sampleMaxY(self):
        return np.log10(self.sample_data.y.max())

    @Property(float, notify=sampleChartRangesChanged)
    def sampleMinY(self):
        return np.log10(self.sample_data.y.min())

    # SLD
    @Property(float, notify=sldChartRangesChanged)
    def sldMaxX(self):
        return self.sld_data.x.max()

    @Property(float, notify=sldChartRangesChanged)
    def sldMinX(self):
        return self.sld_data.x.min()

    @Property(float, notify=sldChartRangesChanged)
    def sldMaxY(self):
        return self.sld_data.y.max()

    @Property(float, notify=sldChartRangesChanged)
    def sldMinY(self):
        return self.sld_data.y.min()

    # Experiment ranges
    @Property(float, notify=experimentChartRangesChanged)
    def experimentMaxX(self):
        data = self.experiment_data
        return data.x.max() if data.x.size > 0 else 1.0

    @Property(float, notify=experimentChartRangesChanged)
    def experimentMinX(self):
        data = self.experiment_data
        return data.x.min() if data.x.size > 0 else 0.0

    @Property(float, notify=experimentChartRangesChanged)
    def experimentMaxY(self):
        data = self.experiment_data
        return np.log10(data.y.max()) if data.y.size > 0 else 1.0

    @Property(float, notify=experimentChartRangesChanged)
    def experimentMinY(self):
        data = self.experiment_data
        valid_y = data.y[data.y > 0] if data.y.size > 0 else np.array([1e-10])
        return np.log10(valid_y.min()) if valid_y.size > 0 else -10.0

    @Property('QVariant', notify=chartRefsChanged)
    def chartRefs(self):
        return self._chartRefs

    @Property(str)
    def calcSerieColor(self):
        return '#00FF00'
        #return self._calcSerieColor

    @Slot(str, str, 'QVariant')
    def setQtChartsSerieRef(self, page: str, serie: str, ref: QObject):
        self._chartRefs['QtCharts'][page][serie] = ref
        console.debug(IO.formatMsg('sub', f'{serie} on {page}: {ref}'))

    def refreshSamplePage(self):
        self.drawCalculatedOnSampleChart()
        self.drawCalculatedOnSldChart()

    def refreshExperimentPage(self):
        self.drawMeasuredOnExperimentChart()

    def refreshAnalysisPage(self):
        self.drawCalculatedAndMeasuredOnAnalysisChart()

    def refreshExperimentRanges(self):
        """Emit signal to update experiment chart ranges when selection changes."""
        self.experimentChartRangesChanged.emit()

    @Slot()
    def drawCalculatedOnSampleChart(self):
        if PLOT_BACKEND == 'QtCharts':
            self.qtchartsReplaceCalculatedOnSampleChartAndRedraw()

    def qtchartsReplaceCalculatedOnSampleChartAndRedraw(self):
        series = self._chartRefs['QtCharts']['samplePage']['sampleSerie']
        series.clear()
        nr_points = 0
        for point in self.sample_data.data_points():
            series.append(point[0], np.log10(point[1]))
            nr_points = nr_points + 1
        console.debug(IO.formatMsg('sub', 'Calc curve', f'{nr_points} points', 'on sample page', 'replaced'))

    @Slot()
    def drawCalculatedOnSldChart(self):
        if PLOT_BACKEND == 'QtCharts':
            self.qtchartsReplaceCalculatedOnSldChartAndRedraw()

    def qtchartsReplaceCalculatedOnSldChartAndRedraw(self):
        series = self._chartRefs['QtCharts']['samplePage']['sldSerie']
        series.clear()
        nr_points = 0
        for point in self.sld_data.data_points():
            series.append(point[0], point[1])
            nr_points = nr_points + 1
        console.debug(IO.formatMsg('sub', 'Sld curve', f'{nr_points} points', 'on sample page', 'replaced'))

    def drawMeasuredOnExperimentChart(self):
        if PLOT_BACKEND == 'QtCharts':
            self.qtchartsReplaceMeasuredOnExperimentChartAndRedraw()

    def qtchartsReplaceMeasuredOnExperimentChartAndRedraw(self):
        series_measured = self._chartRefs['QtCharts']['experimentPage']['measuredSerie']
        series_measured.clear()
        series_error_upper = self._chartRefs['QtCharts']['experimentPage']['errorUpperSerie']
        series_error_upper.clear()
        series_error_lower = self._chartRefs['QtCharts']['experimentPage']['errorLowerSerie']
        series_error_lower.clear()
        nr_points = 0
        for point in self.experiment_data.data_points():
            if point[0] < self._project_lib.q_max and self._project_lib.q_min < point[0]:
                series_measured.append(point[0], np.log10(point[1]))
                series_error_upper.append(point[0], np.log10(point[1] + np.sqrt(point[2])))
                series_error_lower.append(point[0], np.log10(point[1] - np.sqrt(point[2])))
                nr_points = nr_points + 1

        console.debug(IO.formatMsg('sub', 'Measurede curve', f'{nr_points} points', 'on experiment page', 'replaced'))

    def drawCalculatedAndMeasuredOnAnalysisChart(self):
        if PLOT_BACKEND == 'QtCharts':
            self.qtchartsReplaceCalculatedAndMeasuredOnAnalysisChartAndRedraw()

    def qtchartsReplaceCalculatedAndMeasuredOnAnalysisChartAndRedraw(self):
        series_measured = self._chartRefs['QtCharts']['analysisPage']['measuredSerie']
        series_measured.clear()
        series_calculated = self._chartRefs['QtCharts']['analysisPage']['calculatedSerie']
        series_calculated.clear()
        nr_points = 0
        for point in self.experiment_data.data_points():
            if point[0] < self._project_lib.q_max and self._project_lib.q_min < point[0]:
                series_measured.append(point[0], np.log10(point[1]))
                nr_points = nr_points + 1
        console.debug(IO.formatMsg('sub', 'Measurede curve', f'{nr_points} points', 'on analysis page', 'replaced'))

        for point in self.sample_data.data_points():
            series_calculated.append(point[0], np.log10(point[1]))
            nr_points = nr_points + 1
        console.debug(IO.formatMsg('sub', 'Calculated curve', f'{nr_points} points', 'on analysis page', 'replaced'))
