import pytc
import ipywidgets as widgets

from IPython.display import display, clear_output
from IPython.html.widgets import interactive

class ParamCollect():
    def __init__(self, gui, container, fitter):
        
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
        
    def remove_exp(self, b):
        """
        remove experiment from analysis and close widgets
        """
        try:
            self._gui.remove_experiment(self._exp_id)
        except:
            clear_output()
            print("no experiment linked")
        
        self._widgets[3].close()
        
        for i in self._container:
            if self._exp_id == i[0]._exp_id:
                self._container.remove(i)
    
    def parameters(self):
        """
        get parameters for experiment
        """
        pass
        
    def link_exp(self):
        """
        create a new pytc experiment
        """
        self._exp_val = self._widgets[0].value
        if self._exp_val:
            model = self._widgets[1].value
            self._exp_id = pytc.ITCExperiment(self._exp_val, model)
            self.parameters()
        else:
            clear_output()
            print("no exp data given")
            
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
    
class Experiments(ParamCollect):
    """
    create experiment object and generate widgets
    """
    def __init__(self, gui, container, fitter):
        super().__init__(gui, container, fitter)
    
    def parameters(self):
        """
        generate local parameters for experiment.
        """
        
        global_param, local_param = self._fitter.param_names
        global_guesses, local_guesses = self._fitter.param_guesses
        global_ranges, local_ranges = self._fitter.param_ranges
        global_fixed, local_fixed = self._fitter.fixed_param 
        
        self._parameters = {"name": local_param, 
                            "value": local_guesses, 
                            "ranges": local_ranges, 
                            "fixed": local_fixed}
        
        return self._parameters
    
    def gen_sliders(self):
        """
        generate sliders for each experiment, give option to link to global.
        """
        
        pass
    
    def gen_exp(self):
        """
        generate widgets for experiment.
        """
        exp_field = widgets.Text(description = "exp: ")
        model_drop = widgets.Dropdown(options = self._models, value = self._models["blank"])

        rm_exp = widgets.Button(description = "remove experiment")
        rm_exp.on_click(self.remove_exp)

        exp_box = widgets.HBox(children = [exp_field, model_drop, rm_exp])
        self._widgets.extend([exp_field, model_drop, rm_exp, exp_box])
        
        return exp_box


class Interface:
    
    def __init__(self,fitter):
        """
        """
        
        self._global_sliders = {}
        self._local_sliders = []
        self._fitter = fitter
        self._experiments = []
        
    def view_exp(self):
        
        return self._experiments
    
    def add_experiment(self,expt):
        
        self._fitter.add_experiment(expt)
        self._experiments.append(expt)
        
    def remove_experiment(self, expt):
        
        self._fitter.remove_experiment(expt)
        self._experiments.remove(expt)
            
    def reset_sliders(self):
        
        for i in self._local_sliders:
            for slider in i:
                i[slider].close()
            i.clear()
    
    def build_interface(self):
        """
        """

        global_param, local_param = self._fitter.param_names
        global_guesses, local_guesses = self._fitter.param_guesses
        global_ranges, local_ranges = self._fitter.param_ranges
        global_fixed, local_fixed = self._fitter.fixed_param 
        
        all_widgets = {}
        
        for p in global_param:
        
            g_min = global_ranges[p][0]
            g_max = global_ranges[p][1]
            g_val = global_guesses[p]
            
            self._global_sliders[p] = widgets.FloatSlider(min=g_min,max=g_max,value=g_val)
            
            all_widgets["{}".format(p)] = self._global_sliders[p]
    
        for i in range(len(self._experiments)):            
            
            self._local_sliders.append({})
        
            for p in local_param[i]:
            
                g_min = local_ranges[i][p][0]
                g_max = local_ranges[i][p][1]
                g_val = local_guesses[i][p]
                
                self._local_sliders[-1][p] = widgets.FloatSlider(min=g_min,max=g_max,value=g_val)
        
                all_widgets["{},{}".format(p,i)] = self._local_sliders[-1][p]

        w = widgets.interactive(self._update,**all_widgets)
                        
        display(w)

    def _update(self,**kwargs):
        """
        """
        
        for k in kwargs.keys():
            if len(k.split(",")) == 1:
                self._fitter.update_guess(k,kwargs[k])
            else:
                
                param_name = k.split(",")[0]
                expt = self._experiments[int(k.split(",")[1])]
                self._fitter.update_guess(param_name,kwargs[k],expt)
       
        self._fitter.fit()
        self._fitter.plot()
        
        
    def get_param(self):
        
        print(self._fitter.fit_param)