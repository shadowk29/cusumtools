import numpy as np
from scipy.optimize import fsolve
import os
import tkFileDialog
import Tkinter as tk

class CreateToolTip(object):
    '''
    create a tooltip for a given widget
    '''
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)

    def enter(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background='white', relief='solid', borderwidth=1,
                       font=("times", "8", "normal"))
        label.pack(ipadx=1)

    def close(self, event=None):
        if self.tw:
            self.tw.destroy()


class App(tk.Frame):
    def __init__(self, parent):
        #parameter entry widgets
        self.param_frame = tk.LabelFrame(parent,text='Pore Parameters')
        self.open_conductance = tk.Entry(self.param_frame)
        self.blocked_conductance = tk.Entry(self.param_frame)
        self.dna_diameter_default = tk.DoubleVar()
        self.dna_diameter_default.set(2.2)
        self.dna_diameter = tk.Entry(self.param_frame, textvariable=self.dna_diameter_default)
        self.conductivity = tk.Entry(self.param_frame)
        self.open_label=tk.Label(self.param_frame,text='Open Conductance (nS):')
        self.blocked_label=tk.Label(self.param_frame,text='Blocked Conductance (nS):')
        self.dna_label=tk.Label(self.param_frame,text='DNA diameter (nm):')
        self.guess_label=tk.Label(self.param_frame,text='Diameter Guess (nm):')
        self.conductivity_label = tk.Label(self.param_frame,text='Conductivity (nS/nm):')
        self.surface_conductance_default = tk.DoubleVar()
        self.surface_conductance_default.set(2.34)
        self.surface_conductance = tk.Entry(self.param_frame, textvariable=self.surface_conductance_default)
        self.surface_conductance_label = tk.Label(self.param_frame, text='Surface Conductance (nS):')
        self.default_counterion_conductance_length = tk.DoubleVar()
        self.default_counterion_conductance_length.set(-17.595)
        self.counterion_conductance_length = tk.Entry(self.param_frame, textvariable=self.default_counterion_conductance_length)
        self.default_counterion_conductance_length_label = tk.Label(self.param_frame, text=u'Counterion Conductance (nS\u00B7nm):')
        self.screening_factor_default = tk.DoubleVar()
        self.screening_factor_default.set(0)
        self.screening_factor = tk.Entry(self.param_frame, textvariable=self.screening_factor_default)
        self.screening_factor_label = tk.Label(self.param_frame, text='Screening Factor:')

        self.param_frame.grid(row=0,column=0,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W)
        self.open_conductance.grid(row=0,column=1,sticky=tk.E+tk.W)
        self.blocked_conductance.grid(row=1,column=1,sticky=tk.E+tk.W)
        self.dna_diameter.grid(row=2,column=1,sticky=tk.E+tk.W)
        self.conductivity.grid(row=3,column=1,sticky=tk.E+tk.W)
        self.open_label.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.blocked_label.grid(row=1,column=0,sticky=tk.E+tk.W)
        self.dna_label.grid(row=2,column=0,sticky=tk.E+tk.W)
        self.conductivity_label.grid(row=3,column=0,sticky=tk.E+tk.W)
        self.surface_conductance_label.grid(row=4,column=0,sticky=tk.E+tk.W)
        self.surface_conductance.grid(row=4,column=1,sticky=tk.E+tk.W)
        self.default_counterion_conductance_length_label.grid(row=5,column=0,sticky=tk.E+tk.W)
        self.counterion_conductance_length.grid(row=5,column=1,sticky=tk.E+tk.W)
        self.screening_factor_label.grid(row=6,column=0,sticky=tk.E+tk.W)
        self.screening_factor.grid(row=6,column=1,sticky=tk.E+tk.W)

        CreateToolTip(self.open_conductance, 'Open pore conductance (nS)')
        CreateToolTip(self.blocked_conductance, 'Residual conductance (nS)')
        CreateToolTip(self.dna_diameter, 'Diameter of analyte (nm)')
        CreateToolTip(self.conductivity, 'Electrolyte conductivity (nS/nm)')
        CreateToolTip(self.surface_conductance, 'Product of pore surface charge and counterion mobility - 4.572 for KCl, 2.34 for LiCl (nS)')
        CreateToolTip(self.counterion_conductance_length, u'Product of linear charge density of analyte and counterion mobility (nS\u00B7nm)')
        CreateToolTip(self.screening_factor, 'Fractional reduction in counterion cloud')


        #pore calculation widgets
        self.calc_frame = tk.LabelFrame(parent,text='Pore Geometry')
        self.diameter_string = tk.StringVar()
        self.diameter_string.set('Waiting for Input')
        self.length_string = tk.StringVar()
        self.length_string.set('Waiting for Input')
        self.status = tk.StringVar()
        self.status.set('Waiting for Input')
        self.diameter_label=tk.Label(self.calc_frame,text='Diameter:')
        self.length_label=tk.Label(self.calc_frame,text='Length:')
        self.diameter_display = tk.Label(self.calc_frame,textvariable=self.diameter_string)
        self.length_display = tk.Label(self.calc_frame,textvariable=self.length_string)
        self.calculate_button = tk.Button(self.calc_frame,text='Calculate',command=self.pore_geometry)
        self.status_label=tk.Label(self.calc_frame,textvariable=self.status)

        self.calc_frame.grid(row=0,column=2,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W)
        self.diameter_label.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.length_label.grid(row=1,column=0,sticky=tk.E+tk.W)
        self.diameter_display.grid(row=0,column=1,sticky=tk.E+tk.W)
        self.length_display.grid(row=1,column=1,sticky=tk.E+tk.W)
        self.calculate_button.grid(row=2,column=0,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W)
        self.status_label.grid(row=3,column=0,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W)

        CreateToolTip(self.calculate_button, 'Using model from Carlsen et al. ACS Nano (2014) 8(5)')

    def pore_geometry(self):
        try:
            sigma = float(self.conductivity.get())
            G = float(self.open_conductance.get())
            B = float(self.blocked_conductance.get())
            D = float(self.dna_diameter.get())
            mu_S = float(self.surface_conductance.get())
            mu_q = float(self.counterion_conductance_length.get())
            beta = float(self.screening_factor.get())
        
        except ValueError:
            self.status.set('Fill in all fields')
            return
        g = sigma/G
        b = sigma/B

        coefs = np.array([sigma**2.0*(g-b),\
                          4.0*sigma*mu_S*(g-b),\
                          sigma*beta*mu_q*(g-5.0*b) + sigma**2.0*D**2.0*(b+np.pi/4.0*(b-g)),\
                          4.0*beta*mu_q*mu_S*(g-b) + np.pi*sigma*D**2.0*mu_S*(b-g) + (np.pi/4.0-1.0)*sigma**2.0*D**2.0 + 3.0*sigma*beta*mu_q,\
                          np.pi*sigma*D**2.0*mu_S - 4.0*beta*mu_q*mu_S - np.pi/4.0*sigma**2.0*D**4.0*b + (np.pi+1.0)*sigma*b*D**2.0*beta*mu_q - 4.0*b*beta**2.0*mu_q**2.0])
        
        roots = np.roots(coefs)
        real_roots = roots[np.isreal(roots)]
        diameters = np.real(real_roots[real_roots > 0])
        
        all_lengths = np.pi/4.0*(diameters**2*g-diameters)*(1+4*mu_S/(sigma*diameters))
        valid = [all_lengths > 0]
        diameters = diameters[valid]
        lengths = all_lengths[valid]
        location = np.argmax(diameters)
        diameter = diameters[location]
        length = lengths[location]
        
        
        self.diameter_string.set(str(round(diameter,1))+' nm')
        self.length_string.set(str(round(length,1))+' nm')
        self.status.set(str(len(diameters))+' physical options found, showing largest')

def main():
    root=tk.Tk()
    App(root)
    root.mainloop()

    
if __name__ == "__main__":
    main()
