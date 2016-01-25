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
import os
import tkFileDialog
import shutil

class LogGUI(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        ##### Define all widgets and frames displayed in the GUI, and bind appropriate variables ######


        ##### defines widgets for loading presets ##########
        self.loadopts_frame = tk.LabelFrame(parent,text='Options') 
        self.load_default = tk.Button(self.loadopts_frame, text='Load Standard',command=self.load_standard)
        self.load_last = tk.Button(self.loadopts_frame, text='Load Last',command=self.load_last)
        self.load_run_log = tk.Button(self.loadopts_frame, text='Load Run Log', command=self.read_run_log)


        ##### define widgets for identification information ##########
        self.id_info_list = ['Name', 'Date', 'Pore ID', 'Supplier', 'Batch', 'Instrument']
        self.id_entry = OrderedDict()
        self.id_label = OrderedDict()
        self.id_string = OrderedDict()
        self.id_frame = tk.LabelFrame(parent,text='Identification Parameters')
        for var in self.id_info_list:
            self.id_string[var] = tk.StringVar()
            self.id_label[var] = tk.Label(self.id_frame,text=var+': ')
            self.id_entry[var] = tk.Entry(self.id_frame, textvariable = self.id_string[var])



        ##### defines widgets for fabrication information ##########
        self.fab_info_list = ['Salt', 'Molarity', 'pH', 'Voltage', 'Thickness', 'Duration']
        self.fab_entry = OrderedDict()
        self.fab_label = OrderedDict()
        self.fab_string = OrderedDict()
        self.fab_frame = tk.LabelFrame(parent,text='Fabrication Parameters') 
        for var in self.fab_info_list:
            self.fab_string[var] = tk.StringVar()
            self.fab_label[var] = tk.Label(self.fab_frame, text=var+': ')
            self.fab_entry[var] = tk.Entry(self.fab_frame, textvariable = self.fab_string[var])
        


        #####defines widgets for conditioning information##########
        self.cond_info_list = ['Salt', 'Molarity', 'pH', 'Voltage', 'Target Size', 'Duration']
        self.cond_entry = OrderedDict()
        self.cond_label = OrderedDict()
        self.cond_string = OrderedDict()
        self.cond_frame = tk.LabelFrame(parent,text='Conditioning Parameters')
        for var in self.cond_info_list:
            self.cond_string[var] = tk.StringVar()
            self.cond_label[var] = tk.Label(self.cond_frame, text=var+': ')
            self.cond_entry[var] = tk.Entry(self.cond_frame, textvariable = self.cond_string[var])


        ########## defines widgets for measurement information ##########
        self.measure_info_list = ['Salt', 'Molarity', 'pH', 'Final Size', '1Hz PSD', 'Rectification']
        self.measure_entry = OrderedDict()
        self.measure_label = OrderedDict()
        self.measure_string = OrderedDict()
        self.measure_frame = tk.LabelFrame(parent,text='Measurement Parameters')
        for var in self.measure_info_list:
            self.measure_string[var] = tk.StringVar()
            self.measure_label[var] = tk.Label(self.measure_frame, text=var+': ')
            self.measure_entry[var] = tk.Entry(self.measure_frame, textvariable = self.measure_string[var])


        ##### widgets to describe details of the experimental outcome #######
        self.outcome_frame = tk.LabelFrame(parent,text='Outcome') 
        self.outcome = tk.IntVar()
        self.outcome.set(-1)
        self.outcome_success = tk.Radiobutton(self.outcome_frame, text='Success', variable = self.outcome, value=0, indicatoron=0, command=self.grey_success)
        self.outcome_salvage = tk.Radiobutton(self.outcome_frame, text='Salvaged', variable = self.outcome, value=1, indicatoron=0, command=self.grey_salvage)
        self.outcome_failure = tk.Radiobutton(self.outcome_frame, text='Failure', variable = self.outcome, value=2, indicatoron=0, command=self.grey_failure)


        ###### widgets to describe standard successful interventions ######
        self.intervention_list = ['False Positive', 'False Negative', 'Software Error', 'Pore Aging - Noise', 'Pore Aging - IV', 'Electrode Fix', 'Op Amp Fix']
        self.intervention_check = OrderedDict()
        self.intervention_button = OrderedDict()
        self.intervention_frame = tk.LabelFrame(parent,text='Standard Interventions')
        for var in self.intervention_list:
            self.intervention_check[var] = tk.IntVar()
            self.intervention_button[var] = tk.Checkbutton(self.intervention_frame, text=var, variable = self.intervention_check[var])
        

        ##### widgets to describe standard modes of failure #######
        self.failure_list = ['False Positive', 'False Negative', 'Unstable', 'Broken Membrane', 'High 1/f Noise', 'Unable to Wet', 'Overshot Size', 'User Error']
        self.failure_check = OrderedDict()
        self.failure_button = OrderedDict()
        self.failure_frame = tk.LabelFrame(parent,text='Reasons for Failure')
        for var in self.failure_list:
            self.failure_check[var] = tk.IntVar()
            self.failure_button[var] = tk.Checkbutton(self.failure_frame, text=var, variable = self.failure_check[var])
        
        
        ##### the submit button ######
        self.submit_frame = tk.Frame(parent)
        self.verify_button = tk.Button(self.submit_frame, text='Verify', command = self.verify)
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
        self.loadopts_frame.columnconfigure(1, weight=1)
        self.loadopts_frame.columnconfigure(2, weight=1)
        self.load_default.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.load_last.grid(row=0,column=1,sticky=tk.E+tk.W)
        self.load_run_log.grid(row=0,column=2,sticky=tk.E+tk.W)


         
        
        self.id_frame.grid(row=1,column=0,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W) #place ID information widgets in the GUI
        row = 0
        for val in self.id_info_list:
            self.id_label[val].grid(row=row, column=0, sticky = tk.E+tk.W)
            self.id_entry[val].grid(row=row, column=1, sticky = tk.E+tk.W)
            row += 1
        
        self.fab_frame.grid(row=1,column=2,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W) #place fabrication information widgets in the GUI
        row = 0
        for val in self.fab_info_list:
            self.fab_label[val].grid(row=row, column=0, sticky = tk.E+tk.W)
            self.fab_entry[val].grid(row=row, column=1, sticky = tk.E+tk.W)
            row += 1
        
        self.cond_frame.grid(row=1,column=4,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W)#place conditioning information widgets in the GUI
        row = 0
        for val in self.cond_info_list:
            self.cond_label[val].grid(row=row, column=0, sticky = tk.E+tk.W)
            self.cond_entry[val].grid(row=row, column=1, sticky = tk.E+tk.W)
            row += 1
        
        self.measure_frame.grid(row=1,column=6,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W)#place measurement information widgets in the GUI
        row = 0
        for val in self.measure_info_list:
            self.measure_label[val].grid(row=row, column=0, sticky = tk.E+tk.W)
            self.measure_entry[val].grid(row=row, column=1, sticky = tk.E+tk.W)
            row += 1
        

        self.outcome_frame.grid(row=2,column=0,columnspan=8,sticky=tk.N+tk.S+tk.E+tk.W) #place list of possible outcomes in GUI
        self.outcome_frame.columnconfigure(0, weight=1)
        self.outcome_frame.columnconfigure(1, weight=1)
        self.outcome_frame.columnconfigure(2, weight=1)
        self.outcome_success.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.outcome_salvage.grid(row=0,column=1,sticky=tk.E+tk.W)
        self.outcome_failure.grid(row=0,column=2,sticky=tk.E+tk.W)

        
        self.intervention_frame.grid(row=3,column=0,columnspan=4,sticky=tk.N+tk.S+tk.E+tk.W) #place list of possible interventions in GUI
        row = 0
        for val in self.intervention_list:
            self.intervention_button[val].grid(row=row, column=1, sticky = tk.E+tk.W)
            row += 1

        
        
        self.failure_frame.grid(row=3,column=4,columnspan=4,sticky=tk.N+tk.S+tk.E+tk.W) #place list of possible failures modes in GUI
        row = 0
        for val in self.failure_list:
            self.failure_button[val].grid(row=row, column=1, sticky = tk.E+tk.W)
            row += 1


        self.comments_frame.grid(row=4,column=0,columnspan=8,sticky=tk.N+tk.S+tk.E+tk.W)
        self.comments_frame.columnconfigure(0, weight=1)
        self.comments.grid(row=0,column=0,sticky=tk.E+tk.W)
        
        self.status_frame.grid(row=5,column=0,columnspan=8,sticky=tk.N+tk.S+tk.E+tk.W)
        self.status_frame.columnconfigure(0, weight=1)
        self.status.grid(row=0,column=0,sticky=tk.E+tk.W)


        self.submit_frame.grid(row=6,column=0,columnspan=8,sticky=tk.N+tk.S+tk.E+tk.W)
        self.submit_frame.columnconfigure(0, weight=1)
        self.submit_frame.columnconfigure(1, weight=1)
        self.verify_button.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.submit_button.grid(row=0,column=1,sticky=tk.E+tk.W)


        self.set_date()
        self.disable_frame(self.intervention_frame) #grey out unused frames
        self.disable_frame(self.failure_frame)
        self.disable_frame(self.submit_frame)


    def load_standard(self):
        pass

    def load_last(self):
        pass

    def read_run_log(self):
        pass
        
    def grey_success(self):
        pass

    def grey_salvage(self):
        pass

    def grey_failure(self):
        pass

    def submit(self):
        pass

    def set_date(self):
        pass

    def disable_frame(self, frame):
        pass

    def verify(self):
        pass

    
def main():
    root=tk.Tk()
    root.wm_title("NanoLog")
    LogGUI(root)
    root.mainloop()

    
if __name__ == "__main__":
    main()
