"""
pytc GUI using qtpy bindings
"""

import pytc
import sys, glob
from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtWidgets import *
import pandas as pd
from inspect import signature
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class AddExp(QWidget):
	"""
	add experiment pop-up box
	"""

	def __init__(self, exp_list):
		super().__init__()

		self._models = {"Blank" : pytc.models.Blank,
                        "Single Site" : pytc.models.SingleSite,
                        "Single Site Competitor" : pytc.models.SingleSiteCompetitor,
                        "Binding Polynomial" : pytc.models.BindingPolynomial}

		self._exp_model = self._models["Blank"]
		self._exp_file = None
		self._shot_start = 1
		self._exp_list = exp_list

		self.exp_layout()

	def exp_layout(self):
		"""
		"""
		# exp text, model dropdown, shots select

		layout = QGridLayout()
		self.setLayout(layout)

		model_select = QComboBox(self)
		for k, v in self._models.items():
			model_select.addItem(k)

		model_select.activated[str].connect(self.model_select)

		load_exp = QPushButton("Load File", self)
		load_exp.clicked.connect(self.add_file)

		self._exp_label = QLabel("...", self)

		shot_start_text = QLineEdit(self)
		shot_start_text.textChanged[str].connect(self.shot_select)

		gen_exp = QPushButton("Generate Experiment", self)
		gen_exp.clicked.connect(self.generate)

		layout.addWidget(load_exp, 1, 1)
		layout.addWidget(self._exp_label, 1, 2)
		layout.addWidget(model_select, 1, 3)
		layout.addWidget(shot_start_text, 1, 4)
		layout.addWidget(gen_exp, 2, 4)

	def model_select(self, model):
		"""
		"""
		self._exp_model = self._models[model]
		#print(self._exp_model)

	def shot_select(self, shot):
		"""
		"""
		self._shot_start = int(shot)
		#print(self._shot_start, type(self._shot_start))

	def add_file(self):
		"""
		"""
		file_name, _ = QFileDialog.getOpenFileName(self, "Select a file...", "", filter="DH Files (*.DH)")
		self._exp_file = str(file_name)
		self._exp_label.setText(file_name.split("/")[-1])
		#print(self._exp_file, type(self._exp_file))

	def generate(self):
		"""
		"""
		itc_exp = pytc.ITCExperiment(self._exp_file, self._exp_model, self._shot_start)
		self._exp_list.append(itc_exp)
		self.close()

class ChooseFitter(QWidget):
	def __init__(self, exp_list):
		super().__init__()

		self._fitter_choose = {"Global" : pytc.GlobalFit(),
                        "Proton Linked" : pytc.ProtonLinked()}

		self._fitter = self._fitter_choose["Global"]
		self._exp_list = exp_list

		self.fitter_layout()

	def fitter_layout(self):
		"""
		"""
		# exp text, model dropdown, shots select

		layout = QGridLayout()
		self.setLayout(layout)

		fitter_select = QComboBox(self)
		for k, v in self._fitter_choose.items():
			fitter_select.addItem(k)

		fitter_select.activated[str].connect(self.fitter_select)

		gen_fitter = QPushButton("Select Fitter", self)
		gen_fitter.clicked.connect(self.generate)

		layout.addWidget(fitter_select, 1, 1)
		layout.addWidget(gen_fitter, 2, 4)

	def fitter_select(self, fitter):

		self._fitter = self._fitter_choose[fitter]

	def generate(self):
		"""
		"""
		if len(self._exp_list) == 0:
			self._exp_list.append(self._fitter)
		else:
			print("start over")
			
		self.close()

class Plot(FigureCanvas):
	"""
	create a plot widget
	"""

	def __init__(self, parent, width, height, dpi, fitter):
		super().__init__()

		fig = Figure(figsize = (width, height), dpi = dpi)
		self.axes = fig.add_subplot(111)
		self.axes.hold(False)

		self.compute_initial_figure()
		self.setParent(parent)
		self._fitter = fitter

		FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)

	def compute_initial_figure(self):

		self.update_figure()

	def update_figure(self):

		self._fitter.fit()
		self._fitter.plot()

