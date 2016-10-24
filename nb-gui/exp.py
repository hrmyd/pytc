import pytc
import ipywidgets as widgets
from IPython.display import display, clear_output
import glob

class ParamCollect():
    def __init__(self, gui, container, fitter):
        """
        """
        self._gui = gui
        self._exp_id = ''
        self._exp_val = ''
        self._widgets = []
        self._fitter = fitter
        self._container = container
        self._parameters = {}
        self._models = {"blank" : pytc.models.Blank,
          "single site" : pytc.models.SingleSite,  
          "single site competitor" : pytc.models.SingleSiteCompetitor, 
          "binding polynomial" : pytc.models.BindingPolynomial}
        self._current_model = ''
        
        self._exp_box = widgets.HBox()
        
        self._sliders = []
        
    def remove_button(self, b):
        """
        remove exp from fitter and lists
        """
        pass
    
    def parameters(self):
        """
        get parameters for experiment
        """
        pass
        
    def create_exp(self):
        """
        create a new pytc experiment
        """
        pass
        
    @property        
    def exp_id(self):
        """
        return experiment id
        """
        
        return self._exp_id
    
    
    def gen_sliders(self):
        """
        generate sliders for each experiment, give option to link to global.
        """
        
        pass
    
    def gen_exp(self):
        """
        generate widgets for experiment.
        """
        pass
    
class LocalExp(ParamCollect):
    """
    create experiment object and generate widgets
    """
    def __init__(self, gui, container, fitter, global_vars, global_exp):
        super().__init__(gui, container, fitter)

        self._global_vars = global_vars
        self._global_exp = global_exp
        
        self._exp_field = widgets.Text(description = "exp: ")
        self._model_drop = widgets.Dropdown(options = self._models, value = self._models["blank"])
        self._rm_exp = widgets.Button(description = "remove experiment")
        
    def remove_button(self, b):
        """
        remove experiment from analysis and close widgets. for use with button widget.
        """
        try:
            self._gui.remove_experiment(self._exp_id)
        except:
            clear_output()
            print("no experiment linked")
            
        for i in self._container:
            if self._exp_id == i[0]._exp_id:
                self._container.remove(i)
        
        self._exp_box.close()
                
        if self._sliders:
            for s in self._sliders:
                s.close_sliders()
                
    def remove_exp(self):
        """
        remove experiment and sliders, for use without button widget.
        """
        self.remove_button(None)
        
    def create_exp(self):
        """
        create new pytc exp
        """
        
        self._exp_val = self._exp_field.value
        if self._exp_val != 'none':
            self._current_model = self._model_drop.value
            self._exp_id = pytc.ITCExperiment(self._exp_val, self._current_model)
        else:
            clear_output()
            print("no exp data given")
    
    @property
    def parameters(self):
        """
        generate local parameters for experiment.
        """
        
        param = self._exp_id.model.param_values
        
        return param
    
    def gen_sliders(self):
        """
        generate sliders for each experiment, give option to link to global.
        """
        parameters = self.exp_id.param_values
        
        for p in parameters.keys():
            s = LocalSliders(self._exp_id, self._fitter, self._gui, p, self._global_vars, self._global_exp)
            self._sliders.append(s)
            
     
    def add_exp(self, sender):
        """
        generate sliders for experiment based on added data.
        """
        #self._exp_val = sender['new']
        self.create_exp()
        
        self._gui.add_experiment(self._exp_id)
        self.gen_sliders()
        
        self._exp_field.disabled = True
        self._model_drop.disabled = True
        
        for s in self._sliders:
            s.build_sliders()
            
    
    def gen_exp(self):
        """
        generate widgets for experiment.
        """
        
        self._exp_field.on_submit(self.add_exp)
        
        file_list = glob.glob("./**/*.DH")
        file_dict = {fname.split('/')[-1]: fname for fname in file_list}
        
        #exp_drop = widgets.Dropdown(options = file_dict, value = 'none')
        #exp_drop.observe(add_exp, 'value')

        self._rm_exp.on_click(self.remove_exp)

        self._exp_box.children = [self._exp_field, self._model_drop, self._rm_exp]
        self._widgets.extend([self._exp_field, self._model_drop, self._rm_exp, self._exp_box])
        
        return self._exp_box
    
class GlobalExp(ParamCollect):
    """
    create experiment object and generate widgets
    """
    def __init__(self, gui, container, fitter, v_name):
        
        super().__init__(gui, container, fitter)
        self._exp_id = v_name
        
        self._rm_exp = widgets.Button(description = "remove experiment")
        self._name_label = widgets.Label(value = "{}:  ".format(self._exp_id))
    
    @property
    def parameters(self):
        """
        generate local parameters for experiment.
        """
        
        param = self._fitter.fit_param[0][self._exp_id]
        
        return param
    
    def remove_button(self, b):
        """
        remove global parameter and unlink from all linked local parameters, for use with button widget
        """
        try:
            self._fitter.remove_global(self._exp_id)
        except:
            pass
        
        self._exp_box.close()
        self._container.pop(self._exp_id, None)
        self._sliders.close_sliders()
    
    def remove_exp(self):
        """
        remove and unlink global parameter
        """
        self.remove_button(None)
    
    def gen_sliders(self):
        """
        generate sliders for each experiment, give option to link to global.
        """
        s = GlobalSliders(None, self._fitter, self._gui, self._exp_id)
        self._sliders.append(s)
        
        s.build_sliders()
    
    def gen_exp(self):
        """
        generate widgets for experiment.
        """

        self._rm_exp.on_click(self.remove_exp)

        self._exp_box.children = [self._name_label, self._rm_exp]
        
        s = GlobalSliders(None, self._fitter, self._gui, self._exp_id)
        self._sliders = s

        display(self._exp_box)
        s.build_sliders()