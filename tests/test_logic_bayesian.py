# SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
# SPDX-License-Identifier: BSD-3-Clause
"""Exhaustive unit tests for the Bayesian state container (logic/bayesian.py)."""

import pytest

from EasyReflectometryApp.Backends.Py.logic.bayesian import Bayesian


class TestDefaults:
    """Default values from the DEFAULTS dict and constructor."""

    def test_default_samples(self):
        assert Bayesian().samples == 10000

    def test_default_burn(self):
        assert Bayesian().burn == 2000

    def test_default_population(self):
        assert Bayesian().population == 10

    def test_default_thin(self):
        assert Bayesian().thin == 1

    def test_default_posterior_none(self):
        assert Bayesian().posterior is None

    def test_default_has_result_false(self):
        assert Bayesian().has_result is False

    def test_default_rendered_assets_empty(self):
        b = Bayesian()
        assert b.corner_plot_url == ''
        assert b.trace_plot_url == ''
        assert b.heatmap_plot_url == ''
        assert b.heatmap_data is None
        assert b.diagnostics == {}


class TestSamples:
    """samples property — positive integer."""

    def test_get_set(self):
        b = Bayesian()
        b.samples = 5000
        assert b.samples == 5000

    def test_accepts_large_value(self):
        b = Bayesian()
        b.samples = 1_000_000
        assert b.samples == 1_000_000

    def test_accepts_minimum(self):
        b = Bayesian()
        b.samples = 1
        assert b.samples == 1

    @pytest.mark.parametrize('bad', [0, -1, -100])
    def test_rejects_non_positive(self, bad):
        b = Bayesian()
        with pytest.raises(ValueError, match='samples must be a positive integer'):
            b.samples = bad


class TestBurn:
    """burn property — non-negative integer."""

    def test_get_set(self):
        b = Bayesian()
        b.burn = 1000
        assert b.burn == 1000

    def test_accepts_zero(self):
        b = Bayesian()
        b.burn = 0
        assert b.burn == 0

    @pytest.mark.parametrize('bad', [-1, -100])
    def test_rejects_negative(self, bad):
        b = Bayesian()
        with pytest.raises(ValueError, match='burn must be a non-negative integer'):
            b.burn = bad


class TestPopulation:
    """population property — positive integer."""

    def test_get_set(self):
        b = Bayesian()
        b.population = 5
        assert b.population == 5

    def test_accepts_large(self):
        b = Bayesian()
        b.population = 50
        assert b.population == 50

    def test_accepts_minimum(self):
        b = Bayesian()
        b.population = 1
        assert b.population == 1

    @pytest.mark.parametrize('bad', [0, -1, -10])
    def test_rejects_non_positive(self, bad):
        b = Bayesian()
        with pytest.raises(ValueError, match='population must be a positive integer'):
            b.population = bad


class TestThin:
    """thin property — positive integer."""

    def test_get_set(self):
        b = Bayesian()
        b.thin = 5
        assert b.thin == 5

    def test_accepts_minimum(self):
        b = Bayesian()
        b.thin = 1
        assert b.thin == 1

    @pytest.mark.parametrize('bad', [0, -1, -5])
    def test_rejects_non_positive(self, bad):
        b = Bayesian()
        with pytest.raises(ValueError, match='thin must be a positive integer'):
            b.thin = bad


class TestPosterior:
    """posterior dict and has_result."""

    def test_set_posterior(self):
        b = Bayesian()
        posterior = {'draws': 'fake', 'param_names': ['a', 'b']}
        b._posterior = posterior
        assert b.posterior is posterior
        assert b.has_result is True

    def test_set_none(self):
        b = Bayesian()
        b._posterior = None
        assert b.posterior is None
        assert b.has_result is False

    def test_posterior_immutable_via_underscore(self):
        """The posterior property returns the internal reference."""
        b = Bayesian()
        data = {'draws': 'x'}
        b._posterior = data
        assert b.posterior is data


class TestClear:
    """clear() resets everything to post-construction state."""

    def test_clears_posterior(self):
        b = Bayesian()
        b._posterior = {'draws': 'x', 'param_names': ['a']}
        b.clear()
        assert b.posterior is None
        assert b.has_result is False

    def test_clears_rendered_assets(self):
        b = Bayesian()
        b.corner_plot_url = 'file:///corner.png'
        b.trace_plot_url = 'file:///trace.png'
        b.heatmap_plot_url = 'file:///heatmap.png'
        b.heatmap_data = {'x': [1, 2]}
        b.diagnostics = {'rhat': {'a': 1.0}}
        b.clear()
        assert b.corner_plot_url == ''
        assert b.trace_plot_url == ''
        assert b.heatmap_plot_url == ''
        assert b.heatmap_data is None
        assert b.diagnostics == {}

    def test_does_not_affect_hyperparams(self):
        b = Bayesian()
        b.samples = 5000
        b.burn = 1000
        b.population = 5
        b.thin = 2
        b.clear()
        assert b.samples == 5000
        assert b.burn == 1000
        assert b.population == 5
        assert b.thin == 2


class TestIdempotentSetters:
    """Setting the same value multiple times works."""

    def test_samples_idempotent(self):
        b = Bayesian()
        b.samples = 5000
        b.samples = 5000
        assert b.samples == 5000

    def test_burn_idempotent(self):
        b = Bayesian()
        b.burn = 500
        b.burn = 500
        assert b.burn == 500

    def test_population_idempotent(self):
        b = Bayesian()
        b.population = 7
        b.population = 7
        assert b.population == 7

    def test_thin_idempotent(self):
        b = Bayesian()
        b.thin = 3
        b.thin = 3
        assert b.thin == 3
