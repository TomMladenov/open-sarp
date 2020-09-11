#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Tom Mladenov, tom.mladenov@ieee.org"

import os
import zmq
import sys
import time
import csv
from threading import Thread, Lock
from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtUiTools
import datetime
import logging
from bitarray import bitarray, util
from SARPFrame import SARPFrame
from BeaconMessage import USER_PROTOCOLS
import pyqtgraph as pg
import subprocess

VERSION = 'v1.3'

def decodeManchester(arr, inverted):
	len = arr.length()

	if not len % 2 == 0:
		raise Exception("bitarray must be of even length!")
	else:
		a = bitarray()

	index = 0
	while True:
		if arr[index] == 0 and arr[index + 1] == 1:
			if not inverted:
				a.append(False)
			else:
				a.append(True)
			index = index + 2
		elif arr[index] == 1 and arr[index + 1] == 0:
			if not inverted:
				a.append(True)
			else:
				a.append(False)
			index = index + 2
		else:
			raise Exception("Error in differential decoding of frame!")

		if index + 1 > len:
			break

	return a.tobytes()


class BeaconQueryWindow(QtWidgets.QDialog):

	def __init__(self, parent):
		super(BeaconQueryWindow, self).__init__(parent)
		self.parent = parent
		loader = QtUiTools.QUiLoader()
		self.ui = loader.load('gui/beaconwindow.ui', parent)
		self.ui.setWindowTitle('Beacon Query')
		self.ui.setFixedSize(self.ui.size())

		self.ui.sarp_table.setColumnCount(3)
		self.ui.sarp_table.setHorizontalHeaderLabels(['Parameter', 'Value', 'Unit'])
		sarp_table_header = self.ui.sarp_table.horizontalHeader()
		sarp_table_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		sarp_table_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
		sarp_table_header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)


		#self.ui.beacon_table

	def setData(self, object):
		self.object = object
		self.ui.sarp_table.clearContents()
		self.ui.sarp_table.setRowCount(0)

		for item in self.object.data:
			currentline = self.ui.sarp_table.rowCount()
			self.ui.sarp_table.insertRow(currentline)
			self.ui.sarp_table.setItem(currentline, 0, QtWidgets.QTableWidgetItem(item))
			self.ui.sarp_table.setItem(currentline, 1, QtWidgets.QTableWidgetItem(str(self.object.data[item])))
			self.ui.sarp_table.setItem(currentline, 2, QtWidgets.QTableWidgetItem("Hz"))
		#self.ui.freq_label.setText('Burst frequency: {F} Hz'.format(F=object.data['abs_freq']))



class SARPFrameTableModel(QtCore.QAbstractTableModel):

	def __init__(self, data):
		QtCore.QAbstractTableModel.__init__(self)
		self._data = data

	def setHeader(self, header):
		self._header = header

	def rowCount(self, parent):
		return len(self._data)

	def columnCount(self, parent):
		return len(self._header)

	def data(self, index, role):
		if role == QtCore.Qt.BackgroundColorRole:
			if index.column() == 2:
				if self._data[index.row()].valid:
					return QtGui.QColor(0,255,0)
				else:
					return QtGui.QColor(255,0,0)
		elif role != QtCore.Qt.DisplayRole:
			return None
		else:
			if index.column() == 0:
				return str(self._data[index.row()].frame_creation_time)
			elif index.column() == 1:
				return self._data[index.row()].length
			elif index.column() == 2:
				if self._data[index.row()].valid:
					return 'VALID'
				else:
					return 'ERROR'

	def headerData(self, section, orientation, role):
		if role != QtCore.Qt.DisplayRole or orientation != QtCore.Qt.Horizontal:
			return None
		return self._header[section]


