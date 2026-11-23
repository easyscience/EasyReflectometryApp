import logging
import pickle
from html import escape
from pathlib import Path

import numpy as np
from easyreflectometry import Project as ProjectLib
from easyreflectometry.summary import Summary as SummaryLib

from .experiments import CHANNEL_COLORS
from .experiments import ordered_experiment_items

logger = logging.getLogger(__name__)


class Summary:
    # Written as a pickled matplotlib Figure instead of a rendered image.
    PICKLE_SUFFIXES = ('.pickle', '.pkl')

    def __init__(self, project_lib: ProjectLib):
        self._created = True

        self._project_lib = project_lib
        self._summary = SummaryLib(project_lib)
        self._file_name = 'summary'
        self._plot_file_name = 'plots'

    @property
    def created(self) -> bool:
        return self._created

    @property
    def file_name(self) -> str:
        return self._file_name

    @file_name.setter
    def file_name(self, value: str) -> None:
        self._file_name = value

    @property
    def file_path(self) -> Path:
        return self._project_lib.path / self._file_name

    @property
    def plot_file_name(self) -> str:
        return self._plot_file_name

    @plot_file_name.setter
    def plot_file_name(self, value: str) -> None:
        self._plot_file_name = value

    @property
    def plot_file_path(self) -> Path:
        return self._project_lib.path / self._plot_file_name

    @property
    def as_html(self) -> str:
        return self._inject_models_section(self._summary.compile_html_summary())

    def save_as_html(self, file_path: str | None = None) -> None:
        if not self._project_lib.path.exists():
            self._project_lib.path.mkdir(parents=True, exist_ok=True)

        target_path = Path(file_path) if file_path else self.file_path.with_suffix('.html')
        target_path.parent.mkdir(parents=True, exist_ok=True)
        html_content = self._inject_models_section(self._summary.compile_html_summary(figures=True))

        with open(target_path, 'w', encoding='utf-8') as report_file:
            report_file.write(html_content)

    def save_as_pdf(self, file_path: str | None = None) -> None:
        if not self._project_lib.path.exists():
            self._project_lib.path.mkdir(parents=True, exist_ok=True)

        target_path = Path(file_path) if file_path else self.file_path.with_suffix('.pdf')
        target_path.parent.mkdir(parents=True, exist_ok=True)
        self._summary.save_pdf_summary(target_path)

    def save_plot(self, file_path: str, width_cm: float, height_cm: float) -> None:
        target_path = Path(file_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        figure = self.make_plot(width_cm, height_cm)
        try:
            if target_path.suffix.lower() in self.PICKLE_SUFFIXES:
                self._dump_figure(figure, target_path)
            else:
                figure.savefig(target_path, dpi=600)
        finally:
            self._plt().close(figure)

    @staticmethod
    def _dump_figure(figure, target_path: Path) -> None:
        """Write the live matplotlib Figure itself, not a rendered image.

        Reload it in any Python session to keep working with the plot::

            import pickle
            import matplotlib.pyplot as plt

            figure = pickle.load(open('plots.pickle', 'rb'))
            plt.show()

        The axes, artists and data survive the round trip, so the chart can be
        restyled, re-scaled or combined with other data afterwards - none of
        which a PNG, SVG or PDF export allows. The figure is dumped before it
        is closed so that matplotlib records it as pyplot-managed and hands it
        back to pyplot on load.
        """
        with open(target_path, 'wb') as handle:
            pickle.dump(figure, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def show_plot(self, width_cm: float, height_cm: float) -> None:
        self.make_plot(width_cm, height_cm)
        self._plt().show()

    def _plt(self):
        # Prevent noisy matplotlib debug logs like "findfont: score(...)" in app console.
        logging.getLogger('matplotlib').setLevel(logging.WARNING)
        logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
        import matplotlib.pyplot as plt

        return plt

    def _gridspec(self):
        import matplotlib.gridspec as gridspec

        return gridspec

    @staticmethod
    def _calculated_curve(model, x, channel=None, resolution_function=None):
        """Calculated reflectivity for one model, per spin channel when given.

        `resolution_function` is the dataset's own (``None``: the model's), so
        the report shows the curve the fit compared that dataset to.

        Returns None when the channel cannot be calculated (a spin-flip channel
        of a non-magnetic model, or a calculator without magnetism support): no
        overlay is better than the wrong one.
        """
        calculator = model.interface()
        if channel is None:
            # `reflectity_profile` (sic) is the calculator's own method name.
            return np.asarray(
                calculator.reflectity_profile(x, model.unique_name, resolution_function=resolution_function)
            )
        try:
            return np.asarray(
                calculator.reflectivity_profile_channel(
                    x, model.unique_name, channel, resolution_function=resolution_function
                )
            )
        except (ValueError, NotImplementedError, AttributeError) as exception:
            logger.warning('No calculated curve for channel %s: %s', channel.value, exception)
            return None

    def make_plot(self, width_cm: float, height_cm: float):
        plt = self._plt()
        gridspec = self._gridspec()

        fig = plt.figure(figsize=(width_cm / 2.54, height_cm / 2.54), constrained_layout=True)
        gs = gridspec.GridSpec(1, 2, figure=fig)
        ax_reflectivity = fig.add_subplot(gs[0, 0])
        ax_sld = fig.add_subplot(gs[0, 1])

        ax_reflectivity.set_xlabel('$q$/A$^{-1}$')
        ax_reflectivity.set_ylabel('$R(q)$')
        ax_reflectivity.set_yscale('log')
        ax_sld.set_xlabel('$z$/A')
        ax_sld.set_ylabel('SLD($z$)/$10^{-6}$A$^{-2}$')

        experiments = ordered_experiment_items(self._project_lib)
        if experiments:
            self._plot_experiments(ax_reflectivity, experiments)
        else:
            self._plot_sample_curves(ax_reflectivity)
        self._plot_sld_profiles(ax_sld)

        if ax_reflectivity.has_data():
            ax_reflectivity.legend(loc='best')

        return fig

    def _plot_experiments(self, ax, experiments) -> None:
        """Measured data with its calculated curve, each experiment a decade above the last."""
        for offset, (experiment_index, experiment) in enumerate(experiments):
            for label_name, dataset, channel in self._experiment_datasets(experiment_index, experiment):
                self._plot_dataset(ax, experiment.model, label_name, dataset, channel, 10**offset)

    @staticmethod
    def _experiment_datasets(experiment_index: int, experiment) -> list:
        """``(label, dataset, channel)`` of each series an experiment plots; channel None when unpolarized."""
        experiment_name = experiment.name or f'Experiment {experiment_index + 1}'
        channels = getattr(experiment, 'available_channels', None)
        if channels is None:
            return [(experiment_name, experiment, None)]
        # Polarized experiment: one series per measured spin channel.
        return [(f'{experiment_name} ({channel.value})', experiment[channel], channel) for channel in channels]

    def _plot_dataset(self, ax, model, label_name: str, dataset, channel, scale_factor: float) -> None:
        x = np.asarray(dataset.x)
        y = np.asarray(dataset.y)
        if x.size == 0 or y.size == 0:
            return

        model.interface = self._project_lib._calculator
        # Each channel needs its own spin cross-section; the
        # channel-agnostic call would repeat one curve under four
        # channel labels. None means "cannot be calculated" (e.g. a
        # spin-flip channel of a non-magnetic model) — then the
        # measured data is shown without a calculated overlay.
        y_calc = self._calculated_curve(model, x, channel, resolution_function=getattr(dataset, 'resolution_function', None))
        color = CHANNEL_COLORS[channel.value] if channel is not None else _model_color(model)
        # Without a calculated curve the measured series carries the
        # legend entry, so the channel is still identifiable.
        measured_label = label_name if y_calc is None else None
        _plot_measured(ax, x, y * scale_factor, _sigma(dataset, y.size), scale_factor, color, measured_label)

        if y_calc is not None:
            ax.plot(x, y_calc * scale_factor, ls='-', color=color, zorder=10, label=label_name)

    def _plot_sample_curves(self, ax) -> None:
        """Without experiments, each model's calculated reflectivity, a decade above the last."""
        for model_index, model, sample_data in self._nonempty_model_data(self._project_lib.sample_data_for_model_at_index):
            ax.plot(
                sample_data.x,
                sample_data.y * (10**model_index),
                ls='-',
                color=_model_color(model),
                zorder=10,
                label=model.name,
            )

    def _plot_sld_profiles(self, ax) -> None:
        for model_index, model, sld_data in self._nonempty_model_data(self._project_lib.sld_data_for_model_at_index):
            ax.plot(sld_data.x, sld_data.y + (10 * model_index), color=_model_color(model), ls='-', label=model.name)

    def _nonempty_model_data(self, data_at_index):
        """Yield ``(index, model, data)`` for each model whose ``data_at_index(index)`` has points."""
        for model_index, model in enumerate(self._project_lib.models):
            data = data_at_index(model_index)
            if data.x.size and data.y.size:
                yield model_index, model, data

    def _inject_models_section(self, html: str) -> str:
        """Add the table of models when there are several (contrasts); the library's
        summary already lists every experiment and every model's parameters."""
        if len(self._project_lib.models) < 2:
            return html
        section = self._all_models_section_html()
        if '</body>' in html:
            return html.replace('</body>', f'{section}</body>', 1)
        return f'{html}\n{section}'

    def _all_models_section_html(self) -> str:
        models = self._project_lib.models
        rows = []
        for model_index, model in enumerate(models):
            assemblies = len(model.sample)
            layers = sum(len(assembly.layers) for assembly in model.sample)
            reference = self._project_lib.contrast_reference(model_index)
            derived_from = escape(models[reference].name) if reference is not None else ''
            rows.append(
                (
                    f'<tr><td>{model_index}</td><td>{escape(model.name)}</td>'
                    f'<td>{assemblies}</td><td>{layers}</td><td>{derived_from}</td></tr>'
                )
            )

        if not rows:
            return '<h3>All Samples</h3><p>No samples available.</p>'

        table_rows = ''.join(rows)
        return (
            '<h3>All Samples</h3>'
            '<table>'
            '<tr><th>Index</th><th>Name</th><th>Assemblies</th><th>Layers</th><th>Contrast of</th></tr>'
            f'{table_rows}'
            '</table>'
        )


_DEFAULT_COLOR = '#1f77b4'


def _model_color(model) -> str:
    return getattr(model, 'color', None) or _DEFAULT_COLOR


def _sigma(dataset, size: int):
    """One standard deviation per point, or None when the dataset has no usable errors.

    ye holds variances (sigma**2); errorbar() needs one standard deviation, same
    convention as the fitter weights and the analysis-chart residuals.
    """
    if getattr(dataset, 'ye', None) is None:
        return None
    ye = np.asarray(dataset.ye)
    if ye.size != size:
        return None
    return np.sqrt(np.clip(ye, 0.0, None))


def _plot_measured(ax, x, y_scaled, sigma, scale_factor: float, color: str, label: str | None) -> None:
    """The measured points: error bars when there are errors, markers when there are none or a label to carry."""
    if sigma is not None:
        ax.errorbar(x, y_scaled, sigma * scale_factor, marker='', ls='', color=color, alpha=0.45)
        if label is None:
            return
    ax.plot(x, y_scaled, ls='', marker='.', color=color, alpha=0.45, label=label)
