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

	def __init__(self, parent = None, width = 5, height = 4, dpi = 100, fitter = None):

		self._fitter = fitter

		fig = Figure(figsize = (width, height), dpi = dpi)
		self.axes = fig.add_subplot(111)

		super().__init__(fig)
		self.setParent(parent)

		FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)

		self.plot()

	def plot(self):

		data = self._fitter.plot()

		for e in data:
			mr, heats, calc = data[e]

			ax = self.figure.add_subplot(111)
			ax.plot(mr,heats,"o")

			ax.plot(mr,calc,linewidth=1.5)

			self.draw()

class PlotBox(QWidget):
	"""
	hold plot widget and update plot
	"""

	def __init__(self, exp_list):
		super().__init__()

		self._exp_list = exp_list

		self.layout()

	def layout(self):
		main_layout = QVBoxLayout(self)

		self._plot_layout = QVBoxLayout()
		plot_frame = QFrame()
		plot_frame.setLayout(self._plot_layout)

		main_layout.addWidget(plot_frame)
		
		gen_plot = QPushButton("Generate Plot", self)
		gen_plot.clicked.connect(self.update_plot)
		main_layout.addWidget(gen_plot)

	def update_plot(self):
		if self._exp_list:
			self._fitter = self._exp_list[0]

			plot_figure = Plot(fitter = self._fitter)
			self._plot_layout.addWidget(plot_figure)

class Sliders(QWidget):
	"""
	create sliders for an experiment
	"""

	def __init__(self, exp, param_name, value, fitter):
		super().__init__()

		self._exp = exp
		self._param_name = param_name
		self._value = value
		self._fitter = fitter

		self.layout()

	def layout(self):

		layout = QGridLayout(self)

		self._name_label = QLabel(self._param_name, self)
		layout.addWidget(self._name_label, 0, 0, 0, 2)

		self._fix = QCheckBox("Fix?", self)
		self._fix.toggle()
		self._fix.setChecked(False)
		self._fix.stateChanged.connect(self.fix)
		layout.addWidget(self._fix, 1, 0)

		self._slider = QSlider(Qt.Horizontal, self)
		self._slider.setFocusPolicy(Qt.NoFocus)
		self._slider.valueChanged[int].connect(self.update_val)
		layout.addWidget(self._slider, 1, 1)

		self._fix_int = QLineEdit(self)
		layout.addWidget(self._fix_int, 1, 2)
		self._fix_int.setText(str(1))
		self._fix_int.hide()

		self._link = QComboBox(self)
		self._link.addItem("Unlink")
		self._link.addItem("Add Global Var")
		for i in self._global_list:
			self._link.addItem(i)

		self._link.activated[str].connect(self.link_unlink)
		layout.addWidget(self._link, 1, 3)

	def fix(self, state):

		if state == Qt.Checked:
			# change widget views
			self._fix_int.show()
			self._slider.hide()

			self._fitter.fix(self._exp, **{self._param_name: int(self._fix_int.text())})
			print(self._fix_int.text())
		else:
			#change widget views
			self._fix_int.hide()
			self._slider.show()

			self._fitter.unfix(*[self._param_name], expt = self._exp)
			print('unfixed')

	#def set_fix(self, value):

		#self._fitter.fix(self._exp, **{self._param_name: int(self._fix_int.text())})

	def update_val(self, value):

		self._fitter.update_guess(self._param_name, value, self._exp)
		print(value)


class LocalSliders(Sliders):
	"""
	create sliders for an experiment
	"""

	def __init__(self, exp, param_name, value, fitter, global_list, parent_list):

		self._global_list = global_list
		self._parent_list = parent_list

		super().__init__(exp, param_name, value, fitter)

	def link_unlink(self, status):

		if status == "Unlink":
			self._fitter.unlink_from_global(self._exp, self._param_name)
			print("unlinked")
		elif status == "Add Global Var":
			text, ok = QInputDialog.getText(self, "Add Global Variable", "Var Name: ")
			if ok: 
				self._global_list.append(text)
				for e in self._parent_list.values():
					for i in e:
						i.update_global(text)
		else:
			self._fitter.link_to_global(self._exp, self._param_name, status)
			print("linked to " + status)

	def update_global(self, value):

		self._link.addItem(value)

class GlobalSliders(Sliders):
	"""
	create sliders for an experiment
	"""

	def __init__(self, exp, param_name, value, fitter):
		super().__init__(exp, param_name, value, fitter)


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

	def __init__(self, fitter, exp, labels, global_var):
		super().__init__()

		self._exp = exp
		self._labels = labels
		self._fitter = fitter
		self._global_var = global_var

		self.layout()

	def layout(self):
		main_layout = QVBoxLayout(self)

		parameters = self._exp.param_values
		exp_layout = QVBoxLayout()
		self._exp_widget = QFrame()
		self._exp_widget.setLayout(exp_layout)

		main_layout.addWidget(self._exp_widget)

		for p, v in parameters.items():
			s = LocalSliders(self._exp, p, v, self._fitter, self._global_var, self._labels)
			self._labels[self._exp].append(s)
			exp_layout.addWidget(s)

		divider = QFrame()
		divider.setFrameShape(QFrame.HLine)
		main_layout.addWidget(divider)

		remove = QPushButton("Remove", self)
		remove.clicked.connect(self.remove)

		hide = QPushButton("Hide", self)
		hide.clicked.connect(self.hide)

		show = QPushButton("Show", self)
		show.clicked.connect(self.show)

		stretch = QHBoxLayout()
		stretch.addStretch(1)
		stretch.addWidget(hide)
		stretch.addWidget(show)
		stretch.addWidget(remove)
		main_layout.addLayout(stretch)


	def print_exp(self):

		print(self._labels)

	def remove(self):

		 self._fitter.remove_experiment(self._exp)
		 self._labels.pop(self._exp, None)
		 self.close()

	def hide(self):

		self._exp_widget.hide()

	def show(self):

		self._exp_widget.show()

class AllExp(QWidget):
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
				self._labels[i] = []
				exp = Experiments(fitter, i, self._labels, self._global_var)
				self._exp_box.addWidget(exp)
			else:
				fitter.fit()
				print('already in frame')


	def print_exp(self):

		print(self._labels)

	def remove(self, exp_frame):

		 pass

	def hide(self, exp_frame):

		exp_frame.hide()

	def show(self, exp_frame):

		exp_frame.show()