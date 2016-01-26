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
        self.loadopts_frame.grid(row=0,column=0,columnspan=8,sticky=tk.N+tk.S+tk.E+tk.W)
        self.loadopts_frame.columnconfigure(0, weight=1)
        self.loadopts_frame.columnconfigure(1, weight=1)
        self.loadopts_frame.columnconfigure(2, weight=1)
        
        self.load_default = tk.Button(self.loadopts_frame, text='Load Standard',command=self.load_standard)
        self.load_last = tk.Button(self.loadopts_frame, text='Load Last',command=self.load_last)
        self.load_run_log = tk.Button(self.loadopts_frame, text='Load Run Log', command=self.read_run_log)

        self.load_default.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.load_last.grid(row=0,column=1,sticky=tk.E+tk.W)
        self.load_run_log.grid(row=0,column=2,sticky=tk.E+tk.W)


        ##### define widgets for identification information ##########
        self.id_info_list = ['Name', 'Date', 'Pore_ID', 'Supplier', 'Batch', 'Instrument']
        self.id_entry = OrderedDict()
        self.id_label = OrderedDict()
        self.id_string = OrderedDict()
        self.id_frame = tk.LabelFrame(parent,text='Identification Parameters')
        self.id_frame.grid(row=1,column=0,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W)
        row = 0
        for var in self.id_info_list:
            self.id_string[var] = tk.StringVar()
            self.id_label[var] = tk.Label(self.id_frame,text=var+': ')
            self.id_entry[var] = tk.Entry(self.id_frame, textvariable = self.id_string[var])
            self.id_label[var].grid(row=row, column=0, sticky = tk.E+tk.W)
            self.id_entry[var].grid(row=row, column=1, sticky = tk.E+tk.W)
            row += 1
            



        ##### defines widgets for fabrication information ##########
        self.fab_info_list = ['Salt', 'Molarity', 'pH', 'Voltage', 'Thickness', 'Duration']
        self.fab_entry = OrderedDict()
        self.fab_label = OrderedDict()
        self.fab_string = OrderedDict()
        self.fab_frame = tk.LabelFrame(parent,text='Fabrication Parameters')
        self.fab_frame.grid(row=1,column=2,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W)
        row = 0
        for var in self.fab_info_list:
            self.fab_string[var] = tk.StringVar()
            self.fab_label[var] = tk.Label(self.fab_frame, text=var+': ')
            self.fab_entry[var] = tk.Entry(self.fab_frame, textvariable = self.fab_string[var])
            self.fab_label[var].grid(row=row, column=0, sticky = tk.E+tk.W)
            self.fab_entry[var].grid(row=row, column=1, sticky = tk.E+tk.W)
            row += 1
        


        #####defines widgets for conditioning information##########
        self.cond_info_list = ['Salt', 'Molarity', 'pH', 'Voltage', 'Target_Size', 'Duration']
        self.cond_entry = OrderedDict()
        self.cond_label = OrderedDict()
        self.cond_string = OrderedDict()
        self.cond_frame = tk.LabelFrame(parent,text='Conditioning Parameters')
        self.cond_frame.grid(row=1,column=4,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W)#place conditioning information widgets in the GUI
        row = 0
            
        for var in self.cond_info_list:
            self.cond_string[var] = tk.StringVar()
            self.cond_label[var] = tk.Label(self.cond_frame, text=var+': ')
            self.cond_entry[var] = tk.Entry(self.cond_frame, textvariable = self.cond_string[var])
            self.cond_label[var].grid(row=row, column=0, sticky = tk.E+tk.W)
            self.cond_entry[var].grid(row=row, column=1, sticky = tk.E+tk.W)
            row += 1


        ########## defines widgets for measurement information ##########
        self.measure_info_list = ['Salt', 'Molarity', 'pH', 'Final_Size', '1Hz_PSD', 'Rectification']
        self.measure_entry = OrderedDict()
        self.measure_label = OrderedDict()
        self.measure_string = OrderedDict()
        self.measure_frame = tk.LabelFrame(parent,text='Measurement Parameters')
        self.measure_frame.grid(row=1,column=6,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W)#place measurement information widgets in the GUI
        row = 0
        for var in self.measure_info_list:
            self.measure_string[var] = tk.StringVar()
            self.measure_label[var] = tk.Label(self.measure_frame, text=var+': ')
            self.measure_entry[var] = tk.Entry(self.measure_frame, textvariable = self.measure_string[var])
            self.measure_label[var].grid(row=row, column=0, sticky = tk.E+tk.W)
            self.measure_entry[var].grid(row=row, column=1, sticky = tk.E+tk.W)
            row += 1


        ##### widgets to describe details of the experimental outcome #######
        self.outcome_list = ['Success', 'Salvaged', 'Failure']
        self.outcome_radio = OrderedDict()
        self.outcome = tk.IntVar()
        self.outcome.set(-1)
        self.outcome_frame = tk.LabelFrame(parent,text='Outcome')
        self.outcome_frame.grid(row=2,column=0,columnspan=8,sticky=tk.N+tk.S+tk.E+tk.W) #place list of possible outcomes in GUI
        
        self.outcome_frame.columnconfigure(0, weight=1)
        self.outcome_frame.columnconfigure(1, weight=1)
        self.outcome_frame.columnconfigure(2, weight=1)

        col=0
        for var in self.outcome_list:
            self.outcome_radio[var] = tk.Radiobutton(self.outcome_frame, text=var, variable = self.outcome, value=col, indicatoron=0, command=self.grey_outcome)
            self.outcome_radio[var].grid(row=0,column=col,sticky=tk.E+tk.W)
            col += 1


        ###### widgets to describe standard successful interventions ######
        self.intervention_list = ['False_Positive', 'False_Negative', 'Software_Error', 'Pore_Aging_Noise', 'Pore_Aging_Size', 'Electrode_Fix', 'Op_Amp_Fix', 'Other_Comment']
        self.intervention_check = OrderedDict()
        self.intervention_button = OrderedDict()
        self.intervention_frame = tk.LabelFrame(parent,text='Standard Interventions')
        self.intervention_frame.grid(row=3,column=0,columnspan=4,sticky=tk.N+tk.S+tk.E+tk.W) #place list of possible interventions in GUI
        row = 0
        for var in self.intervention_list:
            self.intervention_check[var] = tk.IntVar()
            self.intervention_button[var] = tk.Checkbutton(self.intervention_frame, text=var, variable = self.intervention_check[var])
            self.intervention_button[var].grid(row=row, column=1, sticky = tk.E+tk.W)
            row += 1
        

        ##### widgets to describe standard modes of failure #######
        self.failure_list = ['False_Positive', 'False_Negative', 'Unstable', 'Broken_Membrane', 'High_Noise', 'Not_Wet', 'Overshot_Size', 'User_Error', 'Other_Comment']
        self.failure_check = OrderedDict()
        self.failure_button = OrderedDict()
        self.failure_frame = tk.LabelFrame(parent,text='Reasons for Failure')
        self.failure_frame.grid(row=3,column=4,columnspan=4,sticky=tk.N+tk.S+tk.E+tk.W) #place list of possible failures modes in GUI
        row = 0
        for var in self.failure_list:
            self.failure_check[var] = tk.IntVar()
            self.failure_button[var] = tk.Checkbutton(self.failure_frame, text=var, variable = self.failure_check[var])
            self.failure_button[var].grid(row=row, column=1, sticky = tk.E+tk.W)
            row += 1
        
        
        

        ##### Free text entry box for comments and unhandled failures/interventions #####
        self.comments_frame = tk.LabelFrame(parent, text='Comments')
        self.comments_frame.grid(row=4,column=0,columnspan=8,sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.comments_frame.columnconfigure(0, weight=1)
        
        self.comments = tk.Entry(self.comments_frame)
        self.comments.grid(row=0,column=0,sticky=tk.E+tk.W)

        ##### Status display to guide users in filling out the fields #####
        self.status_frame = tk.LabelFrame(parent, text='Status')
        self.status_frame.grid(row=5,column=0,columnspan=8,sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.status_frame.columnconfigure(0, weight=1)
        
        
        self.status_string = tk.StringVar()
        self.status_string.set('Ready')
        self.status = tk.Label(self.status_frame, textvariable=self.status_string)
        self.status.grid(row=0,column=0,sticky=tk.E+tk.W)


        ##### the verify and submit buttons ######
        self.submit_frame = tk.Frame(parent)
        self.submit_frame.grid(row=6,column=0,columnspan=8,sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.submit_frame.columnconfigure(0, weight=1)
        self.submit_frame.columnconfigure(1, weight=1)

        self.verify_button = tk.Button(self.submit_frame, text='Verify', command = self.verify)
        self.submit_button = tk.Button(self.submit_frame, text='Submit', command = self.submit)
        self.verify_button.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.submit_button.grid(row=0,column=1,sticky=tk.E+tk.W)

        
        ##### Initial Book Keeping ####
        self.set_date()
        self.run_log_path=''
        self.disable_frame(self.intervention_frame) #grey out unused frames
        self.disable_frame(self.failure_frame)
        self.submit_button.configure(state='disable')

    def prep_row(self):
        pore_data = OrderedDict()
        for var in self.id_info_list:
            pore_data[var] = [self.id_entry[var].get()]
        for var in self.fab_info_list:
            pore_data[var] = [self.fab_entry[var].get()]
        for var in self.cond_info_list:
            pore_data[var] = [self.cond_entry[var].get()]
        for var in self.measure_info_list:
            pore_data[var] = [self.measure_entry[var].get()]
        pore_data['Outcome'] = [self.outcome.get()]
        for var in self.intervention_list:
            pore_data[var] = [self.intervention_check[var].get()]
        for var in self.failure_list:
            pore_data[var] = [self.failure_check[var].get()]
        pore_data['File_Path'] = self.file_name
        self.df = pd.DataFrame(pore_data,index=None)

    def set_date(self):
        now = datetime.datetime.now()
        self.id_string['Date'].set(now.strftime("%Y-%m-%d"))

    def disable_frame(self, frame):
        for child in frame.winfo_children():
            child.configure(state='disable')

    def enable_frame(self, frame):
        for child in frame.winfo_children():
            child.configure(state='normal')   
    
    def load_standard(self):
        pass

    def load_last(self):
        pass

    def read_run_log(self):
        self.run_log_path = tkFileDialog.askopenfilename()
        if not self.run_log_path or not os.path.isfile(self.run_log_path):
            self.status_string.set('Choose a valid log file')
            self.read_run_log = ''
        else:
            self.status_string.set('Read run log: '+self.run_log_path)
            
    def copy_run_log(self):
        try:
            self.file_name = 'S:/Issue Tracking/Logs/'+self.id_entry['Name'].get() +'-'+ self.id_entry['Pore_ID'].get() + '.log'
            shutil.copy2(self.run_log_path, self.file_name)
            if os.path.isfile (self.file_name):
                self.status_string.set('Log file copied to '+self.file_name)
                self.run_log_copied = 1
            else:
                self.status_string.set('Unable to copy log file to '+self.file_name)
        except IOError:
            self.status_string.set('Could not open log file')
        
    def grey_outcome(self):
        if self.outcome.get() == 0:
            self.disable_frame(self.intervention_frame)
            self.disable_frame(self.failure_frame)
            for var in self.intervention_list:
                self.intervention_check[var].set(0)
            for var in self.failure_list:
                self.failure_check[var].set(0)
        elif self.outcome.get() == 1:
            self.enable_frame(self.intervention_frame)
            self.disable_frame(self.failure_frame)
            for var in self.failure_list:
                self.failure_check[var].set(0)
        elif self.outcome.get() == 2:
            self.disable_frame(self.intervention_frame)
            self.enable_frame(self.failure_frame)
            for var in self.intervention_list:
                self.intervention_check[var].set(0)

    def verify(self):
        self.status_string.set('')
        submit = 1
        for var in self.id_info_list:
            if not self.id_entry[var].get():
                self.status_string.set(self.status_string.get()+'Please fill out all identification information fields\n')
                submit = 0
                break
        for var in self.fab_info_list:
            if not self.fab_entry[var].get():
                self.status_string.set(self.status_string.get()+'Please fill out all fabrication information fields\n')
                submit = 0
                break
        for var in self.cond_info_list:
            if not self.cond_entry[var].get():
                self.status_string.set(self.status_string.get()+'Please fill out all conditioning information fields\n')
                submit = 0
                break
        for var in self.measure_info_list:
            if not self.measure_entry[var].get():
                self.status_string.set(self.status_string.get()+'Please fill out all measurement information fields\n')
                submit = 0
                break
             
        if self.outcome.get() == -1:
            self.status_string.set(self.status_string.get()+'Please select an experimental outcome\n')
            submit = 0 
        elif self.outcome.get() == 1:
            total = 0
            for var in self.intervention_list:
                total += self.intervention_check[var].get()
            if total == 0:
                self.status_string.set(self.status_string.get()+'Please select at least one standard intervention\n')
                submit = 0
        elif self.outcome.get() == 2:
            total = 0
            for var in self.failure_list:
                total += self.failure_check[var].get()
            if total == 0:
                self.status_string.set(self.status_string.get()+'Please select at least one failure mode\n')
                submit = 0

        if self.intervention_check['Other_Comment'].get() == 1 or self.failure_check['Other_Comment'].get() == 1:
            if not self.comments.get():
                self.status_string.set(self.status_string.get()+'Please comment on the specifics of the non-standard intervention used\n')
                submit = 0

        if not self.run_log_path:
            self.status_string.set(self.status_string.get()+'Please load Record.log for your pore\n')
            submit = 0
        if not os.path.isfile(self.run_log_path):
            self.status_string.set(self.status_string.get()+'Unable to locate log file: '+self.run_log_path+'\n')
            self.run_log_path=''
            submit = 0

        if submit == 1:
            self.submit_button.configure(state='normal')
            self.status_string.set('Ready to submit, please review information for accuracy')


    def submit(self):
        submitted = 1
        self.copy_run_log()
        self.prep_row()
        try:
            if os.path.isfile('S:/Issue Tracking/Fabrication-Statistics.csv'):
                with open('S:/Issue Tracking/Fabrication-Statistics.csv',mode='a') as f:
                    self.df.to_csv(f, header=False, index=False)
            else:
                with open('S:/Issue Tracking/Fabrication-Statistics.csv',mode='a') as f:
                    self.df.to_csv(f, index=False)
        except IOError:
            self.status_string.set('Could not open statistics file - close it and try again')
            submitted = 0
        if submitted == 1:
            self.status_string.set('Pore data submitted')
            self.submit_button.configure(state='disable')

    
def main():
    root=tk.Tk()
    root.wm_title("NanoLog")
    LogGUI(root)
    root.mainloop()

    
if __name__ == "__main__":
    main()
