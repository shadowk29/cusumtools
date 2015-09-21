import pandas as pd
from pandasql import sqldf
import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import os
import tkFileDialog
import Tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg


    
class App(tk.Frame):
    def __init__(self, parent,eventsdb,column_list,events_folder,file_path_string):
        tk.Frame.__init__(self, parent)
        self.file_path_string = file_path_string
        self.events_folder = events_folder
        self.eventsdb = eventsdb
        self.eventsdb_subset = eventsdb
        self.eventsdb_prev = self.eventsdb_subset
        self.column_list = column_list
        self.x_col_options = tk.StringVar()
        self.x_col_options.set('Level Duration (us)')
        self.y_col_options = tk.StringVar()
        self.y_col_options.set('Blockage Level (pA)')
        self.graph_list = tk.StringVar()
        self.graph_list.set('2D Histogram')
        self.alias_columns()
        parent.deiconify()


        
        #Statistics plotting widgets
        self.stats_frame = tk.LabelFrame(parent,text='Statistics View')
        self.f = Figure(figsize=(7,5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.f, master=self.stats_frame)
        self.toolbar_frame = tk.Frame(self.stats_frame)
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.toolbar_frame)
        self.toolbar.update()

        

        self.toolbar_frame.grid(row=1,column=0,columnspan=6)
        self.canvas.get_tk_widget().grid(row=0,column=0,columnspan=6)

        
        
        self.plot_button = tk.Button(self.stats_frame,text='Update Plot',command=self.update_plot)
        self.x_option = tk.OptionMenu(self.stats_frame, self.x_col_options, *[self.alias_dict.get(option,option) for option in self.column_list])
        self.y_option = tk.OptionMenu(self.stats_frame, self.y_col_options, *[self.alias_dict.get(option,option) for option in self.column_list])
        self.graph_option = tk.OptionMenu(self.stats_frame, self.graph_list, 'XY Plot', '1D Histogram', '2D Histogram', command=self.disable_options)
        self.x_log_var = tk.IntVar()
        self.x_log_check = tk.Checkbutton(self.stats_frame, text='Log X', variable = self.x_log_var)
        self.y_log_var = tk.IntVar()
        self.y_log_check = tk.Checkbutton(self.stats_frame, text='Log Y', variable = self.y_log_var)
        
        self.x_bins=tk.Label(self.stats_frame,text='X Bins:')
        self.y_bins=tk.Label(self.stats_frame,text='Y Bins:')

        self.xbin_entry = tk.Entry(self.stats_frame)
        self.xbin_entry.insert(0,100)
        self.ybin_entry = tk.Entry(self.stats_frame)
        self.ybin_entry.insert(0,100)


        self.stats_frame.grid(row=0,column=0,columnspan=6,sticky=tk.N+tk.S)
        self.x_log_check.grid(row=3,column=2,sticky=tk.E+tk.W)
        self.y_log_check.grid(row=4,column=2,sticky=tk.E+tk.W)
        self.x_bins.grid(row=3,column=3,sticky=tk.E+tk.W)
        self.y_bins.grid(row=4,column=3,sticky=tk.E+tk.W)
        self.xbin_entry.grid(row=3,column=4,sticky=tk.E+tk.W)
        self.ybin_entry.grid(row=4,column=4,sticky=tk.E+tk.W)
        self.graph_option.grid(row=3,column=0,rowspan=2,sticky=tk.E+tk.W)
        self.x_option.grid(row=3,column=1,sticky=tk.E+tk.W)
        self.y_option.grid(row=4,column=1,sticky=tk.E+tk.W)
        self.plot_button.grid(row=3,column=5,rowspan=2,sticky=tk.E+tk.W)

        parent.bind("<Return>", self.enter_key_press)

        
        

        #Single Event widgets

        self.events_frame = tk.LabelFrame(parent,text='Single Event View')
        self.event_f = Figure(figsize=(7,5), dpi=100)
        self.event_canvas = FigureCanvasTkAgg(self.event_f, master=self.events_frame)
        self.event_toolbar_frame = tk.Frame(self.events_frame)
        self.event_toolbar = NavigationToolbar2TkAgg(self.event_canvas, self.event_toolbar_frame)
        self.event_toolbar.update()
        self.event_info_string = tk.StringVar()
        self.event_index = tk.IntVar()
        self.event_index.set(self.eventsdb_subset['id'][0])
        self.event_entry = tk.Entry(self.events_frame, textvariable=self.event_index)
        self.plot_event_button = tk.Button(self.events_frame,text='Plot Event',command=self.plot_event)
        self.next_event_button = tk.Button(self.events_frame,text='Next',command=self.next_event)
        self.prev_event_button = tk.Button(self.events_frame,text='Prev',command=self.prev_event)
        self.delete_event_button = tk.Button(self.events_frame,text='Delete',command=self.delete_event)
        self.event_info_string = tk.StringVar()
        self.event_info_string.set('')
        self.event_info_display = tk.Label(self.events_frame, textvariable=self.event_info_string)

        
        self.event_toolbar_frame.grid(row=1,column=0,columnspan=5)
        self.event_canvas.get_tk_widget().grid(row=0,column=0,columnspan=5)
        
        parent.bind("<Left>", self.left_key_press)
        parent.bind("<Right>", self.right_key_press)
        parent.bind("<Delete>", self.delete_key_press)

        self.events_frame.grid(row=0,column=6,columnspan=5,sticky=tk.N+tk.S)
        self.event_entry.grid(row=3,column=2,sticky=tk.E+tk.W)
        self.plot_event_button.grid(row=4,column=2,sticky=tk.E+tk.W)
        self.event_info_display.grid(row=4,column=3,sticky=tk.W+tk.E)
        self.next_event_button.grid(row=3,column=3,sticky=tk.W)
        self.prev_event_button.grid(row=3,column=1,sticky=tk.E)
        self.delete_event_button.grid(row=3,column=4,sticky=tk.E+tk.W)


        #Datbase widgets

        self.db_frame = tk.LabelFrame(parent,text='Database Controls')
        
        self.filter_button = tk.Button(self.db_frame,text='Apply Filter',command=self.filter_db)
        self.reset_button = tk.Button(self.db_frame,text='Reset DB',command=self.reset_db)
        self.undo_button = tk.Button(self.db_frame,text='Undo Last',command=self.undo_filter_db)
        self.db_info_string = tk.StringVar()
        self.db_info_string.set('Number of events: ' +str(len(self.eventsdb_subset)))
        self.db_info_display = tk.Label(self.db_frame, textvariable=self.db_info_string)
        self.save_subset_button = tk.Button(self.db_frame,text='Save Subset',command=self.save_subset)
        self.filter_entry = tk.Entry(self.db_frame)
        
        self.filter_button.grid(row=1,column=2)
        self.reset_button.grid(row=1,column=3)
        
        self.db_frame.grid(row=3,column=6,columnspan=5,sticky=tk.E+tk.W+tk.S+tk.N)
        self.save_subset_button.grid(row=2,column=0,sticky=tk.E+tk.W)
        self.filter_entry.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.filter_button.grid(row=0,column=1,sticky=tk.E+tk.W)
        self.reset_button.grid(row=2,column=1,sticky=tk.E+tk.W)
        self.undo_button.grid(row=1,column=1,sticky=tk.E+tk.W)
        self.db_info_display.grid(row=1,column=0,sticky=tk.E+tk.W)

        #Folder widgets
        self.folder_frame = tk.LabelFrame(parent,text='Folder Options')

        self.stats_file_path = tk.StringVar()
        self.stats_file_path.set(self.file_path_string)
        self.stats_file_display = tk.Label(self.folder_frame, textvariable=self.stats_file_path)
        self.stats_file_label = tk.Label(self.folder_frame, text='Statistics File:')
        self.stats_file_button = tk.Button(self.folder_frame,text='Browse',command=self.open_stats_file)

        self.events_folder_path = tk.StringVar()
        self.events_folder_path.set(self.events_folder)
        self.events_folder_display = tk.Label(self.folder_frame, textvariable=self.events_folder_path)
        self.events_folder_label = tk.Label(self.folder_frame, text='Events Folder:')
        self.events_folder_button = tk.Button(self.folder_frame,text='Browse',command=self.set_events_folder)
        

        self.folder_frame.grid(row=3,column=0,columnspan=6,sticky=tk.E+tk.W+tk.S+tk.N)
        self.stats_file_label.grid(row=0,column=0,sticky=tk.E+tk.W,columnspan=2)
        self.events_folder_label.grid(row=1,column=0,sticky=tk.E+tk.W,columnspan=2)
        self.stats_file_display.grid(row=0,column=2,sticky=tk.E+tk.W,columnspan=2)
        self.events_folder_display.grid(row=1,column=2,sticky=tk.E+tk.W,columnspan=2)
        self.stats_file_button.grid(row=0,column=4,sticky=tk.E+tk.W,columnspan=2)
        self.events_folder_button.grid(row=1,column=4,sticky=tk.E+tk.W,columnspan=2)
        
    def filter_db(self):
        filterstring = self.filter_entry.get()
        self.eventsdb_prev = self.eventsdb_subset
        eventsdb_subset = self.eventsdb_subset
        tempdb = sqldf('SELECT * from eventsdb_subset WHERE %s' % filterstring,locals())
        self.eventsdb_subset = tempdb
        try:
            self.db_info_string.set('Number of events: ' +str(len(self.eventsdb_subset)))
        except TypeError:
            self.db_info_string.set('Invalid Entry')
            self.eventsdb_subset = self.eventsdb_prev

    def undo_filter_db(self):
        temp = self.eventsdb_subset
        self.eventsdb_subset = self.eventsdb_prev
        self.eventsdb_prev = temp
        self.db_info_string.set('Number of events: ' +str(len(self.eventsdb_subset)))

    def reset_db(self):
        self.eventsdb_prev = self.eventsdb_subset
        self.eventsdb_subset = self.eventsdb
        self.db_info_string.set('Number of events: ' +str(len(self.eventsdb_subset)))

    def plot_xy(self):
        logscale_x = self.x_log_var.get()
        logscale_y = self.y_log_var.get()
        x_label = self.x_option.cget('text')
        y_label = self.y_option.cget('text')
        x_col = self.parse_db_col(self.unalias_dict.get(x_label,x_label))
        y_col = self.parse_db_col(self.unalias_dict.get(y_label,y_label))
        xsign = np.sign(np.average(x_col))
        ysign = np.sign(np.average(y_col))
        self.f.clf()
        a = self.f.add_subplot(111)
        a.set_xlabel(x_label)
        a.set_ylabel(y_label)
        self.f.subplots_adjust(bottom=0.14,left=0.21)
        a.plot(xsign*x_col,ysign*y_col,marker='.',linestyle='None')
        if logscale_x:
            a.set_xscale('log')
        if logscale_y:
            a.set_yscale('log')
        self.canvas.show()

    def plot_1d_histogram(self):
        logscale_x = self.x_log_var.get()
        logscale_y = self.y_log_var.get()
        x_label = self.x_option.cget('text')
        col = self.parse_db_col(self.unalias_dict.get(x_label,x_label))
        numbins = self.xbin_entry.get()
        self.f.clf()
        a = self.f.add_subplot(111)
        if logscale_x:
            a.set_xlabel('Log(' +str(x_label)+')')
            a.set_ylabel('Count')
            self.f.subplots_adjust(bottom=0.14,left=0.21)
            sign = np.sign(np.average(col))
            a.hist(np.log10(sign*col),bins=int(numbins),log=bool(logscale_y))
        else:
            a.set_xlabel(x_label)
            a.set_ylabel('Count')
            self.f.subplots_adjust(bottom=0.14,left=0.16)
            a.hist(col,bins=int(numbins),log=bool(logscale_y))
        self.canvas.show()
        
    def plot_2d_histogram(self):
        logscale_x = self.x_log_var.get()
        logscale_y = self.y_log_var.get()
        x_label = self.x_option.cget('text')
        y_label = self.y_option.cget('text')
        x_col = self.parse_db_col(self.unalias_dict.get(x_label,x_label))
        y_col = self.parse_db_col(self.unalias_dict.get(y_label,y_label))
        xbins = self.xbin_entry.get()
        ybins = self.ybin_entry.get()
        self.f.clf()
        a = self.f.add_subplot(111)
        a.set_xlabel(x_label)
        a.set_ylabel(y_label)
        if logscale_x:
            a.set_xlabel('Log(' +str(x_label)+')')
        if logscale_y:
            a.set_ylabel('Log(' +str(y_label)+')')
        self.f.subplots_adjust(bottom=0.14,left=0.21)
        xsign = np.sign(np.average(x_col))
        ysign = np.sign(np.average(y_col))
        a.hist2d(np.log10(xsign*x_col) if bool(logscale_x) else x_col,np.log10(ysign*y_col) if bool(logscale_y) else y_col,bins=[int(xbins),int(ybins)],norm=matplotlib.colors.LogNorm())
        self.canvas.show()

    def disable_options(self, *args):
        option = self.graph_option.cget('text')
        if option == '1D Histogram':
            self.y_option['state']='disabled'
            self.ybin_entry['state']='disabled'
            self.xbin_entry['state']='normal'
        elif option == 'XY Plot':
            self.ybin_entry['state']='disabled'
            self.xbin_entry['state']='disabled'
            self.y_option['state']='normal'
        else:
            self.y_option['state']='normal'
            self.ybin_entry['state']='normal'
            self.xbin_entry['state']='normal'

    def update_plot(self):
        option = self.graph_option.cget('text')
        if option == 'XY Plot':
            self.plot_xy()
        elif option == '1D Histogram':
            self.plot_1d_histogram()
        elif option == '2D Histogram':
            self.plot_2d_histogram()
        else:
            pass

    def parse_db_col(self, col):
        if col in ['blockages_pA','level_current_pA','level_duration_us']:
            return_col = np.hstack([np.array(a,dtype=float)[1:-1] for a in self.eventsdb_subset[col].str.split(';')])
        else:
            return_col = self.eventsdb_subset[col]
        return return_col

    def plot_event(self):
        index = self.event_index.get()
        if any(self.eventsdb_subset['id']==index):
            event_file_path = self.events_folder+'/event_%05d.csv' % index
            try:
                event_file = pd.read_csv(event_file_path,encoding='utf-8')
            except IOError:
                self.event_info_string.set(event_file_path+' not found')
                return
            eventsdb_subset = self.eventsdb_subset
            event_type = sqldf('SELECT type from eventsdb_subset WHERE id=%d' % index,locals())['type'][0]
            if event_type == 0:
                event_file.columns = ['time','current','cusum']
            elif event_type == 1:
                event_file.columns = ['time','current','cusum','stepfit']
            self.event_f.clf()
            a = self.event_f.add_subplot(111)
            a.set_xlabel('Time (us)')
            a.set_ylabel('Current (pA)')
            self.event_f.subplots_adjust(bottom=0.14,left=0.21)
            if event_type == 0:
                a.plot(event_file['time'],event_file['current'],event_file['time'],event_file['cusum'])
            elif event_type == 1:
                a.plot(event_file['time'],event_file['current'],event_file['time'],event_file['cusum'],event_file['time'],event_file['stepfit'])
            self.event_canvas.show()
            self.event_info_string.set('')
        else:
            self.event_info_string.set('No such event!')

    def next_event(self):
        try:
            current_index = self.eventsdb_subset[self.eventsdb_subset['id'] == self.event_index.get()].index.tolist()[0]
        except IndexError:
            current_index = -1
        if current_index < len(self.eventsdb_subset)-1:
            self.event_index.set(int(self.eventsdb_subset['id'][current_index + 1]))
            self.plot_event()
        else:
            pass
            

    def prev_event(self):
        try:
            current_index = self.eventsdb_subset[self.eventsdb_subset['id'] == self.event_index.get()].index.tolist()[0]
        except IndexError:
            current_index = 1
        if current_index > 0:
            self.event_index.set(int(self.eventsdb_subset['id'][current_index - 1]))
            self.plot_event()
        else:
            pass

    def delete_event(self):
        event_index = self.event_index.get()
        try:
            current_index = self.eventsdb_subset[self.eventsdb_subset['id'] == self.event_index.get()].index.tolist()[0]
        except IndexError:
            self.event_info_string.set('No such event!')
            current_index = -1
        if current_index < len(self.eventsdb_subset)-1:
            self.next_event()
        elif current_index > 0:
            self.prev_event()
        else:
            self.event_index.set(self.eventsdb_subset['id'][0])
            self.plot_event()
        eventsdb_subset = self.eventsdb_subset
        self.eventsdb_subset = sqldf('SELECT * from eventsdb_subset WHERE id != %d' % event_index,locals())
        self.db_info_string.set('Number of events: ' +str(len(self.eventsdb_subset)))

    def right_key_press(self, event):
        self.next_event()

    def left_key_press(self, event):
        self.prev_event()

    def delete_key_press(self,event):
        self.delete_event()

    def enter_key_press(self,event):
        self.update_plot()

    def alias_columns(self):
        self.alias_dict = {'id': 'Event Number',
                      'type': 'Event Type',
                      'start_time_s': 'Start Time (s)',
                      'duration_us': 'Dwell Time (us)',
                      'threshold': 'Threshold (unitless)',
                      'event_delay_s': 'Time Since Last Event (s)',
                      'baseline_before_pA': 'Baseline Before (pA)',
                      'baseline_after_pA': 'Baseline After (pA)',
                      'effective_baseline_pA': 'Baseline (pA)',
                      'area_pC': 'Equivalent Charge Deficit (pC)',
                      'average_blockage_pA': 'Average Blockage (pA)',
                      'relative_average_blockage': 'Relative Average Blockage (unitless)',
                      'max_blockage_pA': 'Maximum Blockage (pA)',
                      'relative_max_blockage': 'Relative Maximum Blockage (unitless)',
                      'max_blockage_duration_us': 'Maximum Blockage Duration (us)',
                      'n_levels': 'Number of Levels',
                      'rc_const1_us': 'RC Constant 1 (us)',
                      'rc_const2_us': 'RC Constant 2 (us)',
                      'level_current_pA': 'Level Current (pA)',
                      'level_duration_us': 'Level Duration (us)',
                      'blockages_pA': 'Blockage Level (pA)',
                      'residuals_pA': 'Residuals (pA)'}
        self.unalias_dict = dict (zip(self.alias_dict.values(),self.alias_dict.keys()))

    def save_subset(self):
        folder = os.path.dirname(os.path.abspath(self.file_path_string))
        subset_file_path = folder + '\eventsdb-subset.csv'
        subset_file = open(subset_file_path,'wb')
        self.eventsdb_subset.to_csv(subset_file,index=False)
        subset_file.close()

    def open_stats_file(self):
        self.file_path_string = tkFileDialog.askopenfilename(initialdir='C:\Users\kbrig035\Analysis\CUSUM\output\\')
        self.stats_file_path.set(self.file_path_string)
        self.eventsdb = pd.read_csv(self.file_path_string,encoding='utf-8')
        self.eventsdb_subset = self.eventsdb
        self.eventsdb_prev = self.eventsdb
        self.db_info_string.set('Number of events: ' +str(len(self.eventsdb_subset)))
        

    def set_events_folder(self):
        self.events_folder = tkFileDialog.askdirectory(initialdir='C:\Users\kbrig035\Analysis\CUSUM\output\\')
        self.events_folder_path.set(self.events_folder)

def main():
    root=tk.Tk()
    root.withdraw()
    file_path_string = tkFileDialog.askopenfilename(initialdir='C:/Users/kbrig035/Analysis/CUSUM/output/')
    folder = os.path.dirname(os.path.abspath(file_path_string))
    folder = folder + '\events\\'
    root.wm_title("CUSUM Tools")
    eventsdb = pd.read_csv(file_path_string,encoding='utf-8')
    column_list = list(eventsdb)
    App(root,eventsdb,column_list,folder,file_path_string).grid(row=0,column=0)
    root.mainloop()

if __name__=="__main__":
    main()

