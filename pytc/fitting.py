__description__ = \
"""
fitting.py

Classes for doing nonlinear regression of global models against multiple ITC
experiments.
"""
__author__ = "Michael J. Harms"
__date__ = "2016-06-22"

import copy, inspect, warnings
import numpy as np
import scipy.optimize as optimize
from matplotlib import pyplot as plt
import seaborn as sns

class GlobalFit:
    """
    Class for regressing some binding model against an arbitrary number of 
    ITC experiments.
    """

    def __init__(self): 
        """
        Set up the main binding model to fit.
        """

        # Objects for holding global parameters
        self._global_param_names = []
        self._global_param_guesses = {}
        self._global_param_ranges = {}
        self._global_param_alias_mapping = {}
        self._global_fixed_param = {}

        # List of experiments and the weight to apply for each experiment
        self._experiment_dict = {}
        self._exp_weights = {}
        self._expt_list_stable_order = []

    def add_experiment(self,experiment,param_guesses=None,
                       fixed_param=None,param_aliases=None,weight=1.0):
        """
        experiment: an initialized ITCExperiment instance
        param_guesses: a dictionary of parameter guesses (need not be complete)
        fixed_param: a dictionary of parameters to be fixed, with value being
                     fixed_value. 
        param_aliases: dictionary keying local experiment parameters to global
                       parameters.
        weight: how much to weight this experiment in the regression relative to other
                experiments.  Values <1.0 weight this experiment less than others; 
                values >1.0 weight this more than others.
        """
        
        name = experiment.experiment_id    

        # Record the experiment
        self._experiment_dict[name] = experiment
        self._exp_weights[name] = weight
        self._expt_list_stable_order.append(name)

        if param_guesses != None:
            self._experiment_dict[name].update_guesses(param_guesses)
       
        if fixed_param != None:
            self._experiment_dict[name].update_fixed(fixed_param)        

        if param_aliases != None:
            for p in param_aliases:
                self.link_to_global(-1,p,param_aliases[p])


    def remove_experiment(self,expt):
        """
        Remove an experiment from the analysis.  This is done using the 
        experiment number.  
        """
        
        expt_name = expt.experiment_id

        # Go through all global parameters
        for k in self._global_param_alias_mapping.keys():
    
            # If the experiment links to that
            for expt in self._global_param_alias_mapping[k]:
                if expt_name == expt[0]:
                    self._global_param_alias_mapping[k].remove(expt)
                
                    if len(self._global_param_alias_mapping[k]) == 0:
                        self.remove_global(k)

        self._experiment_dict.pop(expt_name)
        self._expt_list_stable_order.remove(expt_name)
                          
    def link_to_global(self,expt,expt_param,global_param_name):
        """
        Link a local experimental fitting parameter to a global fitting
        parameter.
        """

        expt_name = expt.experiment_id

        # Make sure the experimental paramter is actually in the experiment
        if expt_param not in self._experiment_dict[expt_name].model.param_names:
            err = "Parameter {} not in experiment {}\n".format(expt_param,expt_name)
            raise ValueError(err)

        # Update the alias from the experiment side
        self._experiment_dict[expt_name].model.update_aliases({expt_param:
                                                                 global_param_name})

        e = self._experiment_dict[expt_name]         
        if global_param_name not in self._global_param_names:
        
            # Update the alias from the global fitting side 
            self._global_param_names.append(global_param_name)
            self._global_param_guesses[global_param_name] = e.model.param_guesses[expt_param]
            self._global_param_alias_mapping[global_param_name] = [(expt_name,expt_param)]
            try:
                self._global_fixed_param[global_param_name] = e.model.fixed_param[expt_param]
            except KeyError:
                pass

            self._global_param_ranges[global_param_name] = e.model.param_ranges[expt_param]

        else:

            # Only add link between experiment and the global guess if the link is
            # not already recorded.
            if expt_name not in [m[0] for m in self._global_param_alias_mapping[global_param_name]]:
                self._global_param_alias_mapping[global_param_name].append((expt_name,expt_param))

    def unlink_from_global(self,expt,expt_param,global_param_name):
        """
        Remove the link between a local fitting parameter and a global
        fitting parameter.
        """

        expt_name = expt.experiment_id

        # Make sure the experimental paramter is actually in the experiment
        if expt_param not in self._experiment_dict[expt_name].model.param_names:
            err = "Parameter {} not in experiment {}\n".format(expt_param,expt_name)
            raise ValueError(err)

        # Make sure global name is actually seen
        if global_param_name not in self._global_param_names:
            err = "global parameter {} not found\n".format(global_param_name)
            raise ValueError(err)
    
        # remove global --> expt link 
        self._global_param_alias_mapping[global_param_name].remove((expt_name,expt_param))
        if len(self._global_param_alias_mapping[global_param_name]) == 0:
            self.remove_global(global_param_name)

        # remove expt --> global link 
        self._experiment_dict[expt_name].model.update_aliases({expt_param:None})
 
    
    def remove_global(self,global_param_name):
        """
        Remove a global parameter, unlinking all local parameters. 
        """
           
        if global_param_name not in self._global_param_names:
            err = "Global parameter {} not defined.\n".format(global_param_name)
            raise ValueError(err)

        # Remove expt->global mapping from each experiment
        for k in self._global_param_alias_mapping.keys():

            for expt in self._global_param_alias_mapping[k]:

                expt_name = expt[0]
                expt_params = self._experiment_dict[expt_name].model.param_aliases.keys()
                for p in expt_params:
                    if self._experiment_dict[expt_name].model.param_aliases[p] == global_param_name:
                        self._experiment_dict[expt_name].model.update_aliases({p:None})
                        break
     
        # Remove global data 
        self._global_param_names.remove(global_param_name)
        self._global_param_guesses.pop(global_param_name)
        self._global_param_ranges.pop(global_param_name)
        self._global_param_alias_mapping.pop(global_param_name)

        try:
            self._global_fixed_param.pop(global_param_name)
        except KeyError:
            pass

 
    def _call_dq(self,expt_name,param):
        """
        Call the dQ method for experiment i, mapping global parameters to local
        parameters and fixing specified parameters.
        """
   
        e = self._experiment_dict[expt_name]
 
        model_param_kwarg = dict([(p,param[self._name_to_index[(expt_name,p)]])
                                  for p in e.model.param_names])
        return e.model_dq(**model_param_kwarg)

    def _residuals(self,param):
        """
        Determine the residuals between the global model and all experiments.
        """
        
        all_residuals = []
        
        # Calculate residuals for each experiment
        for expt_name in self._experiment_dict.keys():
      
            calc = self._call_dq(expt_name,param)
 
            # add to the total set of residuals
            all_residuals.extend(self._exp_weights[expt_name]*(self._experiment_dict[expt_name].heats - calc))

        return np.array(all_residuals)

    
    def fit(self):
        """
        Perform a global fit using nonlinear regression.
        """

        # Some sanity checking
        if len(self._experiment_dict) == 0:
            warn = "No experiments loaded.  Fit is trivial.\n"
            warnings.warn(warn)

        # Create a map between complex parameter names (some local, some global,
        # all keyed by local parameter names) and a fitting vector
        self._name_to_index = {}

        # Global parameters first
        index_counter = 0
        guesses = []
        for p in self._global_param_names:
            self._name_to_index[p] = index_counter
            guesses.append(self._global_param_guesses[p])
            index_counter += 1

        # Go through individual experiments
        for expt_name in self._experiment_dict.keys():
          
            e = self._experiment_dict[expt_name] 
            for p in e.model.param_names:

                # If it's a local parameter...
                if p not in list(e.model.param_aliases.keys()):
                    self._name_to_index[(expt_name,p)] = index_counter
                    guesses.append(e.model.param_guesses[p])
                    index_counter += 1

                # Global parameters
                else:
                    g_name = e.model.param_aliases[p]
                    self._name_to_index[(expt_name,p)] = self._name_to_index[g_name]

        # fit_param_array holds the parameter values that will be fit by 
        # nonlinear regression
        fit_param_array = np.array(guesses,dtype=float)
        
        # Set starting value for fit
        self._fit_param = fit_param_array
 
        # Do the actual fit
        fit_param, covariance, info_dict, message, error = optimize.leastsq(self._residuals,
                                                                            x0=fit_param_array,
                                                                            full_output=True)
        # Store the result
        self._fit_param = fit_param

    
    def plot(self,color_list=None):
        """
        Plot the experimental data and fit results.
        """
       
        # Only make a plot if the fit has already been run 
        try:
            self._fit_param
        except AttributeError:
            warn = "Fit has not yet been run.  No plot generated."
            warnings.warn(warn)
            return      
 
        if color_list == None:
            N = len(self._experiment_dict)
            color_list = [plt.cm.brg(i/N) for i in range(N)]
        
        if len(color_list) < len(self._experiment_dict):
            err = "Number of specified colors is less than number of experiments.\n"
            raise ValueError(err)
        
        for i, expt_name in enumerate(self._experiment_dict.keys()):
           
            e = self._experiment_dict[expt_name] 
            calc = self._call_dq(expt_name,self._fit_param)

            #sns.lmplot(e.mole_ratio, e.heats)
 
            plt.plot(e.mole_ratio,e.heats,"o",color=color_list[i])
            plt.plot(e.mole_ratio,calc,color=color_list[i],linewidth=1.5)

    @property
    def fit_param(self):
        """
        Return the fit results as a dictionary that keys parameter name to fit
        value.  This is a tuple with global parameter first, then a list of 
        dictionaries for each local fit. 
        """

        # Global parameters
        global_out_param = {}
        for g in self._global_param_names:
            global_out_param[g] = self._fit_param[self._name_to_index[g]]

        # Local parameters
        local_out_param = []
        for expt_name in self._expt_list_stable_order:
            e = self._experiment_dict[expt_name]

            local_out_param.append({})
            for p in e.model.param_names:
                if p not in e.model.param_aliases:
                    local_out_param[-1][p] = self._fit_param[self._name_to_index[(expt_name,p)]]

        return global_out_param, local_out_param


    #--------------------------------------------------------------------------
    # parameter names  
            
    @property
    def param_names(self):
        """
        Return parameter names. This is a tuple of global names and then a list
        of parameter names for each experiment.
        """

        final_param_names = [] 
        for expt_name in self._expt_list_stable_order:
            e = self._experiment_dict[expt_name]

            param_names = copy.deepcopy(e.model.param_names)
          
            # Part of the global command names. 
            for k in e.model.param_aliases.keys():
                param_names.remove(k)
             
            final_param_names.append(param_names)

        return self._global_param_names, final_param_names  

    #--------------------------------------------------------------------------
    # parameter guesses
         
    @property
    def param_guesses(self):
        """
        Return parameter guesses. This is a tuple of global names and then a list
        of parameter guesses for each experiment.
        """
        
        final_param_guesses = [] 
        for expt_name in self._expt_list_stable_order:
            e = self._experiment_dict[expt_name]
            param_guesses = copy.deepcopy(e.model.param_guesses)

            for k in e.model.param_aliases.keys():
                param_guesses.pop(k)

            final_param_guesses.append(param_guesses)

        return self._global_param_guesses, final_param_guesses

    def update_guess(self,param_name,param_guess,expt=None):
        """
        Update the one of the guesses for this fit.  If the experiment is None,
        set a global parameter.  Otherwise, set the specified experiment.

            param_name: name of parameter to set
            param_guess: value to set parameter to
            expt_name: name of experiment

        """
  
        if expt == None:
            self._global_param_guesses[param_name] = param_guess
        else:
            self._experiment_dict[expt.experiment_id].model.param_guesses[param_name] = param_guess 
           
    #--------------------------------------------------------------------------
    # parameter ranges 

    @property
    def param_ranges(self):
        """
        Return the parameter ranges for each fit parameter. This is a tuple.  
        Global parameters are first, a list of local parameter ranges are next.
        """

        final_param_ranges = [] 
        for expt_name in self._expt_list_stable_order:
            e = self._experiment_dict[expt_name]
            param_ranges = copy.deepcopy(e.model.param_ranges)

            for k in e.model.param_aliases.keys():
                param_ranges.pop(k)

            final_param_ranges.append(param_ranges)

        return self._global_param_ranges, final_param_ranges

    #--------------------------------------------------------------------------
    # fixed parameters 
        
    @property
    def fixed_param(self):
        """
        Return the fixed parameters of the fit.  This is a tuple,  Global fixed
        parameters are first, a list of local fixed parameters is next.
        """

        final_fixed_param = [] 
        for expt_name in self._expt_list_stable_order:
            e = self._experiment_dict[expt_name]

            fixed_param = copy.deepcopy(e.model.fixed_param)

            for k in e.model.param_aliases.keys():
                try:
                    fixed_param.pop(k)
                except KeyError:
                    pass

            final_fixed_param.append(fixed_param)

        return self._global_fixed_param, final_fixed_param
        
    #--------------------------------------------------------------------------
    # parameter aliases
 
    @property
    def param_aliases(self):
        """
        Return the parameter aliases.  This is a tuple.  The first entry is a 
        dictionary of gloal parameters mapping to experiment number; the second
        is a map between experiment number and global parameter names.
        """

        expt_to_global = []
        for expt_name in self._expt_list_stable_order:
            e = self._experiment_dict[expt_name]
            expt_to_global.append(copy.deepcopy(e.model.param_aliases))

       
        return self._global_param_alias_mapping, expt_to_global

    @property
    def experiments(self):
        """
        Return a list of associated experiments.
        """

        out = []
        for expt_name in self._expt_list_stable_order:
            out.append(self._experiment_dict[expt_name])

        return out 
