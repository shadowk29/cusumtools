import pandas as pd
from pandasql import sqldf
import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import pylab as pl
import tkFileDialog
import Tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

def parse_semicolon_list(eventsdb,cols):
    for col in cols:
        eventsdb[col] = [np.array(a,dtype=float) for a in eventsdb[col].str.split(';')]
    
class App(tk.Frame):
    def __init__(self, parent,eventsdb,column_list):
        tk.Frame.__init__(self, parent)
        self.eventsdb = eventsdb
        self.eventsdb_subset = eventsdb
        self.column_list = column_list
        self.x_col_options = tk.StringVar()
        self.x_col_options.set('Select X')
        self.y_col_options = tk.StringVar()
        self.y_col_options.set('Select Y')
        self.graph_list = tk.StringVar()
        self.graph_list.set('Graph Type')
        parent.deiconify()
        
        self.filter_button = tk.Button(parent,text='Apply Filter',command=self.filter_db)
        self.reset_button = tk.Button(parent,text='Reset DB',command=self.reset_db)
        self.plot_button = tk.Button(parent,text='Update Plot',command=self.update_plot)
        

        self.x_option = tk.OptionMenu(parent, self.x_col_options, *self.column_list)
        self.y_option = tk.OptionMenu(parent, self.y_col_options, *self.column_list)
        self.graph_option = tk.OptionMenu(parent, self.graph_list, 'XY Plot', '1D Histogram', '2D Histogram', command=self.disable_options)

        self.db_info_string = tk.StringVar()
        self.db_info_string.set('Number of events: ' +str(len(self.eventsdb_subset)))
        self.db_info_display = tk.Label(parent, textvariable=self.db_info_string)
        
        self.f = Figure(figsize=(5,4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.f, master=parent)
        

        self.toolbar_frame = tk.Frame(parent)
        
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.toolbar_frame)
        self.toolbar.update()

        
        self.filter_entry = tk.Entry(parent)
        self.filter_label=tk.Label(parent,text='DB Filter String:')
        self.x_bins=tk.Label(parent,text='X Bins:')
        self.y_bins=tk.Label(parent,text='Y Bins:')

        self.xbin_entry = tk.Entry(parent)
        self.xbin_entry.insert(0,10)
        self.ybin_entry = tk.Entry(parent)
        self.ybin_entry.insert(0,10)
        
        self.x_bins.grid(row=3,column=2)
        self.y_bins.grid(row=4,column=2)
        self.xbin_entry.grid(row=3,column=3)
        self.ybin_entry.grid(row=4,column=3)
        
        self.graph_option.grid(row=3,column=0,rowspan=2)
        self.x_option.grid(row=3,column=1)
        self.y_option.grid(row=4,column=1)
        
        self.filter_button.grid(row=1,column=2)
        self.reset_button.grid(row=1,column=3)
        
        self.plot_button.grid(row=3,column=4,rowspan=2)

        self.toolbar_frame.grid(row=1,column=0,columnspan=5)
        self.canvas.get_tk_widget().grid(row=0,column=0,columnspan=5)
        
        self.filter_label.grid(row=2,column=0)
        self.filter_entry.grid(row=2,column=1)
        self.filter_button.grid(row=2,column=2)
        self.reset_button.grid(row=2,column=3)
        self.db_info_display.grid(row=2,column=4)


        
    def filter_db(self):
        filterstring = self.filter_entry.get()
        eventsdb_subset = self.eventsdb_subset
        self.eventsdb_subset = sqldf('SELECT * from eventsdb_subset WHERE %s' % filterstring,locals())
        self.db_info_string.set('Number of events: ' +str(len(self.eventsdb_subset)))

    def reset_db(self):
        self.eventsdb_subset = self.eventsdb
        self.db_info_string.set('Number of events: ' +str(len(self.eventsdb_subset)))

    def plot_xy(self):
        x_col = self.x_option.cget('text')
        y_col = self.y_option.cget('text')
        self.f.clf()
        a = self.f.add_subplot(111)
        a.set_xlabel(x_col)
        a.set_ylabel(y_col)
        self.f.subplots_adjust(bottom=0.14,left=0.16)
        a.plot(self.eventsdb_subset[x_col],self.eventsdb_subset[y_col])
        self.canvas.show()

    def plot_1d_histogram(self):
        col = self.x_option.cget('text')
        self.f.clf()
        a = self.f.add_subplot(111)
        a.set_xlabel(col)
        a.set_ylabel('Count')
        self.f.subplots_adjust(bottom=0.14,left=0.16)
        a.hist(self.eventsdb_subset[col])
        self.canvas.show()
        
    def plot_2d_histogram(self):
        x_col = self.x_option.cget('text')
        y_col = self.y_option.cget('text')
        self.f.clf()
        a = self.f.add_subplot(111)
        a.set_xlabel(x_col)
        a.set_ylabel(y_col)
        self.f.subplots_adjust(bottom=0.14,left=0.16)
        a.hexbin(self.eventsdb_subset[x_col],self.eventsdb_subset[y_col])
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


       
def main():
    root=tk.Tk()
    root.withdraw()
    file_path_string = tkFileDialog.askopenfilename(initialdir='C:\Users\kbrig035\Analysis\CUSUM\output\\')
    eventsdb = pd.read_csv(file_path_string,encoding='utf-8')
    column_list = list(eventsdb)
    App(root,eventsdb,column_list).grid(row=0,column=0)
    root.mainloop()

if __name__=="__main__":
    main()

