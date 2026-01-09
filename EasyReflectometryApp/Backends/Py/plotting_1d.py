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
    samplePageDataChanged = Signal()  # Signal for QML to refresh sample page charts

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
                    'sldSerie': None,
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
                if len(selected_indices) > 1:
                    # Return concatenated data for multiple experiments (legacy support)
                    return self._proxy._analysis.get_concatenated_experiment_data()
            # Default single experiment behavior
            current_index = self._project_lib.current_experiment_index
            data = self._project_lib.experimental_data_for_model_at_index(current_index)
        except IndexError:
            data = DataSet1D(
                name='Experiment Data empty',
                x=np.empty(0),
                y=np.empty(0),
                ye=np.empty(0),
                xe=np.empty(0),
            )
        return data

    @property
    def is_multi_experiment_mode(self) -> bool:
        """Check if multiple experiments are selected."""
        try:
            if hasattr(self._proxy, '_analysis') and hasattr(self._proxy._analysis, '_selected_experiment_indices'):
                return len(self._proxy._analysis._selected_experiment_indices) > 1
        except Exception:
            pass
        return False

    @property
    def individual_experiment_data_list(self) -> list:
        """Get individual experiment data for multi-experiment plotting."""
        try:
            if hasattr(self._proxy, '_analysis'):
                return self._proxy._analysis.get_individual_experiment_data_list()
        except Exception as e:
            console.debug(f"Error getting individual experiment data: {e}")
        return []

    # Sample
    @Property(float, notify=sampleChartRangesChanged)
    def sampleMaxX(self):
        return self._get_all_models_sample_range()[1]

    @Property(float, notify=sampleChartRangesChanged)
    def sampleMinX(self):
        return self._get_all_models_sample_range()[0]

    @Property(float, notify=sampleChartRangesChanged)
    def sampleMaxY(self):
        return self._get_all_models_sample_range()[3]

    @Property(float, notify=sampleChartRangesChanged)
    def sampleMinY(self):
        return self._get_all_models_sample_range()[2]

    def _get_all_models_sample_range(self):
        """Get combined X/Y ranges for all models' sample data."""
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')

        for idx in range(len(self._project_lib.models)):
            try:
                data = self._project_lib.sample_data_for_model_at_index(idx)
                if data.x.size > 0:
                    min_x = min(min_x, data.x.min())
                    max_x = max(max_x, data.x.max())
                if data.y.size > 0:
                    valid_y = data.y[data.y > 0]
                    if valid_y.size > 0:
                        min_y = min(min_y, np.log10(valid_y.min()))
                        max_y = max(max_y, np.log10(valid_y.max()))
            except (IndexError, ValueError):
                continue

        # Fallback to current model if no valid data found
        if min_x == float('inf'):
            min_x = self.sample_data.x.min() if self.sample_data.x.size > 0 else 0.0
        if max_x == float('-inf'):
            max_x = self.sample_data.x.max() if self.sample_data.x.size > 0 else 1.0
        if min_y == float('inf'):
            min_y = np.log10(self.sample_data.y.min()) if self.sample_data.y.size > 0 else -10.0
        if max_y == float('-inf'):
            max_y = np.log10(self.sample_data.y.max()) if self.sample_data.y.size > 0 else 0.0

        return (min_x, max_x, min_y, max_y)

    # SLD
    @Property(float, notify=sldChartRangesChanged)
    def sldMaxX(self):
        return self._get_all_models_sld_range()[1]

    @Property(float, notify=sldChartRangesChanged)
    def sldMinX(self):
        return self._get_all_models_sld_range()[0]

    @Property(float, notify=sldChartRangesChanged)
    def sldMaxY(self):
        return self._get_all_models_sld_range()[3]

    @Property(float, notify=sldChartRangesChanged)
    def sldMinY(self):
        return self._get_all_models_sld_range()[2]

    def _get_all_models_sld_range(self):
        """Get combined X/Y ranges for all models' SLD data."""
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')

        for idx in range(len(self._project_lib.models)):
            try:
                data = self._project_lib.sld_data_for_model_at_index(idx)
                if data.x.size > 0:
                    min_x = min(min_x, data.x.min())
                    max_x = max(max_x, data.x.max())
                if data.y.size > 0:
                    min_y = min(min_y, data.y.min())
                    max_y = max(max_y, data.y.max())
            except (IndexError, ValueError):
                continue

        # Fallback to current model if no valid data found
        if min_x == float('inf'):
            min_x = self.sld_data.x.min() if self.sld_data.x.size > 0 else 0.0
        if max_x == float('-inf'):
            max_x = self.sld_data.x.max() if self.sld_data.x.size > 0 else 1.0
        if min_y == float('inf'):
            min_y = self.sld_data.y.min() if self.sld_data.y.size > 0 else -1.0
        if max_y == float('-inf'):
            max_y = self.sld_data.y.max() if self.sld_data.y.size > 0 else 1.0

        return (min_x, max_x, min_y, max_y)

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

    @Property(bool, notify=experimentDataChanged)
    def isMultiExperimentMode(self) -> bool:
        """Return whether multiple experiments are selected for plotting."""
        return self.is_multi_experiment_mode

    @Property('QVariantList', notify=experimentDataChanged)
    def individualExperimentDataList(self) -> list:
        """Return list of individual experiment data for multi-experiment plotting."""
        data_list = self.individual_experiment_data_list
        # Convert to QML-friendly format
        qml_data_list = []
        for exp_data in data_list:
            qml_data_list.append({
                'name': exp_data['name'],
                'color': exp_data['color'],
                'index': exp_data['index'],
                'hasData': exp_data['data'].x.size > 0
            })
        return qml_data_list

    @Slot(str, str, 'QVariant')
    def setQtChartsSerieRef(self, page: str, serie: str, ref: QObject):
        self._chartRefs['QtCharts'][page][serie] = ref
        console.debug(IO.formatMsg('sub', f'{serie} on {page}: {ref}'))

    @Slot(int, result='QVariantList')
    def getSampleDataPointsForModel(self, model_index: int) -> list:
        """Get sample data points for a specific model for plotting."""
        try:
            data = self._project_lib.sample_data_for_model_at_index(model_index)
            points = []
            for point in data.data_points():
                points.append({
                    'x': float(point[0]),
                    'y': float(np.log10(point[1])) if point[1] > 0 else -10.0
                })
            return points
        except Exception as e:
            console.debug(f'Error getting sample data points for model {model_index}: {e}')
            return []

    @Slot(int, result='QVariantList')
    def getSldDataPointsForModel(self, model_index: int) -> list:
        """Get SLD data points for a specific model for plotting."""
        try:
            data = self._project_lib.sld_data_for_model_at_index(model_index)
            points = []
            for point in data.data_points():
                points.append({
                    'x': float(point[0]),
                    'y': float(point[1])
                })
            return points
        except Exception as e:
            console.debug(f'Error getting SLD data points for model {model_index}: {e}')
            return []

    @Slot(int, result=str)
    def getModelColor(self, model_index: int) -> str:
        """Get the color for a specific model."""
        try:
            return str(self._project_lib.models[model_index].color)
        except (IndexError, AttributeError):
            return '#000000'

    @Property(int, notify=sampleChartRangesChanged)
    def modelCount(self) -> int:
        """Return the number of models."""
        return len(self._project_lib.models)

    @Slot(int, result='QVariantList')
    def getExperimentDataPoints(self, experiment_index: int) -> list:
        """Get data points for a specific experiment for plotting."""
        try:
            data = self._project_lib.experimental_data_for_model_at_index(experiment_index)
            points = []
            for point in data.data_points():
                if point[0] < self._project_lib.q_max and self._project_lib.q_min < point[0]:
                    points.append({
                        'x': float(point[0]),
                        'y': float(np.log10(point[1])),
                        'errorUpper': float(np.log10(point[1] + np.sqrt(point[2]))),
                        'errorLower': float(np.log10(max(point[1] - np.sqrt(point[2]), 1e-10)))  # Avoid log(0)
                    })
            return points
        except Exception as e:
            console.debug(f"Error getting experiment data points for index {experiment_index}: {e}")
            return []

    @Slot(int, result='QVariantList')
    def getAnalysisDataPoints(self, experiment_index: int) -> list:
        """Get measured and calculated data points for a specific experiment for analysis plotting."""
        try:
            # Get measured experimental data
            exp_data = self._project_lib.experimental_data_for_model_at_index(experiment_index)

            # Get the model index for this experiment - it may be different from experiment_index
            # When multiple experiments share the same model
            model_index = 0
            if hasattr(exp_data, 'model') and exp_data.model is not None:
                # Find the model index in the models collection
                for idx, model in enumerate(self._project_lib.models):
                    if model is exp_data.model:
                        model_index = idx
                        break
            else:
                # Fallback: use experiment_index if it's within model range, else 0
                model_index = experiment_index if experiment_index < len(self._project_lib.models) else 0

            # Get the q values from the experimental data for calculating the model
            q_values = exp_data.x
            # Filter to q range
            mask = (q_values >= self._project_lib.q_min) & (q_values <= self._project_lib.q_max)
            q_filtered = q_values[mask]

            # Get calculated model data at the same q points using the correct model index
            calc_data = self._project_lib.sample_data_for_model_at_index(model_index, q_filtered)

            points = []
            exp_points = list(exp_data.data_points())
            calc_y = calc_data.y

            calc_idx = 0
            for point in exp_points:
                if point[0] < self._project_lib.q_max and self._project_lib.q_min < point[0]:
                    calc_y_val = calc_y[calc_idx] if calc_idx < len(calc_y) else point[1]
                    points.append({
                        'x': float(point[0]),
                        'measured': float(np.log10(point[1])),
                        'calculated': float(np.log10(calc_y_val)),
                    })
                    calc_idx += 1
            return points
        except Exception as e:
            console.debug(f"Error getting analysis data points for index {experiment_index}: {e}")
            return []

    def refreshSamplePage(self):
        # Clear cached data so it gets recalculated
        self._sample_data = {}
        self._sld_data = {}
        # Emit signals to update ranges and trigger QML refresh
        self.sampleChartRangesChanged.emit()
        self.sldChartRangesChanged.emit()
        self.samplePageDataChanged.emit()

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
        # Draw on sample page
        series = self._chartRefs['QtCharts']['samplePage']['sldSerie']
        if series is not None:
            series.clear()
            nr_points = 0
            for point in self.sld_data.data_points():
                series.append(point[0], point[1])
                nr_points = nr_points + 1
            console.debug(IO.formatMsg('sub', 'Sld curve', f'{nr_points} points', 'on sample page', 'replaced'))

        # Draw on analysis page
        analysis_series = self._chartRefs['QtCharts']['analysisPage']['sldSerie']
        if analysis_series is not None:
            analysis_series.clear()
            nr_points = 0
            for point in self.sld_data.data_points():
                analysis_series.append(point[0], point[1])
                nr_points = nr_points + 1
            console.debug(IO.formatMsg('sub', 'Sld curve', f'{nr_points} points', 'on analysis page', 'replaced'))

    def drawMeasuredOnExperimentChart(self):
        if PLOT_BACKEND == 'QtCharts':
            if self.is_multi_experiment_mode:
                self.qtchartsReplaceMultiExperimentChartAndRedraw()
            else:
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

        console.debug(IO.formatMsg('sub', 'Measured curve', f'{nr_points} points', 'on experiment page', 'replaced'))

    def qtchartsReplaceMultiExperimentChartAndRedraw(self):
        """Draw multiple experiment series with distinct colors."""
        console.debug(IO.formatMsg('sub', 'Multi-experiment mode', 'drawing separate lines'))

        # Clear default series but don't use them for multi-experiment mode
        if 'measuredSerie' in self._chartRefs['QtCharts']['experimentPage']:
            self._chartRefs['QtCharts']['experimentPage']['measuredSerie'].clear()
        if 'errorUpperSerie' in self._chartRefs['QtCharts']['experimentPage']:
            self._chartRefs['QtCharts']['experimentPage']['errorUpperSerie'].clear()
        if 'errorLowerSerie' in self._chartRefs['QtCharts']['experimentPage']:
            self._chartRefs['QtCharts']['experimentPage']['errorLowerSerie'].clear()

        # Individual experiment series are managed by QML
        # This method is called to trigger the refresh, actual drawing is handled by QML
        self.experimentDataChanged.emit()

    def drawCalculatedAndMeasuredOnAnalysisChart(self):
        if PLOT_BACKEND == 'QtCharts':
            if self.is_multi_experiment_mode:
                self.qtchartsReplaceMultiExperimentAnalysisChartAndRedraw()
            else:
                self.qtchartsReplaceCalculatedAndMeasuredOnAnalysisChartAndRedraw()

    def qtchartsReplaceMultiExperimentAnalysisChartAndRedraw(self):
        """Clear default series and let QML handle multi-experiment drawing on analysis page."""
        console.debug(IO.formatMsg('sub', 'Multi-experiment mode', 'drawing separate lines on analysis page'))

        # Clear default series but don't use them for multi-experiment mode
        if 'measuredSerie' in self._chartRefs['QtCharts']['analysisPage']:
            self._chartRefs['QtCharts']['analysisPage']['measuredSerie'].clear()
        if 'calculatedSerie' in self._chartRefs['QtCharts']['analysisPage']:
            self._chartRefs['QtCharts']['analysisPage']['calculatedSerie'].clear()

        # Individual experiment series are managed by QML
        # This method is called to trigger the refresh, actual drawing is handled by QML
        self.experimentDataChanged.emit()

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
