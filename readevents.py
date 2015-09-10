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
        self.col_options = tk.StringVar()
        self.col_options.set('Select X')
        
        parent.deiconify()
        
        self.print_button = tk.Button(parent,text='Print DB', command=self.print_events_db)
        self.filter_button = tk.Button(parent,text='Apply Filter',command=self.filter_db)
        self.plot_button = tk.Button(parent,text='Plot XY Graph',command=self.plot_xy)
        self.hist1d_button = tk.Button(parent,text='Plot 1D Histogram',command=self.plot_1d_histogram)
        self.hist2d_button = tk.Button(parent,text='Plot 2D Histogram',command=self.plot_2d_histogram)
        

        self.x_option = tk.OptionMenu(parent, self.col_options, *self.column_list, command=self.test)

        self.db_info_string = tk.StringVar()
        self.db_info_string.set('Number of events: ' +str(len(self.eventsdb_subset)))
        self.db_info_display = tk.Label(parent, textvariable=self.db_info_string)
        
        self.f = Figure(figsize=(5,4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.f, master=parent)
        self.canvas.get_tk_widget().grid(row=6,column=0,columnspan=5)

        toolbar_frame = tk.Frame(parent)
        toolbar_frame.grid(row=7,column=0,columnspan=5)
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, toolbar_frame)
        self.toolbar.update()

        self.x_entry = tk.Entry(parent)
        self.y_entry = tk.Entry(parent)
        self.filter_entry = tk.Entry(parent)
        filter_label=tk.Label(parent,text='DB Filter String:')
        x_label=tk.Label(parent,text='X Column:')
        y_label=tk.Label(parent,text='Y Column:')
        
        filter_label.grid(row=1,column=0)
        x_label.grid(row=2,column=0)
        y_label.grid(row=3,column=0)
        self.filter_entry.grid(row=1,column=1)
        self.x_entry.grid(row=2,column=1)
        self.y_entry.grid(row=3,column=1)

        self.x_option.grid(row=0,column=0)
        self.print_button.grid(row=0,column=1)
        self.filter_button.grid(row=1,column=2)
        self.db_info_display.grid(row=1,column=3)
        self.plot_button.grid(row=3,column=2)
        self.hist1d_button.grid(row=2,column=2)
        self.hist2d_button.grid(row=3,column=3)

        
        
        

    def print_events_db(self):
        print self.eventsdb_subset
        
    def filter_db(self):
        filterstring = self.filter_entry.get()
        print filterstring
        eventsdb_subset = self.eventsdb_subset
        self.eventsdb_subset = sqldf('SELECT * from eventsdb_subset WHERE %s' % filterstring,locals())
        self.db_info_string.set('Number of events: ' +str(len(eventsdb_subset)))

    def plot_xy(self):
        x_col = self.x_entry.get()
        y_col = self.y_entry.get()
        self.f.clf()
        a = self.f.add_subplot(111)
        a.set_xlabel(x_col)
        a.set_ylabel(y_col)
        self.f.subplots_adjust(bottom=0.14,left=0.16)
        a.plot(self.eventsdb_subset[x_col],self.eventsdb_subset[y_col])
        self.canvas.show()

    def plot_1d_histogram(self):
        col = self.x_entry.get()
        self.f.clf()
        a = self.f.add_subplot(111)
        a.set_xlabel(col)
        a.set_ylabel('Count')
        self.f.subplots_adjust(bottom=0.14,left=0.16)
        a.hist(self.eventsdb_subset[col])
        self.canvas.show()
        
    def plot_2d_histogram(self):
        x_col = self.x_entry.get()
        y_col = self.y_entry.get()
        self.f.clf()
        a = self.f.add_subplot(111)
        a.set_xlabel(x_col)
        a.set_ylabel(y_col)
        self.f.subplots_adjust(bottom=0.14,left=0.16)
        a.hist2d(self.eventsdb_subset[x_col],self.eventsdb_subset[y_col])
        self.canvas.show()

    def test(self, *args):
        print self.x_option.cget('text')
        #self.hist1d_button['state']='disabled'
        
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