class SARPMessageTableModel(QtCore.QAbstractTableModel):

	def __init__(self, data):
		QtCore.QAbstractTableModel.__init__(self)
		self._data = data

	def setHeader(self, header):
		self._header = header

	def rowCount(self, parent):
		return len(self._data)

	def columnCount(self, parent):
		return len(self._header)

	def data(self, index, role):
		if index.isValid():

			if role == QtCore.Qt.DecorationRole:
				if index.column() == 11:
					if self._data[index.row()].beacon_message.data['country_name'] != 'N/A':
						country_string = self._data[index.row()].beacon_message.data['country_name_alpha2'].lower()
						return QtGui.QIcon('gui/graphics/flags/{STR}.png'.format(STR=country_string))
					else:
						return None
				else:
					return None


			elif role == QtCore.Qt.BackgroundColorRole:
				if index.column() == 2:
					if self._data[index.row()].data['rt/pb'] == 'REALTIME':
						return QtGui.QColor(255,255,0)
					else:
						return None

				elif index.column() == 3:
					if self._data[index.row()].data['timecode_parity_valid']:
						return QtGui.QColor(0,255,0)
					else:
						return QtGui.QColor(255,0,0)


				elif index.column() == 8:
					if self._data[index.row()].data['doppler_parity_valid']:
						return QtGui.QColor(0,255,0)
					else:
						return QtGui.QColor(255,0,0)

				elif index.column() == 1:
					if self._data[index.row()].data['format_valid']:
						return QtGui.QColor(0,255,0)
					else:
						return QtGui.QColor(255,0,0)
			elif role != QtCore.Qt.DisplayRole:
				return None
			else:
				switcher={
							0: str(self._data[index.row()].data['message_creation_time']),
							1: self._data[index.row()].data['format'],
							2: self._data[index.row()].data['rt/pb'],
							3: str(self._data[index.row()].data['timecode']),
							4: str(self._data[index.row()].data['dru']),
							5: str(self._data[index.row()].data['pseudo']),
							6: self._data[index.row()].data['latest'],
							7: self._data[index.row()].data['type'],
							8: str(round(float(self._data[index.row()].data['abs_freq'])/1000.0, 2)),
							9: self._data[index.row()].data['level_dbm'],
							10: self._data[index.row()].data['s/no_db'],
							11: self._data[index.row()].beacon_message.data['country_name_alpha2'],
							12: self._data[index.row()].beacon_message.data['protocol_name_shortened'],
							13: self._data[index.row()].beacon_message.data['beacon_hex']
						}

				return switcher.get(index.column(), "N/A")

	def headerData(self, section, orientation, role):
		if role != QtCore.Qt.DisplayRole or orientation != QtCore.Qt.Horizontal:
			return None
		return self._header[section]


