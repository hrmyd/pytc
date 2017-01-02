"""
pytc GUI using qtpy bindings
"""

import pytc
import sys
from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtWidgets import *

from setup_widgets import *
from exp_widgets import *

class Splitter(QWidget):
	"""
	hold main experiment based widgets
	"""

	def __init__(self, exp_list):
		super().__init__()

		self._exp_list = exp_list
		self.layout()

	def layout(self):
		"""
		"""

		main_frame = QHBoxLayout(self)

		exp_box = Experiments(self._exp_list)

		plot_frame = QFrame(self)
		plot_frame.setFrameShape(QFrame.StyledPanel)

		fit_widgets = QFrame(self)
		fit_widgets.setFrameShape(QFrame.StyledPanel)

		splitter1 = QSplitter(Qt.Horizontal)
		splitter1.addWidget(exp_box)
		splitter1.addWidget(plot_frame)
		splitter1.setSizes([200, 200])

		splitter2 = QSplitter(Qt.Vertical)
		splitter2.addWidget(splitter1)
		splitter2.addWidget(fit_widgets)
		#splitter2.setSizes([10])

		main_frame.addWidget(splitter2)
		self.setLayout(main_frame)

		#plot = Plot(parent = self, width = 4, height = 5, dpi = 100, fitter = pytc.GlobalFit())
		#plot_box.addWidget(plot)


class Main(QMainWindow):
	"""
	"""
	def __init__(self):
		super().__init__()

		self._exp_list = []

		self.menu()
		self.new_exp()

	def menu(self):
		"""
		make the menu bar
		"""
		menu = self.menuBar()
		menu.setNativeMenuBar(False)

		file_menu = menu.addMenu("Experiments")
		testing_commands = menu.addMenu("Testing")

		return_exp = QAction("Print Experiments", self)
		return_exp.setShortcut("Ctrl+P")
		return_exp.triggered.connect(self.print_exp)
		testing_commands.addAction(return_exp)

		return_fitter = QAction("Print Fitter", self)
		#return_fitter.setShortcut("Ctrl+P")
		return_fitter.triggered.connect(self.print_fitter)
		testing_commands.addAction(return_fitter)

		new_exp = QAction("New", self)
		new_exp.setShortcut("Ctrl+N")
		new_exp.triggered.connect(self.new_exp)
		file_menu.addAction(new_exp)

		add_exp = QAction("Add", self)
		add_exp.setShortcut("Ctrl+A")
		add_exp.triggered.connect(self.add_file)
		file_menu.addAction(add_exp)

		export_exp = QAction("Export", self)
		export_exp.setShortcut("Ctrl+E")
		export_exp.triggered.connect(self.export_file)
		file_menu.addAction(export_exp)

		save_exp = QAction("Save", self)
		save_exp.setShortcut("Ctrl+S")
		file_menu.addAction(save_exp)

		open_exp = QAction("Open", self)
		open_exp.setShortcut("Ctrl+O")
		file_menu.addAction(open_exp)

		exp = Splitter(self._exp_list)
		self.setCentralWidget(exp)

		self.setGeometry(300, 150, 900, 600)
		self.setWindowTitle('pytc')
		self.show()

	def print_exp(self):
		"""
		testing, check pytc experiments loading
		"""

		print(self._exp_list[1:])

	def print_fitter(self):

		print(self._exp_list[0])

	def add_file(self):
		"""
		add a new pytc experiment.
		"""
		self._new_exp = AddExp(self._exp_list)
		self._new_exp.setGeometry(500, 400, 500, 100)
		self._new_exp.show()

	def new_exp(self):
		"""
		choose fitter and start new fit
		"""
		self._choose_fitter = ChooseFitter(self._exp_list)
		self._choose_fitter.setGeometry(550, 420, 300, 100)
		self._choose_fitter.show()

	def export_file(self):
		"""
		export data and graph as .csv
		"""
		file_name = QFileDialog.getSaveFileName(self, "Save File")
		data_file = open(file_name, "w")

		data_file.close()

if __name__ == '__main__':

	app = QApplication(sys.argv)
	pytc_run = Main()
	sys.exit(app.exec_())