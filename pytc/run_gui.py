import pytc
import ipywidgets as widgets

from IPython.display import display, clear_output
from IPython.html.widgets import interactive

exp_w = []
f = pytc.GlobalFit()
gui = Interface(f)

def rm_last(b):

    if exp_w:
        last_exp = exp_w[-1]
        last_exp[1].close()
        try:
            gui.remove_experiment(last_exp[0].exp_id())
        except:
            pass

        exp_w.remove(last_exp)

def gen_exp(b):
    
    gui.reset_sliders()
    clear_output()
    
    for i in exp_w:
        if len(exp_w) > len(gui.view_exp()):
            try:
                exp = i[0]
                exp.link_exp()

                gui.add_experiment(exp.exp_id())
                
                # generate sliders here, update experiment view, something like...
                
                param = i[0].parameters()
                name = param["name"]
                
                print(name)
                
            except:
                print("no data added.")
        else:
            pass

        #f.link_to_global(exp, "dilution_heat", "global_heat")
        #f.link_to_global(exp, "dilution_intercept", "global_intercept")

    gui.build_interface()
    gui.get_param()

def clear_exp(b):

    for i in exp_w:
        try:
            i[1].close()
            gui.remove_experiment(i[0].exp_id())
        except:
            pass
        
        exp_w.remove(i)
        
    gui.reset_sliders()
    
    clear_output()


def add_field(b):
    
    clear_output()
    gui.reset_sliders()
    exp_object = Experiments(gui, exp_w, f)
    show = exp_object.gen_exp()

    exp_w.append([exp_object, show])

    display(show)
        
    # true false??? each time add_field clicked set true, each time analyze clicked set false.
        
ENTRY_W = '200px'

add_exp_field_b = widgets.Button(description = "Add an Experiment")
add_exp_field_b.layout.width = ENTRY_W
add_exp_field_b.on_click(add_field)

rmv_last_field = widgets.Button(description = "Remove Last Experiment")
rmv_last_field.layout.width = ENTRY_W
rmv_last_field.on_click(rm_last)

exp_object = Experiments(gui, exp_w, f)
show = exp_object.gen_exp()

exp_w.append([exp_object, show])

analyze_widget = widgets.Button(description = "Analyze")
analyze_widget.on_click(gen_exp)

clear_widget = widgets.Button(description = "Clear", value = False)
clear_widget.on_click(clear_exp)

experiments_layout = widgets.Layout(display = "flex", 
                      flex_flow = "row", 
                      align_items = "stretch")

experiments = widgets.Box(children = [add_exp_field_b, rmv_last_field], 
                                      layout = experiments_layout)
parent = widgets.Box(children = [analyze_widget, clear_widget, experiments, show])

display(parent)