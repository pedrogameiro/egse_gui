#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import os
import sys
from pathlib import Path
from typing import List

from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy

from .daemon import DaemonABC

dir_path = os.path.dirname(os.path.realpath(__file__))

uifile_1 = dir_path + '/ui/egse_tm.ui'
form_tm, base_tm = uic.loadUiType(uifile_1)

uifile_2 = dir_path + '/ui/egse_conf.ui'
form_conf, base_conf = uic.loadUiType(uifile_2)

#uifile_3 = dir_path + '/ui/egse_log.ui'
#form_log, base_log = uic.loadUiType(uifile_3)


class EgseConf(base_conf, form_conf):
    def __init__(self, egsetm):
        super(base_conf, self).__init__()
        self.setupUi(self)
        self.egsetm = egsetm

        confpath = os.environ.get('XDG_CONFIG_HOME',
                                  os.environ['HOME'] + '/.config')
        confpath += '/istsat/egseconfig.json'
        self.lastconfigfile = confpath

        self.OKButton.clicked.connect(self.doOk)
        self.LoadFileButton.clicked.connect(self.loadfilebutton)
        self.SaveFileButton.clicked.connect(self.saveconfigbutton)
        self.LogFileButton.clicked.connect(self.selectLogFile)
        self.TCFileButton.clicked.connect(self.selectTcFile)
        self.TMFileButton.clicked.connect(self.selectTmFile)
        self.DefaultsButton.clicked.connect(self.doDefaults)

        if Path(self.lastconfigfile).is_file():
            self.loadconfigfile(self.lastconfigfile)
        else:
            self.doDefaults()

        self.OKButton.setFocus(True)

    def doOk(self):
        self.saveconfigfile(self.lastconfigfile)
        self.close()
        self.egsetm.show()

    def loadfilebutton(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Config', QtCore.QDir.currentPath(), 'JSON Files (*.json)')
        self.loadconfigfile(fileName)

    def saveconfigbutton(self):
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Config', QtCore.QDir.currentPath(), 'JSON Files (*.json)')
        self.loadconfigfile(fileName)

    def selectLogFile(self):
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Log File', QtCore.QDir.currentPath(), '*')
        self.LogFileText.setText(fileName)

    def selectTcFile(self):
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'TC File', QtCore.QDir.currentPath(), '*')
        self.TCFileText.setText(fileName)

    def selectTmFile(self):
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'TM File', QtCore.QDir.currentPath(), '*')
        self.TMFileText.setText(fileName)

    def doDefaults(self):
        self.I1Text.setText(''),
        self.I2Text.setText(''),
        self.TdelayText.setText(''),
        self.FSampleText.setText(''),
        self.LogFileText.setText('egse.log'),
        self.TCFileText.setText('egse_tc.log'),
        self.TMFileText.setText('egse_tm.log')

    def loadconfigfile(self, fileName):

        with open(fileName) as json_file:
            data = json.load(json_file)
            for p in data['config']:
                self.I1Text.setText(p['i1t']),
                self.I2Text.setText(p['i2t']),
                self.TdelayText.setText(p['tdelay']),
                self.FSampleText.setText(p['fsample']),
                self.LogFileText.setText(p['logfile']),
                self.TCFileText.setText(p['tcfile']),
                self.TMFileText.setText(p['tmfile'])

    def saveconfigfile(self, fileName: str):

        data = {}
        data['config'] = []
        data['config'].append({
            'i1t': self.I1Text.toPlainText(),
            'i2t': self.I2Text.toPlainText(),
            'tdelay': self.TdelayText.toPlainText(),
            'fsample': self.FSampleText.toPlainText(),
            'logfile': self.LogFileText.toPlainText(),
            'tcfile': self.TCFileText.toPlainText(),
            'tmfile': self.TMFileText.toPlainText()
        })

        p = Path(fileName)
        if not p.parent.exists():
            p.parent.mkdir(parents=True)

        with p.open('w') as outfile:
            json.dump(data, outfile)


class EgseTm(base_tm, form_tm):
    def __init__(self, daemon: DaemonABC):
        super(base_tm, self).__init__()
        self.setupUi(self)

        alert_palette = QtGui.QPalette()
        normal_palette = QtGui.QPalette()
        alert_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.red)
        normal_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.black)

        self.plots = []

        self.tms = [{
            'label': getattr(self, 'TMLabel_{}'.format(i)),
            'radio': getattr(self, 'TMRadio_{}'.format(i)),
            'inst': getattr(self, 'TMInst_{}'.format(i)),
            'avg': getattr(self, 'TMAvg_{}'.format(i)),
            'max': getattr(self, 'TMMax_{}'.format(i)),
        } for i in range(1, 13)]

        self.alarms = [{
            'label': getattr(self, 'AlarmLabel_{}'.format(i)),
            'min': getattr(self, 'AlarmMin_{}'.format(i)),
            'max': getattr(self, 'AlarmMax_{}'.format(i)),
        } for i in range(1, 13)]

        self.TMPlotButton.clicked.connect(self.TMPlotButtonHook)
        self.TMClearButton.clicked.connect(self.TMClearButtonHook)
        self.TCSendButton.clicked.connect(self.TCSendButtonHook)
        self.TCCustomSendButton.clicked.connect(self.TCCustomSendButtonHook)
        self.AlarmDefaultsButton.clicked.connect(self.AlarmDefaultsButtonHook)

        self.AlarmDefaultsButtonHook()

        self.daemon = daemon

    def TMPlotButtonHook(self):
        self.plots.append(PlotApp(self))

    def TMClearButtonHook(self):
        for t in self.tms:
            t['radio'].setChecked(False)

    def TCCustomSendButtonHook(self):
        fullcmd = self.TCCustomCmd.toPlainText()

        self.TCCustomRet.setText("TODO")

        print("TODO")
        print(fullcmd)

    def TCSendButtonHook(self):
        cmd = self.TCCmd.currentText()
        addr = self.TCaddr.toPlainText()
        par1 = self.TCPar1.toPlainText()
        par2 = self.TCPar2.toPlainText()

        self.TCret.setText("TODO")

        print("TODO")
        print(cmd)
        print(addr)
        print(par1)
        print(par2)

    def AlarmDefaultsButtonHook(self):
        for a in self.alarms:
            a['min'].setText('0')
            a['max'].setText('10')

        print("TODO")


class PlotApp(QMainWindow):
    def __init__(self, egse_tm):
        super().__init__()
        self.egse_tm = egse_tm

        self.left = 10
        self.top = 10
        self.title = 'Plot'
        self.width = 640
        self.height = 400
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.m = PlotCanvas(self, width=6.5, height=4)
        self.m.move(0, 0)

        print("Show")
        self.show()


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.plot(parent.egse_tm.daemon.get_sensor_samples())

    def plot(self, data: List[float]):
        ax = self.figure.add_subplot(111)
        ax.cla()
        ax.plot(data, 'r-')
        ax.set_title('PyQt Matplotlib Example2')
        self.draw()


def run(daemon: DaemonABC):
    app = QApplication(sys.argv)
    egsetm = EgseTm(daemon)
    egseconf = EgseConf(egsetm)
    egseconf.show()
    sys.exit(app.exec_())