class Main(QtWidgets.QMainWindow):

	prev_len = 0

	def __init__(self, parent=None):
		super(Main, self).__init__(parent)
		eventLogger.info('SARSAT Frame Processor Desktop')
		eventLogger.info('Loading GUI file {GUI}'.format(GUI='gui'))

		loader = QtUiTools.QUiLoader()
		self.ui = loader.load('gui/gui.ui', parent)
		self.ui.show()

		self.beaconquerywindow = BeaconQueryWindow(self)
		self.beaconquerywindow.hide()

		self.layout_widget = pg.GraphicsLayoutWidget()
		self.beaconwindow = self.layout_widget.addPlot()

		self.beaconplot = pg.ScatterPlotItem(size=10, pen=pg.mkPen(None))
		self.beaconplot.sigClicked.connect(self.querySample)


		self.ref_freq = pg.InfiniteLine(pos=406022500, angle=0)
		self.beaconwindow.addItem(self.beaconplot)
		self.beaconwindow.addItem(self.ref_freq)
		self.beaconwindow.addLegend()
		self.beaconwindow.setLabel('left', "Burst frequency [Hz]")
		self.beaconwindow.setLabel('bottom', "Satellite Timecode [20-1 s]")
		self.layout_widget.setWindowTitle('Beacon viewer')
		self.layout_widget.show()

		self.ui.setWindowTitle('SARSAT Frame Processor Desktop {VER}'.format(VER=VERSION))
		self.ui.setFixedSize(self.ui.size())
		self.ui.version_label.setText('SARSAT Frame Processor Desktop {VER}'.format(VER=VERSION))

		self.ui.message_format_box.addItem('SARSAT SARP-2')
		self.ui.message_format_box.addItem('SARSAT SARP-3')
		self.ui.message_format_box.setCurrentIndex(1)
		self.ui.message_format_box.currentIndexChanged.connect(self.updateMessageFormat)

		self.ui.actionSave_TM_to_csv.triggered.connect(self.test)

		self.adapter = TMAdapter(self, "127.0.0.1", 38211, self.ui.message_format_box.currentText())
		self.adapter.update_signal.connect(self.updateTableViews)
		self.adapter.count_signal.connect(self.updateCounters)

		self.adapter.symbol_signal.connect(self.updateSymbolStatus)
		self.adapter.decoder_signal.connect(self.updateDecoderStatus)
		self.adapter.sync_signal.connect(self.updateSyncStatus)
		self.adapter.format_signal.connect(self.updateFormatStatus)

		self.sarp_frame_table_model = SARPFrameTableModel(self.adapter.sarp_frames)
		self.sarp_frame_table_model.dataChanged.connect(self.printMessage)
		self.sarp_frame_table_model.setHeader(['RX UTC (Ground)', 'Length', 'Check'])
		self.ui.sarp_frame_table.setModel(self.sarp_frame_table_model)
		self.ui.sarp_frame_table.setColumnWidth(0,175)
		self.ui.sarp_frame_table.setColumnWidth(1,50)
		self.ui.sarp_frame_table.setColumnWidth(2,50)

		hheader = self.ui.sarp_frame_table.horizontalHeader()
		hheader.setFixedHeight(20)
		vheader = self.ui.sarp_frame_table.verticalHeader()
		vheader.setDefaultSectionSize(15)
		self.ui.sarp_frame_table.show()

		self.sarp_message_table_model = SARPMessageTableModel(self.adapter.sarp_messages)
		self.sarp_message_table_model.setHeader(['RX UTC (Ground)', 'Format', 'RT/PB', 'Timecode', 'DRU', 'Pseudo', 'Latest', 'Type', 'Burst freq', 'Level', 'S/No', 'Country', 'Protocol', 'Beacon hex'])

		self.ui.sarp_message_table.setModel(self.sarp_message_table_model)
		self.ui.sarp_message_table.setColumnWidth(0,175)
		self.ui.sarp_message_table.setColumnWidth(1,50)
		self.ui.sarp_message_table.setColumnWidth(2,70)
		self.ui.sarp_message_table.setColumnWidth(3,70)
		self.ui.sarp_message_table.setColumnWidth(4,0)
		self.ui.sarp_message_table.setColumnWidth(5,0)
		self.ui.sarp_message_table.setColumnWidth(6,0)
		self.ui.sarp_message_table.setColumnWidth(7,80)
		self.ui.sarp_message_table.setColumnWidth(8,75)
		self.ui.sarp_message_table.setColumnWidth(9,50)
		self.ui.sarp_message_table.setColumnWidth(10,50)
		self.ui.sarp_message_table.setColumnWidth(11,50)
		self.ui.sarp_message_table.setColumnWidth(13,225)

		hheader = self.ui.sarp_message_table.horizontalHeader()
		hheader.setFixedHeight(20)
		vheader = self.ui.sarp_message_table.verticalHeader()
		vheader.setDefaultSectionSize(15)
		self.ui.sarp_message_table.show()


		self.ui.host_label.setText(self.adapter.host)
		self.ui.frame_counter_label.setText('0')
		self.ui.message_counter_label.setText('0')
		eventLogger.info('GUI Thread started')

		self.graphTimer = QtCore.QTimer()
		self.graphTimer.timeout.connect(self.updateBeaconView)
		self.graphTimer.start(1000)

		self.adapter.start()

	def querySample(self, points):
		#print(points.ptsClicked[0].pos())
		self.beaconquerywindow.setData(points.ptsClicked[0].data())
		self.beaconquerywindow.ui.show()

	def test(self):
		for key in USER_PROTOCOLS:
			row_list = [["timecode", "frequency", "type"]]

			for message in self.adapter.sarp_messages:

				if message.beacon_message.data['protocol_num'] == key:
					row_list.append([message.data['timecode'], message.data['abs_freq'], message.beacon_message.data['protocol_num']])

			with open('log/beacon_messages_20161031_094324Z_1544478984Hz_{KEY}.csv'.format(KEY=key), 'w', newline='') as file:
				writer = csv.writer(file)
				writer.writerows(row_list)

	def updateSymbolStatus(self, bool):
		if bool:
			self.ui.symbol_status_label.setText('FLOW')
			self.ui.symbol_status_label.setStyleSheet('background-color: rgb(0, 255, 0)')
		else:
			self.ui.symbol_status_label.setText('NO FLOW')
			self.ui.symbol_status_label.setStyleSheet('background-color: rgb(255, 0, 0)')

	def updateDecoderStatus(self, bool):
		if bool:
			self.ui.decoder_status_label.setText('DECODE OK')
			self.ui.decoder_status_label.setStyleSheet('background-color: rgb(0, 255, 0)')
		else:
			self.ui.decoder_status_label.setText('DECODE ERROR')
			self.ui.decoder_status_label.setStyleSheet('background-color: rgb(255, 0, 0)')

	def updateSyncStatus(self, bool):
		if bool:
			self.ui.sync_status_label.setText('GOOD FRAME')
			self.ui.sync_status_label.setStyleSheet('background-color: rgb(0, 255, 0)')
		else:
			self.ui.sync_status_label.setText('BAD FRAME')
			self.ui.sync_status_label.setStyleSheet('background-color: rgb(255, 0, 0)')

	def updateFormatStatus(self, bool):
		if bool:
			self.ui.format_status_label.setText('FORMAT OK')
			self.ui.format_status_label.setStyleSheet('background-color: rgb(0, 255, 0)')
		else:
			self.ui.format_status_label.setText('FORMAT ERROR')
			self.ui.format_status_label.setStyleSheet('background-color: rgb(255, 0, 0)')


	def updateMessageFormat(self, index):
		new_message_format = self.ui.message_format_box.currentText()
		self.adapter.setMessageFormat(new_message_format)


	def printMessage(self, tuple):
		print(str(tuple))

	def updateLink(self, up):
		if up:
			self.ui.link_label.setText('TM FLOW')
			self.ui.link_label.setStyleSheet('background-color: rgb(0, 255, 0)')
		else:
			self.ui.link_label.setText('NO TM')
			self.ui.link_label.setStyleSheet('background-color: rgb(255, 0, 0)')

	def updateCounters(self, len_frames, len_messages):
		self.ui.frame_counter_label.setText('{FRAMES}'.format(FRAMES=len_frames))
		self.ui.message_counter_label.setText('{MESSAGES}'.format(MESSAGES=len_messages))

	def updateTableViews(self):

		length = len(self.adapter.sarp_frames)

		if not length == self.prev_len:
			#=============== UPDATE TABLES FROM MODELS ================
			self.sarp_frame_table_model = SARPFrameTableModel(self.adapter.sarp_frames)
			self.sarp_frame_table_model.setHeader(['RX UTC (Ground)', 'Length', 'Check'])
			self.ui.sarp_frame_table.setModel(self.sarp_frame_table_model)

			self.sarp_message_table_model = SARPMessageTableModel(self.adapter.sarp_messages)
			self.sarp_message_table_model.setHeader(['RX UTC (Ground)', 'Format', 'RT/PB', 'Timecode', 'DRU', 'Pseudo', 'Latest', 'Type', 'Burst freq', 'Level', 'S/No', 'Country', 'Protocol', 'Beacon hex'])
			self.ui.sarp_message_table.setModel(self.sarp_message_table_model)
			#======================= AUTO SCROLL ========================

			if self.ui.frames_auto_scroll_box.isChecked():
				self.ui.sarp_frame_table.scrollToBottom()

			if self.ui.messages_auto_scroll_box.isChecked():
				self.ui.sarp_message_table.scrollToBottom()

			self.prev_len = len(self.adapter.sarp_frames)

	def updateBeaconView(self):

		datapoints_freq = []
		datapoints_timecode = []

		current_sarp_messages = [x for x in self.adapter.sarp_messages]

		symbols = [		'o' 	if m.beacon_message.data['protocol_num'] == 0
				else 	's' 	if m.beacon_message.data['protocol_num'] == 1
				else 	't' 	if m.beacon_message.data['protocol_num'] == 2
				else 	'd' 	if m.beacon_message.data['protocol_num'] == 3
				else 	's' 	if m.beacon_message.data['protocol_num'] == 4
				else 	't' 	if m.beacon_message.data['protocol_num'] == 5
				else 	'd' 	if m.beacon_message.data['protocol_num'] == 6
				else '+' for m in current_sarp_messages]

		brushes = [		pg.mkBrush(255, 0, 0, 255)	if m.beacon_message.data['protocol_num'] == 0
				else 	pg.mkBrush(0, 255, 0, 255) 	if m.beacon_message.data['protocol_num'] == 1
				else 	pg.mkBrush(0, 0, 255, 255) 	if m.beacon_message.data['protocol_num'] == 2
				else 	pg.mkBrush(0, 0, 255, 255) 	if m.beacon_message.data['protocol_num'] == 3
				else 	pg.mkBrush(0, 255, 0, 255) 	if m.beacon_message.data['protocol_num'] == 4
				else 	pg.mkBrush(255, 0, 0, 255) 	if m.beacon_message.data['protocol_num'] == 5
				else 	pg.mkBrush(255, 0, 0, 255) 	if m.beacon_message.data['protocol_num'] == 6
				else 	pg.mkBrush(255, 0, 0, 255)	for m in current_sarp_messages]

		self.beaconplot.setData(	x=[x.data['timecode'] for x in current_sarp_messages],
									y=[x.data['abs_freq'] for x in current_sarp_messages],
									data=[x for x in current_sarp_messages],
									symbol=symbols,
									brush=brushes)