class Sliders(QWidget):
	"""
	create sliders for an experiment
	"""

	def __init__(self, param_name, value, global_list, parent_list, fitter):
		super().__init__()

		self._param_name = param_name
		self._value = value
		self._global_list = global_list
		self._parent_list = parent_list
		self._fitter = fitter

		self.layout()

	def layout(self):

		layout = QGridLayout(self)

		name_label = QLabel(self._param_name, self)
		layout.addWidget(name_label, 0, 0, 0, 2)

		fix = QCheckBox("Fix?", self)
		fix.toggle()
		fix.stateChanged.connect(self.fix)
		layout.addWidget(fix, 1, 0)

		slider = QSlider(Qt.Horizontal, self)
		slider.setFocusPolicy(Qt.NoFocus)
		slider.valueChanged[int].connect(self.update_val)
		layout.addWidget(slider, 1, 1)

		self._link = QComboBox(self)
		self._link.addItem("Unlink")
		self._link.addItem("Add Global Var")
		for i in self._global_list:
			self._link.addItem(i)

		self._link.activated[str].connect(self.link_unlink)
		layout.addWidget(self._link, 1, 2)

	def fix(self, state):

		if state == Qt.Checked:
			print('fixed')
		else:
			print('unfixed')

	def update_val(self, value):

		print(value)

	def link_unlink(self, status):

		if status == "Unlink":
			print("unlinked")
		elif status == "Add Global Var":
			text, ok = QInputDialog.getText(self, "Add Global Variable", "Var Name: ")
			if ok: 
				self._global_list.append(text)
				for e in self._parent_list.values():
					for i in e:
						i.update_global(text)
		else:
			print("linked to " + status)

	def update_global(self, value):

		self._link.addItem(value)

class Experiments(QWidget):
	"""
	experiment box widget
	"""

	def __init__(self, exp_list):
		super().__init__()

		self._exp_list = exp_list
		self._labels = {}
		self._global_var = []
		self.initGUI()

	def initGUI(self):

		layout = QVBoxLayout(self)

		scroll = QScrollArea(self)
		layout.addWidget(scroll)

		exp_content = QWidget()
		self._exp_box = QVBoxLayout(exp_content)
		scroll.setWidget(exp_content)
		scroll.setWidgetResizable(True)

		gen_experiments = QPushButton("Fit Experiments", self)
		gen_experiments.clicked.connect(self.add_exp)
		layout.addWidget(gen_experiments)

		print_exp = QPushButton("Print Experiments", self)
		print_exp.clicked.connect(self.print_exp)
		layout.addWidget(print_exp)

	def add_exp(self):

		for i in self._exp_list:
			if i not in self._labels:
				parameters = i.param_values
				self._labels[i] = []
				exp_layout = QVBoxLayout()
				exp_widget = QFrame()
				exp_widget.setLayout(exp_layout)

				self._exp_box.addWidget(exp_widget)

				divider = QFrame()
				divider.setFrameShape(QFrame.HLine)
				self._exp_box.addWidget(divider)

				for p, v in parameters.items():
					s = Sliders(p, v, self._global_var, self._labels)
					self._labels[i].append(s)
					exp_layout.addWidget(s)
			else:
				print('already in frame')


	def print_exp(self):

		print(self._labels)

	def remove(self, exp_frame):

		 pass

	def hide(self, exp_frame):

		exp_frame.hide()

	def show(self, exp_frame):

		exp_frame.show()

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

		self.setGeometry(400, 250, 900, 600)
		self.setWindowTitle('pytc')
		self.show()

	def print_exp(self):
		"""
		testing, check pytc experiments loading
		"""

		print(self._exp_list[:1])

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
		self._choose_fitter.setGeometry(500, 400, 500, 100)
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