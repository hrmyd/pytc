import pytc
import ipywidgets as widgets
from IPython.display import display, clear_output
import pandas as pd
from .exp import GlobalExp


class Sliders():
    def __init__(self, exp, fitter, gui, param_name):
        """
        """
        self._var_opt = {'link': ['blank'], 'unlink': ['unlink']}
        
        self._loc_link = widgets.Dropdown(value = self._var_opt['unlink'], options = self._var_opt)
        self._glob_link = widgets.Dropdown(value = self._loc_link.value[0], options = self._loc_link.value)
        self._fixed_check = widgets.Checkbox(description = 'Fix? ', value = False)
        self._slider = widgets.FloatSlider(description = 'Guess ')
        self._fixed_int = widgets.BoundedFloatText(description = 'F', display = 'none')
        self._s_min = widgets.FloatText(description = '∧')
        self._s_max = widgets.FloatText(description = '∨')
        self._all_widgets = widgets.VBox()
        
        self._exp = exp
        self._fitter = fitter
        self._gui = gui
        self._param_name = param_name
        
        self._fixed_check.layout.width = '80px'
        self._loc_link.layout.width = '200px'
        self._glob_link.layout.width = '200px'
        self._slider.layout.width = '300px'
        self._s_min.layout.width = '110px'
        self._s_max.layout.width = '110px'
        self._fixed_int.layout.width = '120px'
        self._fixed_int.layout.display = 'none'
    
    def logic(self):
        """
        handle trait changes for each widget and link to the fitter.
        """
    
        self._fixed_check.observe(self.check_change, 'value')
        self._loc_link.observe(self.link_change, 'value')
        self._s_min.observe(self.min_change, 'value')
        self._s_max.observe(self.max_change, 'value')
        self._slider.observe(self.param_change, 'value')
        
    def update_fit(self, fixed, guess, bounds_min, bounds_max, fixed_int):
        """
        """
        global_param, local_param = self._fitter.fit_param
        global_error, local_error = self._fitter.fit_error
        
        local_var = {}
        global_var = {}
        
        guess = self._exp.model.param_guesses[self._param_name]

        n=0
        for param, error in zip(local_param, local_error):
            for p, e in zip(param, error):
                local_var["{},{}".format(p, n)] = {'param': param[p], 'error': error[e]}
                #print("{},{}".format(p, n), ': ', param[p], error[e])
            n+=1

        for param, error in zip(global_param.keys(), global_error.keys()):
            global_var[param] = {'param': global_param[param], 'error': global_error[error]}
            #print(param, ': ', global_param[param], global_error[error])
            
        df1 = pd.DataFrame.from_dict(local_var, 'index')
        df2 = pd.DataFrame.from_dict(global_var, 'index')
        
        df1.append(df2)
        
        display(df1)
            
        self._fitter.fit()
        self._fitter.plot()
        
    def close_sliders(self):
        """
        """
        self._all_widgets.close()

    def min_change(self, min_val):
        """
        change minimum for fixed integer and slider widgets, update bounds and range for parameter.
        """
        self._slider.min = min_val['new']
        #self._fixed_int.min = min_val['new']
        self.update_bounds(self._slider.min, self._slider.max)

    def max_change(self, max_val):
        """
        change maximum for fixed integer and slider widgets, update bounds and range for parameter.
        """
        self._slider.max = max_val['new']
        #self._fixed_int.max = max_val['new']
        self.update_bounds(self._slider.min, self._slider.max)
        
    def update_bounds(self, s_min, s_max):
        """
        """
        pass

    def check_change(self, val):
        """
        update if parameter is fixed and change widget view
        """
        if val['new']:
            self._slider.layout.display = 'none'
            self._fixed_int.layout.display = ''
            self._fitter.fix(self._exp, **{self._param_name: self._fixed_int.value})
        elif val['new'] == False and self._loc_link.value == ['link']:
            self._slider.layout.display = 'none'
            self._fixed_int.layout.display = 'none'
            self._min_max.layout.display = 'none'
            self._bounds.layout.display = 'none'
            self._fitter.unfix(*[self._param_name], expt = self._exp)
        elif val['new'] == False and self._loc_link.value == ['unlink']: 
            self._slider.layout.display = ''
            self._fixed_int.layout.display = 'none'
            self._min_max.layout.display = ''
            self._bounds.layout.display = ''
            self._fitter.unfix(*[self._param_name], expt = self._exp)

        #fixed and update fixed

    def link_change(self, select):
        """
        update if parameter is linked or unlinked from a global parameter and update widget view
        """
        if select['new'] == ['unlink'] and self._fixed_check.value == False:
            self._slider.layout.display = ''
            self._fixed_int.layout.display = 'none'
            self._s_min.layout.display = ''
            self._s_max.layout.display = ''
            self._fixed_check.layout.display = ''
        elif select['new'] == ['unlink'] and self._fixed_check.value:
            self._slider.layout.display = 'none'
            self._fixed_int.layout.display = ''
            self._s_min.layout.display = ''
            self._s_max.layout.display = ''
            self._fixed_check.layout.display = ''
        else:
            self._slider.layout.display = 'none'
            self._fixed_int.layout.display = 'none'
            self._s_min.layout.display = 'none'
            self._s_max.layout.display = 'none'
            self._fixed_check.layout.display = 'none'
                
    def param_change(self, param_val):
        """
        update parameter value guess based on slider value
        """
        guess = param_val['new']
        
        self._fitter.update_guess(self._param_name, guess, self._exp)
    
    def build_sliders(self):
        """
        build sliders!
        """
        pass
        
