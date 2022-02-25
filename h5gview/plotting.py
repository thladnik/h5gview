import uuid

import numpy as np
from PySide6 import QtCore, QtWidgets
import pyqtgraph as pg
from h5gview import core


def options(dataset: core.Dataset):
    if len(dataset.shape) == 1:
        return Plot1D,
    elif len(dataset.shape) == 2:
        return Plot1D, PlotImage,
    elif len(dataset.shape) > 2:
        return Plot1D, PlotImage, PlotImageSeries
    return ()


class Plot(QtWidgets.QWidget):
    instances = []

    def __init__(self, parent, dataset: core.Dataset):
        QtWidgets.QWidget.__init__(self, parent=parent, f=QtCore.Qt.WindowType.Window)
        self.id = str(uuid.uuid4())
        self.dataset = dataset
        self.instances.append(self)


class Plot1D(Plot):

    def __init__(self, parent, dataset: core.Dataset):
        Plot.__init__(self, parent, dataset)
        self.setLayout(QtWidgets.QHBoxLayout())

        # Add controls
        self.transpose = QtWidgets.QCheckBox('Transpose')
        self.transpose.setTristate(False)
        self.transpose.stateChanged.connect(self._update_plot)
        self.layout().addWidget(self.transpose)

        # Add plot widget
        self._plot_widget = pg.PlotWidget(background='white')
        self.layout().addWidget(self._plot_widget)

        geo = self.screen().geometry()

        # self.move(geo.width()-geo.width()//2, geo.height()//10)
        self.resize(geo.width()//3, geo.height()//3)

        self._plots = []

        self._update_plot()
        self.show()

    def _update_plot(self):

        data = np.squeeze(self.dataset.data)
        if self.transpose.checkState():
            data = data.T

        for p in self._plots:
            self._plot_widget.removeItem(p)

        self._plots = []

        if len(data.shape) == 1:
            p = self._plot_widget.plot(y=data)
            self._plots.append(p)
        else:
            drange = np.max(data) - np.min(data)
            for i, d in enumerate(data):
                p = self._plot_widget.plot(y=i * drange + d, pen=pg.mkPen('black'))
                self._plots.append(p)



class PlotImage(Plot):

    def __init__(self, parent, dataset: core.Dataset):
        Plot.__init__(self, parent, dataset)

        self.setLayout(QtWidgets.QHBoxLayout())
        self._image_view = pg.ImageView()
        self.layout().addWidget(self._image_view)

        geo = self.screen().geometry()

        self.move(geo.width()-geo.width()//2, geo.height()//10)
        self.resize(geo.width()//3, geo.height()//3)

        data = np.squeeze(dataset.data)

        self._image_view.setImage(data)

        self.show()


class PlotImageSeries(Plot):
    pass
