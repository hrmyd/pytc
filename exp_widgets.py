import pytc
from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtWidgets import *
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

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

	def __init__(self, exp, param_name, value, global_list, parent_list, fitter):
		super().__init__()

		self._exp = exp
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
		fix.setChecked(False)
		fix.stateChanged.connect(self.fix)
		layout.addWidget(fix, 1, 0)

		slider = QSlider(Qt.Horizontal, self)
		slider.setFocusPolicy(Qt.NoFocus)
		slider.valueChanged[int].connect(self.update_val)
		layout.addWidget(slider, 1, 1)

		self._fix_int = QLineEdit(self)
		layout.addWidget(self._fix_int, 1, 2)

		self._link = QComboBox(self)
		self._link.addItem("Unlink")
		self._link.addItem("Add Global Var")
		for i in self._global_list:
			self._link.addItem(i)

		self._link.activated[str].connect(self.link_unlink)
		layout.addWidget(self._link, 1, 3)

	def fix(self, state):

		if state == Qt.Checked:
			self._fitter.fix(self._exp, **{self._param_name: int(self._fix_int.text())})
			print(self._fix_int.text())
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

class Parameters(QWidget):
	"""
	widget for returning experiment parameters.
	"""

	def __init__(self, exp_list):
		super().__init__()

		self._exp_list = exp_list

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

		fitter = self._exp_list[0]

		for i in self._exp_list[1:]:
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
					s = Sliders(i, p, v, self._global_var, self._labels, fitter)
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