class LocalSliders(Sliders):
    def __init__(self, exp, fitter, gui, param_name, global_vars, global_exp):
        super().__init__(exp, fitter, gui, param_name)
        
        self._global_vars = global_vars
        self._global_exp = global_exp
        
    def update_bounds(self, s_min, s_max):
        """
        update bound and range for the parameter
        """
        bounds = [s_min, s_max]
        self._fitter.update_bounds(self._param_name, bounds, self._exp)
        
        # check if bounds are smaller than range, then update.
        curr_range = self._exp.model.param_guess_ranges[self._param_name]
        curr_bounds = self._exp.model.bounds[self._param_name]
        
        if curr_range[0] < curr_bounds[0] or curr_range[1] > curr_bounds[1]:
            self._fitter.update_range(self._param_name, bounds, self._exp)
            
    def create_global(self, g):
        """
        link local parameter to global parameter, create new global experiment object, and generate new sliders.
        """
        if g != 'unlink' and g != 'blank':
            try:
                self._fitter.link_to_global(self._exp, self._param_name, g)
                if g not in self._global_exp:
                    new_global = GlobalExp(self._gui, self._global_exp, self._fitter, g)
                    self._global_exp[g] = new_global
                    new_global.gen_exp()
            except:
                pass
            
            self._fitter.fit()
            self._fitter.plot()
            

    def create_local(self, l):
        """
        update list of global variables and choose to link or unlink local parameter
        """

        self._var_opt['link'] = self._global_vars
        self._loc_link.options = self._var_opt
        
        if l[0] == 'unlink':
            try:
                self._fitter.unlink_from_global(self._exp, self._param_name)
            except: 
                pass
        else:
             self._glob_link.options = l
        
                
    def build_sliders(self):
        """
        """
        self.logic()
        
        exp_range = self._exp.model.param_guess_ranges[self._param_name]
        self._slider.min = exp_range[0]
        self._slider.max = exp_range[1]
        self._slider.value = self._exp.model.param_guesses[self._param_name]
        
        #self._fixed_int = exp_range[0]
        #self._fixed_int = exp_range[1]
        
        loc_inter = widgets.interactive(self.create_local, l = self._loc_link)
        glob_inter = widgets.interactive(self.create_global, g =  self._glob_link)
        
        main_interactive = widgets.interactive(self.update_fit,
                                               fixed = self._fixed_check,
                                               guess = self._slider,
                                               bounds_min = self._s_min,
                                               bounds_max = self._s_max,
                                               fixed_int = self._fixed_int,)
        
        children = main_interactive.children + (loc_inter, glob_inter)
        main = widgets.HBox(children = children)
        
        name_label = widgets.Label(value = "{}: ".format(self._param_name))
        
        self._all_widgets.children = [name_label, main]
        #self._all_widgets.layout.width = '90%'
        self._all_widgets.layout.margin = '0px 0px 20px 0px'

        display(self._all_widgets)
        
class GlobalSliders(Sliders):
    def __init__(self, exp, fitter, gui, param_name):
        super().__init__(exp, fitter, gui, param_name)
        
    def update_bounds(self, s_min, s_max):
        """
        update bound and range for global parameter
        """
        bounds = [s_min, s_max]
        self._fitter.update_bounds(self._param_name, bounds, self._exp)
        
        # check if bounds are smaller than range, then update.
        curr_range = self._fitter.param_ranges[0][self._param_name]
        curr_bounds = self._fitter.param_bounds[0][self._param_name]
        
        if curr_range[0] < curr_bounds[0] or curr_range[1] > curr_bounds[1]:
            self._fitter.update_range(self._param_name, bounds, self._exp)
               
    def build_sliders(self):
        """
        """
        self.logic()

        exp_range = self._fitter.param_ranges[0][self._param_name]
        self._slider.min = exp_range[0]
        self._slider.max = exp_range[1]
        self._slider.value = self._fitter.param_guesses[0][self._param_name]
        
        #self._fixed_int = exp_range[0]
        #self._fixed_int = exp_range[1]
        
        name_label = widgets.Label(value = "{}: ".format(self._param_name))
        
        main_interactive = widgets.interactive(self.update_fit,
                                               fixed = self._fixed_check,
                                               guess = self._slider,
                                               bounds_min = self._s_min,
                                               bounds_max = self._s_max,
                                               fixed_int = self._fixed_int,)
        
        main = widgets.HBox(children = main_interactive.children)
        
        self._all_widgets.children = [main]
        #self._all_widgets.layout.width = '90%'
        self._all_widgets.layout.margin = '0px 0px 20px 0px'

        display(self._all_widgets)