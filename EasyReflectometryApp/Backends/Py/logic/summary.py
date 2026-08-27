import logging
import pickle
from html import escape
from pathlib import Path

import numpy as np
from easyreflectometry import Project as ProjectLib
from easyreflectometry.summary import Summary as SummaryLib

from .experiments import CHANNEL_COLORS

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
        base_html = self._summary.compile_html_summary()
        return base_html
        # return self._inject_multimodel_multiexperiment_sections(base_html)

    def save_as_html(self, file_path: str | None = None) -> None:
        if not self._project_lib.path.exists():
            self._project_lib.path.mkdir(parents=True, exist_ok=True)

        target_path = Path(file_path) if file_path else self.file_path.with_suffix('.html')
        target_path.parent.mkdir(parents=True, exist_ok=True)
        html_content = self._summary.compile_html_summary(figures=True)
        # html_content = self._inject_multimodel_multiexperiment_sections(html_content)

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
    def _calculated_curve(model, x, channel=None):
        """Calculated reflectivity for one model, per spin channel when given.

        Returns None when the channel cannot be calculated (a spin-flip channel
        of a non-magnetic model, or a calculator without magnetism support): no
        overlay is better than the wrong one.
        """
        calculator = model.interface()
        if channel is None:
            return np.asarray(calculator.reflectity_profile(x, model.unique_name))
        try:
            return np.asarray(calculator.reflectivity_profile_channel(x, model.unique_name, channel))
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

        experiments = self._ordered_experiments()
        if experiments:
            for offset, (experiment_index, experiment) in enumerate(experiments):
                experiment_name = experiment.name or f'Experiment {experiment_index + 1}'
                channels = getattr(experiment, 'available_channels', None)
                if channels is None:
                    datasets = [(experiment_name, experiment, None)]
                else:
                    # Polarized experiment: one series per measured spin channel.
                    datasets = [
                        (f'{experiment_name} ({channel.value})', experiment[channel], channel) for channel in channels
                    ]
                for label_name, dataset, channel in datasets:
                    x = np.asarray(dataset.x)
                    y = np.asarray(dataset.y)
                    if x.size == 0 or y.size == 0:
                        continue

                    ye = np.asarray(dataset.ye) if getattr(dataset, 'ye', None) is not None else None
                    model = experiment.model
                    model.interface = self._project_lib._calculator
                    # Each channel needs its own spin cross-section; the
                    # channel-agnostic call would repeat one curve under four
                    # channel labels. None means "cannot be calculated" (e.g. a
                    # spin-flip channel of a non-magnetic model) — then the
                    # measured data is shown without a calculated overlay.
                    y_calc = self._calculated_curve(model, x, channel)
                    scale_factor = 10**offset

                    color = CHANNEL_COLORS[channel.value] if channel is not None else (
                        getattr(model, 'color', None) or '#1f77b4'
                    )
                    # Without a calculated curve the measured series carries the
                    # legend entry, so the channel is still identifiable.
                    measured_label = label_name if y_calc is None else None
                    if ye is not None and ye.size == y.size:
                        # ye holds variances (sigma**2); errorbar() needs one
                        # standard deviation, same convention as the fitter
                        # weights and the analysis-chart residuals.
                        sigma = np.sqrt(np.clip(ye, 0.0, None))
                        ax_reflectivity.errorbar(
                            x,
                            y * scale_factor,
                            sigma * scale_factor,
                            marker='',
                            ls='',
                            color=color,
                            alpha=0.45,
                        )
                        if measured_label is not None:
                            ax_reflectivity.plot(
                                x, y * scale_factor, ls='', marker='.', color=color, alpha=0.45, label=measured_label
                            )
                    else:
                        ax_reflectivity.plot(
                            x, y * scale_factor, ls='', marker='.', color=color, alpha=0.45, label=measured_label
                        )

                    if y_calc is not None:
                        ax_reflectivity.plot(
                            x, y_calc * scale_factor, ls='-', color=color, zorder=10, label=label_name
                        )
        else:
            for model_index, model in enumerate(self._project_lib.models):
                sample_data = self._project_lib.sample_data_for_model_at_index(model_index)
                if sample_data.x.size == 0 or sample_data.y.size == 0:
                    continue

                color = getattr(model, 'color', None) or '#1f77b4'
                ax_reflectivity.plot(
                    sample_data.x,
                    sample_data.y * (10**model_index),
                    ls='-',
                    color=color,
                    zorder=10,
                    label=model.name,
                )

        for model_index, model in enumerate(self._project_lib.models):
            sld_data = self._project_lib.sld_data_for_model_at_index(model_index)
            if sld_data.x.size == 0 or sld_data.y.size == 0:
                continue

            color = getattr(model, 'color', None) or '#1f77b4'
            ax_sld.plot(sld_data.x, sld_data.y + (10 * model_index), color=color, ls='-', label=model.name)

        if ax_reflectivity.has_data():
            ax_reflectivity.legend(loc='best')

        return fig

    def _ordered_experiments(self) -> list[tuple[int, object]]:
        experiments = self._project_lib.experiments
        if hasattr(experiments, 'items'):
            return sorted(experiments.items(), key=lambda item: item[0])
        return list(enumerate(experiments))

    def _inject_multimodel_multiexperiment_sections(self, html: str) -> str:
        extra_sections = [
            self._all_models_section_html(),
            self._all_experiments_section_html(),
        ]
        combined_sections = ''.join(section for section in extra_sections if section)
        if not combined_sections:
            return html

        if '</body>' in html:
            return html.replace('</body>', f'{combined_sections}</body>', 1)
        return f'{html}\n{combined_sections}'

    def _all_models_section_html(self) -> str:
        rows = []
        for model_index, model in enumerate(self._project_lib.models):
            assemblies = len(model.sample)
            layers = sum(len(assembly.layers) for assembly in model.sample)
            rows.append(
                (
                    f'<tr><td>{model_index}</td><td>{escape(model.name)}</td>'
                    f'<td>{assemblies}</td><td>{layers}</td></tr>'
                )
            )

        if not rows:
            return '<h3>All Samples</h3><p>No samples available.</p>'

        table_rows = ''.join(rows)
        return (
            '<h3>All Samples</h3>'
            '<table>'
            '<tr><th>Index</th><th>Name</th><th>Assemblies</th><th>Layers</th></tr>'
            f'{table_rows}'
            '</table>'
        )

    def _all_experiments_section_html(self) -> str:
        experiment_rows = []
        for experiment_index, experiment in self._ordered_experiments():
            x = np.asarray(experiment.x)
            q_min = float(np.min(x)) if x.size else float('nan')
            q_max = float(np.max(x)) if x.size else float('nan')
            model_name = getattr(getattr(experiment, 'model', None), 'name', 'N/A')
            name = experiment.name or f'Experiment {experiment_index + 1}'

            experiment_rows.append(
                (
                    f'<tr><td>{experiment_index}</td><td>{escape(name)}</td>'
                    f'<td>{escape(model_name)}</td><td>{len(x)}</td>'
                    f'<td>{q_min:.6g}</td><td>{q_max:.6g}</td></tr>'
                )
            )

        if not experiment_rows:
            return '<h3>All Experiments</h3><p>No experiments available.</p>'

        rows_str = ''.join(experiment_rows)
        return (
            '<h3>All Experiments</h3>'
            '<table>'
            '<tr><th>Index</th><th>Name</th><th>Model</th><th>Points</th><th>q min</th><th>q max</th></tr>'
            f'{rows_str}'
            '</table>'
        )
