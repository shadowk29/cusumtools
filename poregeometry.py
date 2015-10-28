import numpy as np
from scipy.optimize import fsolve
import os
import tkFileDialog
import Tkinter as tk


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
        self.surface_conductance_default.set(4.572)
        self.surface_conductance = tk.Entry(self.param_frame, textvariable=self.surface_conductance_default)
        self.surface_conductance_label = tk.Label(self.param_frame, text='Surface Conductance (nS):')
        self.default_counterion_conductance_length = tk.DoubleVar()
        self.default_counterion_conductance_length.set(0)
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


        #pore calculation widgets
        self.calc_frame = tk.LabelFrame(parent,text='Pore Geometry')
        self.diameter_string = tk.StringVar()
        self.diameter_string.set('Waiting for Input')
        self.length_string = tk.StringVar()
        self.length_string.set('Waiting for Input')
        self.status = tk.StringVar()
        self.status.set('Waiting for Input')
        self.diameter_label=tk.Label(self.calc_frame,text='Diameter (nm):')
        self.length_label=tk.Label(self.calc_frame,text='Length (nm):')
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

        coefs = np.array([sigma**2*(g-b),\
                          4*sigma*mu_S*(g-b),\
                          sigma*beta*mu_q*(g-5*b) + sigma**2*D**2*(b+np.pi/4*(b-g)),\
                          4*beta*mu_q*mu_S*(g-b) + np.pi*sigma*D**2*mu_S*(b-g) + (np.pi/4-1)*sigma**2*D**2 + 3*sigma*beta*mu_q,\
                          np.pi*sigma*D**2*mu_S - 4*beta*mu_q*mu_S - np.pi/4*sigma**2*D**4*b + (np.pi+1)*sigma*b*D**2*beta*mu_q - 4*b*beta**2*mu_q**2])
        
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
        
        
        self.diameter_string.set(round(diameter,1))
        self.length_string.set(round(length,1))
        self.status.set(str(len(diameters))+' physical options found, showing largest')

def main():
    root=tk.Tk()
    App(root)
    root.mainloop()

    
if __name__ == "__main__":
    main()
