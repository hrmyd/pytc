import pytc
import ipywidgets as widgets
from IPython.display import display, clear_output
from .exp import LocalExp

class Interface:
    
    def __init__(self, fitter, global_exp):
        """
        """
        
        self._fitter = fitter
        self._experiments = []
        self._global_exp = global_exp
        self._param = []
        
    def view_exp(self):
        
        return self._experiments
    
    def add_experiment(self,expt):
        """
        add experiment to fitter
        """
        self._fitter.add_experiment(expt)
        self._experiments.append(expt)
        expt.initialize_param()
        
    def remove_experiment(self, expt):
        """
        remove experiment from fitter
        """
        self._fitter.remove_experiment(expt)
        self._experiments.remove(expt)


class FitGUI:
    
    def __init__(self, fitter):
        self._loc_exp = []
        self._glob_exp = {}
        self._global_var = ['blank']
        self._fitter = fitter
        self._gui = Interface(self._fitter, self._glob_exp)
        
        ENTRY_W = '200px'

        self._global_field = widgets.Text()
        self._global_add = widgets.Button(description = "Add Global Variable")
        self._global_remove = widgets.Button(description = "Remove Global Variable")
        self._add_exp_field = widgets.Button(description = "Add an Experiment")
        self._rmv_last_field = widgets.Button(description = "Remove Last Experiment")
        self._clear_widget = widgets.Button(description = "Clear")
        
        self._global_field.layout.width = '100px'
        self._global_add.layout.width = '160px'
        self._global_remove.layout.width = '160px'
        self._add_exp_field.layout.width = ENTRY_W
        self._rmv_last_field.layout.width = ENTRY_W
        
    def rm_last(self, b):

        if self._loc_exp:
            last_exp = self._loc_exp[-1]
            last_exp.remove_exp()

    def clear_exp(self, b):

        clear_output()
        for i in self._loc_exp:
            i.remove_exp()

        for i in self._glob_exp.values():
            i.remove_exp()

    def add_field(self, b):

        clear_output()
        exp = LocalExp(self._gui, self._loc_exp, self._fitter, self._global_var, self._glob_exp)
        show = exp.gen_exp()
        show.layout.margin = '30px 10px 0px 0px'

        self._loc_exp.append(exp)

        display(show)

    def create_global(self, b):

        glob_var = self._global_field.value

        if glob_var not in self._global_var and glob_var:
            self._global_var.append(glob_var)
            self._global_field.value = ''
        else:
            pass

    def remove_global(self, b):

        self._fitter.remove_global(self._global_field.value)
        global_var.remove(self._global_field.value)
    
    def build_gui(self):
        """
        """
        self._global_add.on_click(self.create_global)
        self._global_remove.on_click(self.remove_global)
        self._add_exp_field.on_click(self.add_field)
        self._rmv_last_field.on_click(self.rm_last)
        self._clear_widget.on_click(self.clear_exp)

        experiments_layout = widgets.Layout(display = "flex", 
                              flex_flow = "row", 
                              align_items = "stretch",
                              margin = "0px 0px 30px 0px")

        glob_box = widgets.Box(children = [self._global_field, self._global_add, self._global_remove],
                               layout = experiments_layout)
        #glob_box.layout.margin = "0px 0px 30px 0px"

        experiments = widgets.Box(children = [self._add_exp_field, self._rmv_last_field, self._clear_widget], 
                                              layout = experiments_layout)
        parent = widgets.Box(children = [experiments, glob_box])

        display(parent)
        self.add_field(None)