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
        self.intialize_alias_dict()
        
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


        ##### Entry boxes for pore information ######
        self.entries = OrderedDict()
        self.entry_labels = OrderedDict()
        self.entry_strings = OrderedDict()
        self.entry_frames = OrderedDict()
        framecol = 0
        for frame, widgets in self.entry_dict.iteritems():
            self.entries[frame] = OrderedDict()
            self.entry_labels[frame] = OrderedDict()
            self.entry_strings[frame] = OrderedDict()
            self.entry_frames[frame] = tk.LabelFrame(parent,text=frame)
            self.entry_frames[frame].grid(row=1,column=framecol,columnspan=2,sticky=tk.N+tk.S+tk.E+tk.W)
            framecol += 2
            row = 0
            for key, val in widgets.iteritems():
                self.entry_strings[frame][key] = tk.StringVar()
                self.entry_labels[frame][key] = tk.Label(self.entry_frames[frame],text=val+': ')
                self.entries[frame][key] = tk.Entry(self.entry_frames[frame], textvariable = self.entry_strings[frame][key])
                self.entry_labels[frame][key].grid(row=row, column=0, sticky=tk.E+tk.W)
                self.entries[frame][key].grid(row=row, column=1, sticky=tk.E+tk.W)
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

        ##### Entry boxes for pore information ######
        self.checkbuttons = OrderedDict()
        self.checkvars = OrderedDict()
        self.failure_frames = OrderedDict()
        framecol = 0
        for frame, widgets in self.mode_dict.iteritems():
            self.checkbuttons[frame] = OrderedDict()
            self.checkvars[frame] = OrderedDict()
            self.failure_frames[frame] = tk.LabelFrame(parent,text=frame)
            self.failure_frames[frame].grid(row=3,column=framecol,columnspan=4,sticky=tk.N+tk.S+tk.E+tk.W)
            framecol += 4
            row = 0
            for key, val in widgets.iteritems():
                self.checkvars[frame][key] = tk.IntVar()
                self.checkbuttons[frame][key] = tk.Checkbutton(self.failure_frames[frame], text=val, variable = self.checkvars[frame][key])
                self.checkbuttons[frame][key].grid(row=row, column=0, sticky=tk.E+tk.W)
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
        for frame, widgets in self.failure_frames.iteritems():
                self.disable_frame(widgets)
        self.submit_button.configure(state='disable')

    def intialize_alias_dict(self):
        self.entry_dict = OrderedDict([('Identification', OrderedDict([('name', 'Name'),
                                                                       ('date', 'Date'),
                                                                       ('pore_id', 'Pore ID'),
                                                                       ('supplier', 'Supplier'),
                                                                       ('batch', 'Membrane Batch'),
                                                                       ('instrument', 'Instrument')
                                                                       ])),
                                       ('Fabrication', OrderedDict([('fab_salt', 'Salt'),
                                                                    ('fab_molarity', 'Molarity'),
                                                                    ('fab_pH', 'pH'),
                                                                    ('fab_voltage', 'Voltage'),
                                                                    ('thickness', 'Thickness'),
                                                                    ('fab_time', 'Fabrication Time')
                                                                    ])),
                                       ('Conditioning', OrderedDict([('cond_salt', 'Salt'),
                                                                    ('cond_molarity', 'Molarity'),
                                                                    ('cond_pH', 'pH'),
                                                                    ('cond_voltage', 'Voltage'),
                                                                    ('target_size', 'Target Size'),
                                                                    ('cond_time', 'Conditioning Time')
                                                                    ])),
                                       ('Measurement', OrderedDict([('measure_salt', 'Salt'),
                                                                    ('measure_molarity', 'Molarity'),
                                                                    ('measure_pH', 'pH'),
                                                                    ('final_size', 'Final Size'),
                                                                    ('1Hz_PSD_200mV', '1Hz PSD at 200mV'),
                                                                    ('rectification', 'Rectification')
                                                                    ]))
                                       ])
        self.mode_dict = OrderedDict([('Intervention', OrderedDict([('i_false_pos', 'False Positive(s)'),
                                                                     ('i_false_neg', 'False Negative(s)'),
                                                                     ('i_sw_error', 'Software Error'),
                                                                     ('i_aging_noise', 'Pore Aging - Noise'),
                                                                     ('i_aging_iv', 'Pore Aging - Size'),
                                                                     ('i_aging_rect', 'Pore Aging - Rectification'),
                                                                     ('i_electrode', 'Electrode Fix'),
                                                                     ('i_op_amp', 'Op Amp Fix'),
                                                                     ('i_other', 'Other - Comment')
                                                                     ])),
                                       ('Failure', OrderedDict([('f_false_pos', 'False Positive(s)'),
                                                                ('f_false_neg', 'False Negastives(s)'),
                                                                ('f_unstable', 'Unstable'),
                                                                ('f_broken', 'Broken Membrane'),
                                                                ('f_noise', 'High 1/f Noise'),
                                                                ('f_wet', 'Unable to Wet'),
                                                                ('f_oversize', 'Overshot Pore Size'),
                                                                ('f_user', 'User Error'),
                                                                ('f_duration', 'Too Long'),
                                                                ('f_other', 'Other - Comment')
                                                                ]))
                                       ])

        self.standard_dict = OrderedDict([('Identification', OrderedDict([('name', ''),
                                                                       ('date', datetime.datetime.now().strftime("%Y-%m-%d")),
                                                                       ('pore_id', ''),
                                                                       ('supplier', 'Norcada'),
                                                                       ('batch', ''),
                                                                       ('instrument', '')
                                                                       ])),
                                       ('Fabrication', OrderedDict([('fab_salt', 'KCl'),
                                                                    ('fab_molarity', '1'),
                                                                    ('fab_pH', '10'),
                                                                    ('fab_voltage', '-6'),
                                                                    ('thickness', '10'),
                                                                    ('fab_time', '')
                                                                    ])),
                                       ('Conditioning', OrderedDict([('cond_salt', 'LiCl'),
                                                                    ('cond_molarity', '3.6'),
                                                                    ('cond_pH', '8'),
                                                                    ('cond_voltage', '3'),
                                                                    ('target_size', ''),
                                                                    ('cond_time', '')
                                                                    ])),
                                       ('Measurement', OrderedDict([('measure_salt', 'LiCl'),
                                                                    ('measure_molarity', '3.6'),
                                                                    ('measure_pH', '8'),
                                                                    ('final_size', ''),
                                                                    ('1Hz_PSD_200mV', ''),
                                                                    ('rectification', '')
                                                                    ]))
                                       ])
        


    def prep_row(self):
        pore_data = OrderedDict()
        for frame, widgets in self.entry_dict.iteritems():
            for key, val in widgets.iteritems():
                pore_data[key] = self.entries[frame][key].get()
        pore_data['Outcome'] = [self.outcome.get()]
        for frame, widgets in self.mode_dict.iteritems():
            for key, val in widgets.iteritems():
                pore_data[key] = self.checkvars[frame][key].get()
        pore_data['File_Path'] = self.file_name
        pore_data['Comments'] = self.comments.get().translate(None, ',\t;')
        self.df = pd.DataFrame(pore_data,index=None)

    def set_date(self):
        now = datetime.datetime.now()
        self.entry_strings['Identification']['date'].set(now.strftime("%Y-%m-%d"))

    def disable_frame(self, frame):
        for child in frame.winfo_children():
            child.configure(state='disable')

    def enable_frame(self, frame):
        for child in frame.winfo_children():
            child.configure(state='normal')   
    
    def load_standard(self):
        for frame, widgets in self.standard_dict.iteritems():
            for key, val in widgets.iteritems():
                self.entry_strings[frame][key].set(val)

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
            self.file_name = 'S:/Issue Tracking/Logs/'+self.entries['Identification']['name'].get() +'-'+ self.entries['Identification']['pore_id'].get() + '.log'
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
            for frame, widgets in self.failure_frames.iteritems():
                self.disable_frame(widgets)
                for key, val in self.checkvars[frame].iteritems():
                    val.set(0)           
        elif self.outcome.get() == 1:
            for frame, widgets in self.failure_frames.iteritems():
                if frame != 'Intervention':
                    self.disable_frame(widgets)
                    for key, val in self.checkvars[frame].iteritems():
                        val.set(0)
                else:
                    self.enable_frame(widgets)
        elif self.outcome.get() == 2:
            for frame, widgets in self.failure_frames.iteritems():
                if frame != 'Failure':
                    self.disable_frame(widgets)
                    for key, val in self.checkvars[frame].iteritems():
                        val.set(0)
                else:
                    self.enable_frame(widgets)

    def verify(self):
        self.status_string.set('')
        submit = 1


        for frame, widgets in self.entry_dict.iteritems():
            for key, val in widgets.iteritems():
                if not self.entries[frame][key].get():
                    self.status_string.set(self.status_string.get()+'Please fill out all {0} information fields\n'.format(frame))
                    submit = 0
                    break
                
        if self.outcome.get() == -1:
            self.status_string.set(self.status_string.get()+'Please select an experimental outcome\n')
            submit = 0 
        elif self.outcome.get() == 1:
            total = 0
            for key, val in self.checkvars['Intervention'].iteritems():
                total += val.get()
            if total == 0:
                self.status_string.set(self.status_string.get()+'Please select at least one standard intervention\n')
                submit = 0
        elif self.outcome.get() == 2:
            total = 0
            for key, val in self.checkvars['Failure'].iteritems():
                total += val.get()
            if total == 0:
                self.status_string.set(self.status_string.get()+'Please select at least one failure mode\n')
                submit = 0

        if self.checkvars['Failure']['f_other'].get() == 1 or self.checkvars['Intervention']['i_other'].get() == 1:
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
