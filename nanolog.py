##                                COPYRIGHT
##    Copyright (C) 2016 Kyle Briggs (kbrig035<at>uottawa.ca)
##
##    This file is part of NanoLog.
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import tkFileDialog
import Tkinter as tk
import datetime
import pandas as pd
from collections import OrderedDict

class LogGUI(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        ##### Define all widgets and frames displayed in the GUI, and bind appropriate variables ######


        ##### defines widgets for loading presets ##########
        self.loadopts_frame = tk.LabelFrame(parent,text='Options') 
        self.load_default = tk.Button(self.loadopts_frame, text='Load Standard',command=self.load_standard)
        self.load_last = tk.Button(self.loadopts_frame, text='Load Last',command=self.load_last)


        ##### define widgets for identification information ##########
        self.id_frame = tk.LabelFrame(parent,text='Identification Parameters') 
        self.name = tk.Entry(self.id_frame)
        self.name_label = tk.Label(self.id_frame,text='Name: ')
        self.date_string = tk.StringVar()
        self.date = tk.Entry(self.id_frame,textvariable=self.date_string)
        self.date_label = tk.Label(self.id_frame,text='Date: ')
        self.id = tk.Entry(self.id_frame)
        self.id_label = tk.Label(self.id_frame,text='Pore ID: ')
        self.supplier_set = tk.StringVar()
        self.supplier = tk.Entry(self.id_frame, textvariable=self.supplier_set)
        self.supplier_label = tk.Label(self.id_frame,text='Supplier: ')
        self.batch = tk.Entry(self.id_frame)
        self.batch_label = tk.Label(self.id_frame,text='Batch: ')


        ##### defines widgets for fabrication information ##########
        self.fab_frame = tk.LabelFrame(parent,text='Fabrication Parameters') 
        
        self.fab_electrolyte_set = tk.StringVar()
        self.fab_electrolyte = tk.Entry(self.fab_frame, textvariable=self.fab_electrolyte_set)
        self.fab_electrolyte_label = tk.Label(self.fab_frame,text='Salt: ')

        self.fab_molarity_set = tk.DoubleVar()
        self.fab_molarity_set.set('')
        self.fab_molarity = tk.Entry(self.fab_frame, textvariable=self.fab_molarity_set)
        self.fab_molarity_label = tk.Label(self.fab_frame,text='Molarity: ')

        self.fab_pH_set = tk.DoubleVar()
        self.fab_pH_set.set('')
        self.fab_pH = tk.Entry(self.fab_frame, textvariable=self.fab_pH_set)
        self.fab_pH_label = tk.Label(self.fab_frame,text='pH: ')

        self.fab_voltage_set = tk.DoubleVar()
        self.fab_voltage_set.set('')
        self.fab_voltage = tk.Entry(self.fab_frame, textvariable=self.fab_voltage_set)
        self.fab_voltage_label = tk.Label(self.fab_frame,text='Voltage: ')

        self.fab_thickness_set = tk.DoubleVar()
        self.fab_thickness_set.set('')
        self.fab_thickness = tk.Entry(self.fab_frame, textvariable=self.fab_thickness_set)
        self.fab_thickness_label = tk.Label(self.fab_frame,text='Thickness: ')

        self.fab_time = tk.Entry(self.fab_frame)
        self.fab_time_label = tk.Label(self.fab_frame,text='Duration: ')


        #####defines widgets for conditioning information##########
        self.cond_frame = tk.LabelFrame(parent,text='Conditioning Parameters')

        self.cond_electrolyte_set = tk.StringVar()
        self.cond_electrolyte = tk.Entry(self.cond_frame, textvariable=self.cond_electrolyte_set)
        self.cond_electrolyte_label = tk.Label(self.cond_frame,text='Salt: ')

        self.cond_molarity_set = tk.DoubleVar()
        self.cond_molarity_set.set('')
        self.cond_molarity = tk.Entry(self.cond_frame, textvariable=self.cond_molarity_set)
        self.cond_molarity_label = tk.Label(self.cond_frame,text='Molarity: ')

        self.cond_pH_set = tk.DoubleVar()
        self.cond_pH_set.set('')
        self.cond_pH = tk.Entry(self.cond_frame, textvariable=self.cond_pH_set)
        self.cond_pH_label = tk.Label(self.cond_frame,text='pH: ')

        self.cond_voltage_set = tk.DoubleVar()
        self.cond_voltage_set.set('')
        self.cond_voltage = tk.Entry(self.cond_frame, textvariable=self.cond_voltage_set)
        self.cond_voltage_label = tk.Label(self.cond_frame,text='Voltage: ')

        self.cond_time = tk.Entry(self.cond_frame)
        self.cond_time_label = tk.Label(self.cond_frame,text='Duration: ')

        
        self.cond_size = tk.Entry(self.cond_frame)
        self.cond_size_label = tk.Label(self.cond_frame,text='Target Size: ')


        ########## defines widgets for measurement information ##########
        self.measure_frame = tk.LabelFrame(parent,text='Measurement Parameters')

        self.measure_electrolyte_set = tk.StringVar()
        self.measure_electrolyte = tk.Entry(self.measure_frame, textvariable=self.measure_electrolyte_set)
        self.measure_electrolyte_label = tk.Label(self.measure_frame,text='Salt: ')

        self.measure_molarity_set = tk.DoubleVar()
        self.measure_molarity_set.set('')
        self.measure_molarity = tk.Entry(self.measure_frame, textvariable=self.measure_molarity_set)
        self.measure_molarity_label = tk.Label(self.measure_frame,text='Molarity: ')

        self.measure_pH_set = tk.DoubleVar()
        self.measure_pH_set.set('')
        self.measure_pH = tk.Entry(self.measure_frame, textvariable=self.measure_pH_set)
        self.measure_pH_label = tk.Label(self.measure_frame,text='pH: ')

        self.measure_size = tk.Entry(self.measure_frame)
        self.measure_size_label = tk.Label(self.measure_frame,text='Final Size: ')

        self.measure_noise = tk.Entry(self.measure_frame)
        self.measure_noise_label = tk.Label(self.measure_frame,text='1Hz PSD: ')

        self.measure_rect = tk.Entry(self.measure_frame)
        self.measure_rect_label = tk.Label(self.measure_frame,text='Rectification: ')


        ##### widgets to describe details of the experimental outcome #######
        self.outcome_frame = tk.LabelFrame(parent,text='Outcome') 
        self.outcome = tk.IntVar()
        self.outcome.set(-1)
        self.outcome_success = tk.Radiobutton(self.outcome_frame, text='Success', variable = self.outcome, value=0, indicatoron=0, command=self.grey_success)
        self.outcome_salvage = tk.Radiobutton(self.outcome_frame, text='Salvaged', variable = self.outcome, value=1, indicatoron=0, command=self.grey_salvage)
        self.outcome_failure = tk.Radiobutton(self.outcome_frame, text='Failure', variable = self.outcome, value=2, indicatoron=0, command=self.grey_failure)


        ###### widgets to describe standard successful interventions ######
        self.intervention_frame = tk.LabelFrame(parent,text='Steps Taken to Salvage') 
        self.si_false_pos = tk.IntVar()
        self.si_false_neg = tk.IntVar()
        self.si_sw_crash = tk.IntVar()
        self.si_aging = tk.IntVar()
        self.si_electrode = tk.IntVar()
        self.si_op_amp = tk.IntVar()
        self.si_false_pos_check = tk.Checkbutton(self.intervention_frame, text="False Positive(s)", variable=self.si_false_pos,command=self.check_enable_submit)
        self.si_false_neg_check = tk.Checkbutton(self.intervention_frame, text="False Negative(s)", variable=self.si_false_neg,command=self.check_enable_submit)
        self.si_sw_crash_check = tk.Checkbutton(self.intervention_frame, text="Software Crash", variable=self.si_sw_crash,command=self.check_enable_submit)
        self.si_aging_check = tk.Checkbutton(self.intervention_frame, text="Pore aging", variable=self.si_aging,command=self.check_enable_submit)
        self.si_electrode_check = tk.Checkbutton(self.intervention_frame, text="Electrode Fix", variable=self.si_electrode,command=self.check_enable_submit)
        self.si_op_amp_check = tk.Checkbutton(self.intervention_frame, text="Op Amp Fix", variable=self.si_op_amp,command=self.check_enable_submit)
        

        ##### widgets to describe standard modes of failure #######
        self.failure_frame = tk.LabelFrame(parent,text='Reasons for Failure') 
        self.f_false_pos = tk.IntVar()
        self.f_false_neg = tk.IntVar()
        self.f_unstable = tk.IntVar()
        self.f_broken = tk.IntVar()
        self.f_noise = tk.IntVar()
        self.f_wet = tk.IntVar()
        self.f_op_amp = tk.IntVar()
        self.f_oversize = tk.IntVar()
        self.f_crash = tk.IntVar()


        self.f_false_pos_check = tk.Checkbutton(self.failure_frame, text="False Positive(s)", variable=self.f_false_pos,command=self.check_enable_submit)
        self.f_false_neg_check = tk.Checkbutton(self.failure_frame, text="False Negative(s)", variable=self.f_false_neg,command=self.check_enable_submit)
        self.f_unstable_check = tk.Checkbutton(self.failure_frame, text="Unstable", variable=self.f_unstable,command=self.check_enable_submit)
        self.f_broken_check = tk.Checkbutton(self.failure_frame, text="Broken Membrane", variable=self.f_broken,command=self.check_enable_submit)
        self.f_noise_check = tk.Checkbutton(self.failure_frame, text="Too Noisy", variable=self.f_noise,command=self.check_enable_submit)
        self.f_wet_check = tk.Checkbutton(self.failure_frame, text="Unable to Wet", variable=self.f_wet,command=self.check_enable_submit)
        self.f_op_amp_check = tk.Checkbutton(self.failure_frame, text="Op Amp Failure", variable=self.f_op_amp,command=self.check_enable_submit)
        self.f_oversize_check = tk.Checkbutton(self.failure_frame, text="Overshot Size", variable=self.f_oversize,command=self.check_enable_submit)
        self.f_crash_check = tk.Checkbutton(self.failure_frame, text="Software Crash", variable=self.f_crash,command=self.check_enable_submit)


        ##### the submit button ######
        self.submit_frame = tk.Frame(parent)
        self.submit_button = tk.Button(self.submit_frame, text='Submit', command = self.submit)


        ##### Free text entry box for comments and unhandled failures/interventions #####
        self.comments_frame = tk.LabelFrame(parent, text='Comments')
        self.comments = tk.Entry(self.comments_frame)

        ##### Status display to guide users in filling out the fields #####
        self.status_frame = tk.LabelFrame(parent, text='Status')
        self.status_string = tk.StringVar()
        self.status_string.set('Ready')
        self.status = tk.Label(self.status_frame, textvariable=self.status_string)


        ##### Define the grid layout of all the above widgets within the GUI.
        ##### Frames are laid out with respect to one another and the parent frame
        ##### Widgets are laid out within frames

        self.loadopts_frame.grid(row=0,column=0,columnspan=8,sticky=tk.N+tk.S+tk.E+tk.W) #places loading options in the GUI
        self.loadopts_frame.columnconfigure(0, weight=1)
        self.loadopts_frame.columnconfigure(4, weight=1)
        self.load_default.grid(row=0,column=0,columnspan=4,sticky=tk.E+tk.W)
        self.load_last.grid(row=0,column=4,columnspan=4,sticky=tk.E+tk.W)


         
        
        self.id_frame.grid(row=1,column=0,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W) #place ID information widgets in the GUI
        self.name.grid(row=0,column=1,sticky=tk.E+tk.W)
        self.name_label.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.date.grid(row=1,column=1,sticky=tk.E+tk.W)
        self.date_label.grid(row=1,column=0,sticky=tk.E+tk.W)
        self.id.grid(row=2,column=1,sticky=tk.E+tk.W)
        self.id_label.grid(row=2,column=0,sticky=tk.E+tk.W)
        self.supplier.grid(row=3,column=1,sticky=tk.E+tk.W)
        self.supplier_label.grid(row=3,column=0,sticky=tk.E+tk.W)
        self.batch.grid(row=4,column=1,sticky=tk.E+tk.W)
        self.batch_label.grid(row=4,column=0,sticky=tk.E+tk.W)
        
        self.fab_frame.grid(row=1,column=2,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W) #place fabrication information widgets in the GUI
        self.fab_electrolyte.grid(row=0,column=1,sticky=tk.E+tk.W)
        self.fab_electrolyte_label.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.fab_molarity.grid(row=1,column=1,sticky=tk.E+tk.W)
        self.fab_molarity_label.grid(row=1,column=0,sticky=tk.E+tk.W)
        self.fab_pH.grid(row=2,column=1,sticky=tk.E+tk.W)
        self.fab_pH_label.grid(row=2,column=0,sticky=tk.E+tk.W)
        self.fab_voltage.grid(row=3,column=1,sticky=tk.E+tk.W)
        self.fab_voltage_label.grid(row=3,column=0,sticky=tk.E+tk.W)
        self.fab_thickness.grid(row=4,column=1,sticky=tk.E+tk.W)
        self.fab_thickness_label.grid(row=4,column=0,sticky=tk.E+tk.W)
        self.fab_time.grid(row=5,column=1,sticky=tk.E+tk.W)
        self.fab_time_label.grid(row=5,column=0,sticky=tk.E+tk.W)

        
        self.cond_frame.grid(row=1,column=4,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W)#place conditioning information widgets in the GUI
        self.cond_electrolyte.grid(row=0,column=1,sticky=tk.E+tk.W)
        self.cond_electrolyte_label.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.cond_molarity.grid(row=1,column=1,sticky=tk.E+tk.W)
        self.cond_molarity_label.grid(row=1,column=0,sticky=tk.E+tk.W)
        self.cond_pH.grid(row=2,column=1,sticky=tk.E+tk.W)
        self.cond_pH_label.grid(row=2,column=0,sticky=tk.E+tk.W)
        self.cond_voltage.grid(row=3,column=1,sticky=tk.E+tk.W)
        self.cond_voltage_label.grid(row=3,column=0,sticky=tk.E+tk.W)
        self.cond_time.grid(row=4,column=1,sticky=tk.E+tk.W)
        self.cond_time_label.grid(row=4,column=0,sticky=tk.E+tk.W)
        self.cond_size.grid(row=5,column=1,sticky=tk.E+tk.W)
        self.cond_size_label.grid(row=5,column=0,sticky=tk.E+tk.W)

        
        self.measure_frame.grid(row=1,column=6,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W)#place measurement information widgets in the GUI
        self.measure_electrolyte.grid(row=0,column=1,sticky=tk.E+tk.W)
        self.measure_electrolyte_label.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.measure_molarity.grid(row=1,column=1,sticky=tk.E+tk.W)
        self.measure_molarity_label.grid(row=1,column=0,sticky=tk.E+tk.W)
        self.measure_pH.grid(row=2,column=1,sticky=tk.E+tk.W)
        self.measure_pH_label.grid(row=2,column=0,sticky=tk.E+tk.W)
        self.measure_size.grid(row=3,column=1,sticky=tk.E+tk.W)
        self.measure_size_label.grid(row=3,column=0,sticky=tk.E+tk.W)
        self.measure_noise.grid(row=4,column=1,sticky=tk.E+tk.W)
        self.measure_noise_label.grid(row=4,column=0,sticky=tk.E+tk.W)
        self.measure_rect.grid(row=5,column=1,sticky=tk.E+tk.W)
        self.measure_rect_label.grid(row=5,column=0,sticky=tk.E+tk.W)


        self.outcome_frame.grid(row=2,column=0,columnspan=8,sticky=tk.N+tk.S+tk.E+tk.W) #place list of possible outcomes in GUI
        self.outcome_frame.columnconfigure(0, weight=1)
        self.outcome_frame.columnconfigure(1, weight=1)
        self.outcome_frame.columnconfigure(2, weight=1)
        self.outcome_success.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.outcome_salvage.grid(row=0,column=1,sticky=tk.E+tk.W)
        self.outcome_failure.grid(row=0,column=2,sticky=tk.E+tk.W)

        
        self.intervention_frame.grid(row=3,column=0,columnspan=4,sticky=tk.N+tk.S+tk.E+tk.W) #place list of possible interventions in GUI
        self.outcome_frame.columnconfigure(0, weight=1)
        self.outcome_frame.columnconfigure(4, weight=1)
        self.si_false_pos_check.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.si_false_neg_check.grid(row=1,column=0,sticky=tk.E+tk.W)
        self.si_sw_crash_check.grid(row=2,column=0,sticky=tk.E+tk.W)
        self.si_aging_check.grid(row=0,column=1,sticky=tk.E+tk.W)
        self.si_electrode_check.grid(row=1,column=1,sticky=tk.E+tk.W)
        self.si_op_amp_check.grid(row=2,column=1,sticky=tk.E+tk.W)

        
        
        self.failure_frame.grid(row=3,column=4,columnspan=4,sticky=tk.N+tk.S+tk.E+tk.W) #place list of possible failures modes in GUI
        self.f_false_pos_check.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.f_false_neg_check.grid(row=1,column=0,sticky=tk.E+tk.W)
        self.f_unstable_check.grid(row=2,column=0,sticky=tk.E+tk.W)
        self.f_broken_check.grid(row=0,column=1,sticky=tk.E+tk.W)
        self.f_noise_check.grid(row=1,column=1,sticky=tk.E+tk.W)
        self.f_wet_check.grid(row=2,column=1,sticky=tk.E+tk.W)
        self.f_op_amp_check.grid(row=0,column=2,sticky=tk.E+tk.W)
        self.f_oversize_check.grid(row=1,column=2,sticky=tk.E+tk.W)
        self.f_crash_check.grid(row=2,column=2,sticky=tk.E+tk.W)


        self.comments_frame.grid(row=4,column=0,columnspan=8,sticky=tk.N+tk.S+tk.E+tk.W)
        self.comments_frame.columnconfigure(0, weight=1)
        self.comments.grid(row=0,column=0,sticky=tk.E+tk.W)
        
        self.status_frame.grid(row=5,column=0,columnspan=8,sticky=tk.N+tk.S+tk.E+tk.W)
        self.status_frame.columnconfigure(0, weight=1)
        self.status.grid(row=0,column=0,sticky=tk.E+tk.W)


        self.submit_frame.grid(row=6,column=0,columnspan=8,sticky=tk.N+tk.S+tk.E+tk.W)
        self.submit_frame.columnconfigure(0, weight=1)
        self.submit_button.grid(row=0,column=0,sticky=tk.E+tk.W)


        self.set_date()
        self.disable_frame(self.intervention_frame)
        self.disable_frame(self.failure_frame)
        self.disable_frame(self.submit_frame)

        entry_list = [child for child in self.fab_frame.winfo_children() if isinstance(child, tk.Entry)]
        

    def set_date(self):
        now = datetime.datetime.now()
        self.date_string.set(now.strftime("%Y-%m-%d"))

    def load_standard(self): #load standard settings for as many entry fields as possible
        self.supplier_set.set('Norcada')
        self.fab_electrolyte_set.set('KCl')
        self.fab_molarity_set.set(1)
        self.fab_pH_set.set(10)
        self.fab_voltage_set.set(-6)
        self.fab_thickness_set.set(10)

        self.cond_electrolyte_set.set('LiCl')
        self.cond_molarity_set.set(3.6)
        self.cond_pH_set.set(8)
        self.cond_voltage_set.set(3)

        self.measure_electrolyte_set.set('LiCl')
        self.measure_molarity_set.set(3.6)
        self.measure_pH_set.set(8)

        self.status_string.set('Standard Configuration Loaded')

    def prep_row(self):
        pore_data = OrderedDict()
        pore_data['name'] = [self.name.get()]
        pore_data['date'] = [self.date.get()]
        pore_data['id']   = [self.id.get()]
        pore_data['supplier'] = [self.supplier.get()]
        pore_data['batch'] = [self.batch.get()]
        pore_data['fab_electrolyte'] = [self.fab_electrolyte.get()]
        pore_data['fab_molarity'] = [self.fab_molarity.get()]
        pore_data['fab_pH'] = [self.fab_pH.get()]
        pore_data['fab_voltage'] = [self.fab_voltage.get()]
        pore_data['thickness'] = [self.fab_thickness.get()]
        pore_data['fab_time'] = [self.fab_time.get()]
        pore_data['cond_electrolyte'] = [self.cond_electrolyte.get()]
        pore_data['cond_molarity'] = [self.cond_molarity.get()]
        pore_data['cond_pH'] = [self.cond_pH.get()]
        pore_data['cond_voltage'] = [self.cond_voltage.get()]
        pore_data['cond_time'] = [self.cond_time.get()]
        pore_data['cond_size'] = [self.cond_time.get()]
        pore_data['measure_electrolyte'] = [self.measure_electrolyte.get()]
        pore_data['measure_molarity'] = [self.measure_molarity.get()]
        pore_data['measure_pH'] = [self.measure_pH.get()]
        pore_data['measure_size'] = [self.measure_size.get()]
        pore_data['measure_noise'] = [self.measure_noise.get()]
        pore_data['measure_rect'] = [self.measure_rect.get()]
        pore_data['si_false_pos'] = [self.si_false_pos.get()]
        pore_data['si_false_neg'] = [self.si_false_neg.get()]
        pore_data['si_sw_crash'] = [self.si_sw_crash.get()]
        pore_data['si_aging'] = [self.si_aging.get()]
        pore_data['si_electrode'] = [self.si_electrode.get()]
        pore_data['f_false_pos'] = [self.f_false_pos.get()]
        pore_data['f_false_neg'] = [self.f_false_neg.get()]
        pore_data['f_unstable'] = [self.f_unstable.get()]
        pore_data['f_broken'] = [self.f_broken.get()]
        pore_data['f_noise'] = [self.f_noise.get()]
        pore_data['f_wet'] = [self.f_wet.get()]
        pore_data['f_op_amp'] = [self.f_op_amp.get()]
        pore_data['f_oversize'] = [self.f_oversize.get()]
        pore_data['f_crash'] = [self.f_crash.get()]
        
        self.df = pd.DataFrame(pore_data, index=None)
        print self.df

    def load_stats(self):
        pass

    
    def load_last(self):
        pass

    def grey_success(self):
        self.disable_frame(self.intervention_frame)
        self.disable_frame(self.failure_frame)
        self.enable_frame(self.submit_frame)

    def grey_salvage(self):
        self.enable_frame(self.intervention_frame)
        self.disable_frame(self.failure_frame)
    
    def grey_failure(self):
        self.disable_frame(self.intervention_frame)
        self.enable_frame(self.failure_frame)

    def disable_frame(self, frame):
        for child in frame.winfo_children():
            child.configure(state='disable')

    def enable_frame(self, frame):
        for child in frame.winfo_children():
            child.configure(state='normal')

    def submit(self):
        self.prep_row()
        if os.path.isfile('test.csv'):
            with open('test.csv',mode='a') as f:
                self.df.to_csv(f, header=False, index=False)
        else:
            with open('test.csv',mode='a') as f:
                self.df.to_csv(f, index=False)

    def check_enable_submit(self):
        self.enable_frame(self.submit_frame)
    
def main():
    root=tk.Tk()
    root.wm_title("NanoLog")
    LogGUI(root)
    root.mainloop()

    
if __name__ == "__main__":
    main()