class TMAdapter(QtCore.QThread):


	count_signal = QtCore.Signal(int, int)
	update_signal = QtCore.Signal(bool)
	plot_message_signal = QtCore.Signal(object)

	symbol_signal = QtCore.Signal(bool)
	decoder_signal = QtCore.Signal(bool)
	sync_signal = QtCore.Signal(bool)
	format_signal = QtCore.Signal(bool)

	sarp_frames = []
	sarp_messages = []
	message_format = None

	active = False
	host = None

	def __init__(self, parent, ip, port, message_format):
		QtCore.QThread.__init__(self, parent)
		self.parent = parent
		self.active = True
		self.message_format = message_format

		self.context = zmq.Context()
		self.socket = self.context.socket(zmq.SUB)
		self.host = 'tcp://' + ip + ':' + str(port)
		self.socket.connect(self.host)
		self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
		self.socket.setsockopt(zmq.RCVTIMEO, 1000)

		eventLogger.info('Started listening on {HOST} for incoming data from GNU Radio flowgraph'.format(HOST=self.host))

	def setMessageFormat(self, message_format):
		self.message_format = message_format

	def run(self):
		while self.active:
			try:
				data = self.socket.recv() #receive 1200 symbols
				self.symbol_signal.emit(True)
				b = bitarray(endian='big')
				b.extend([True if x == 1 else False for x in data])
				try:
					bytes = decodeManchester(b, inverted=False) #if we have a bad decode, this will raise an exception and the frame will not be considered
					self.decoder_signal.emit(True)
					sarp_frame = SARPFrame(bytes, self.message_format)
					self.sarp_frames.append(sarp_frame)
					if sarp_frame.valid: #if the frame structure looks ok, proceed and get the messages
						self.sync_signal.emit(True)
						if sarp_frame.message1.data['format_valid'] and sarp_frame.message2.data['format_valid'] and sarp_frame.message3.data['format_valid']:
							self.sarp_messages.append(sarp_frame.message1)
							self.sarp_messages.append(sarp_frame.message2)
							self.sarp_messages.append(sarp_frame.message3)
							self.plot_message_signal.emit([sarp_frame.message1, sarp_frame.message2, sarp_frame.message3])
							self.format_signal.emit(True)
						else:
							self.format_signal.emit(False)
					else:
						self.sync_signal.emit(False)
						self.format_signal.emit(False)


					self.update_signal.emit(True)
					eventLogger.info('GOOD FRAME DECODE: {LEN} bytes, Frame valid: {CHECK}'.format(LEN=len(bytes), CHECK=sarp_frame.valid))
				except Exception as e:
					self.decoder_signal.emit(False)
					self.sync_signal.emit(False)
					self.format_signal.emit(False)
					eventLogger.error('BAD FRAME DECODE: {ERR}'.format(ERR=e))

				self.count_signal.emit(len(self.sarp_frames), len(self.sarp_messages))
			except Exception as e:
				self.symbol_signal.emit(False)
				self.decoder_signal.emit(False)
				self.sync_signal.emit(False)
				self.format_signal.emit(False)
				self.update_signal.emit(True)


def setup_logger(name, log_file, level=logging.INFO):
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	logging.Formatter.converter = time.gmtime
	fileHandler = logging.FileHandler(log_file)
	streamHandler = logging.StreamHandler()

	fileHandler.setFormatter(formatter)
	streamHandler.setFormatter(formatter)

	logger = logging.getLogger(name)
	logger.setLevel(level)
	logger.addHandler(fileHandler)
	logger.addHandler(streamHandler)
	return logger


if __name__ == '__main__':

	path = os.path.dirname(os.path.abspath(__file__))
	now = datetime.datetime.utcnow()
	subprocess.run(["mkdir", "-p", "log"])  # doesn't capture output
	eventLogger = setup_logger('event_logger', path + '/log/sarp_processor_{DATE}.log'.format(DATE=now.strftime("%Y%m%d_%H%M%SZ")), level=logging.INFO)

	QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
	a = QtWidgets.QApplication(sys.argv)

	app = Main()
	app.show()
	a.exec_()
	os._exit(0)
