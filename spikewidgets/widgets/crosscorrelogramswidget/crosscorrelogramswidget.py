import numpy as np
from matplotlib import pyplot as plt
from spikewidgets.widgets.basewidget import BaseMultiWidget
from .correlograms_phy import compute_correlograms


def plot_autocorrelograms(sorting, sample_rate=None, unit_ids=None, bin_size=2, window=50, figure=None, ax=None):
    if sample_rate is None:
        if sorting.get_sampling_frequency() is None:
            raise Exception("Sampling rate information is not in the SortingExtractor. "
                            "Provide the 'sample_rate' argument")
        else:
            sample_rate = sorting.get_sampling_frequency()
    W = AutoCorrelogramsWidget(
        sorting=sorting,
        samplerate=sample_rate,
        unit_ids=unit_ids,
        binsize=bin_size,
        window=window,
        figure=figure,
        ax=ax
    )
    W.plot()
    return W


def plot_crosscorrelograms(sorting, sample_rate=None, unit_ids=None, bin_size=1, window=10, figure=None, ax=None):
    if sample_rate is None:
        if sorting.get_sampling_frequency() is None:
            raise Exception("Sampling rate information is not in the SortingExtractor. "
                            "Provide the 'sample_rate' argument")
        else:
            sample_rate = sorting.get_sampling_frequency()
    W = CrossCorrelogramsWidget(
        sorting=sorting,
        samplerate=sample_rate,
        unit_ids=unit_ids,
        binsize=bin_size,
        window=window,
        figure=figure,
        ax=ax
    )
    W.plot()
    return W


class AutoCorrelogramsWidget(BaseMultiWidget):
    def __init__(self, *, sorting, samplerate, unit_ids=None, binsize=2, window=50, figure=None, ax=None):
        BaseMultiWidget.__init__(self, figure, ax)
        self._sorting = sorting
        self._unit_ids = unit_ids
        self._samplerate = samplerate
        self._binsize = binsize
        self._window = window

    def plot(self):
        self._do_plot()

    def _do_plot(self):
        units = self._unit_ids
        if units is None:
            units = self._sorting.get_unit_ids()
        list_corr = []

        spike_times, spike_clusters = _prepare_spike_times_and_clusters(self._sorting, units, self._samplerate)
        ccg = compute_correlograms(spike_times, spike_clusters, cluster_ids=units, sample_rate=self._samplerate,
                                   bin_size=self._binsize, window_size=self._window, symmetrize=True)

        for i_u, unit in enumerate(units):
            bin_counts = ccg[i_u, i_u]
            bins = np.linspace(- self._window / 2, self._window / 2, len(bin_counts))
            wid = self._binsize
            item = dict(
                title=str(unit),
                bin_counts=bin_counts,
                bins=bins,
                wid=wid
            )
            list_corr.append(item)

        with plt.rc_context({'axes.edgecolor': 'gray'}):
            self._plot_autocorrelograms_multi(list_corr)

    def _plot_autocorrelograms_multi(self, list_corr, *, ncols=5, **kwargs):
        if len(list_corr) < ncols:
            ncols = len(list_corr)
        nrows = np.ceil(len(list_corr) / ncols)
        for i, item in enumerate(list_corr):
            ax = self.get_tiled_ax(i, nrows, ncols)
            _plot_correlogram(**item, **kwargs, ax=ax, color='gray')
            

class CrossCorrelogramsWidget(BaseMultiWidget):
    def __init__(self, *, sorting, samplerate, unit_ids=None, binsize=2, window=50, figure=None, ax=None):
        BaseMultiWidget.__init__(self, figure, ax)
        self._sorting = sorting
        self._unit_ids = unit_ids
        self._samplerate = samplerate
        self._binsize = binsize
        self._window = window

    def plot(self):
        self._do_plot()

    def _do_plot(self):
        units = self._unit_ids
        if units is None:
            units = self._sorting.get_unit_ids()
        list_corr = []

        spike_times, spike_clusters = _prepare_spike_times_and_clusters(self._sorting, units, self._samplerate)
        ccg = compute_correlograms(spike_times, spike_clusters, cluster_ids=units, sample_rate=self._samplerate,
                                   bin_size=self._binsize, window_size=self._window, symmetrize=True)

        for u1, unit1 in enumerate(units):
            for u2, unit2 in enumerate(units):
                bin_counts = ccg[u1, u2]
                bins = np.linspace(- self._window / 2, self._window / 2, len(bin_counts))
                wid = self._binsize
                item = dict(
                    title=str(unit1) + '-' + str(unit2),
                    bin_counts=bin_counts,
                    bins=bins,
                    wid=wid
                )
                list_corr.append(item)
        with plt.rc_context({'axes.edgecolor': 'gray'}):
            self._plot_crosscorrelograms_multi(list_corr)

    def _plot_crosscorrelograms_multi(self, list_corr, **kwargs):
        units = self._unit_ids
        if units is None:
            units = self._sorting.get_unit_ids()
        ncols = len(units)
        nrows = np.ceil(len(list_corr) / ncols)
        self.figure.set_size_inches((3*ncols, 2*nrows))
        for i, item in enumerate(list_corr):
            ax, diag = self.get_tiled_ax(i, nrows, ncols, hspace=1.5, wspace=0.2, is_diag=True)
            if diag:
                _plot_correlogram(**item, **kwargs, ax=ax, color='blue')
            else:
                _plot_correlogram(**item, **kwargs, ax=ax, color='gray')


def _plot_correlogram(*, ax, bin_counts, bins, wid, title='', color=None):
    ax.bar(x=bins, height=bin_counts, width=wid, color=color, align='edge')
    ax.set_xlabel('dt (s)')
    ax.set_xticks([bins[0], bins[len(bins)//2], bins[-1]])
    ax.set_yticks([])
    if title:
        ax.set_title(title, color='gray')


def _prepare_spike_times_and_clusters(sorting, unit_ids, samplerate):
    spike_times = np.array([])
    spike_clusters = np.array([], dtype=int)

    for u in sorting.get_unit_ids():
        if u in unit_ids:
            spike_times = np.concatenate((spike_times, sorting.get_unit_spike_train(u) / samplerate))
            spike_clusters = np.concatenate((spike_clusters, np.array([u]*len(sorting.get_unit_spike_train(u)))))

    order = np.argsort(spike_times)
    spike_times = spike_times[order]
    spike_clusters = spike_clusters[order]

    return spike_times, spike_clusters
