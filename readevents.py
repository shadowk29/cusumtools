##                                COPYRIGHT
##    Copyright (C) 2015 Kyle Briggs (kbrig035<at>uottawa.ca)
##
##    This file is part of cusumtools.
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

import pandas as pd
from pandasql import sqldf
import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import os
import tkinter.filedialog
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy.optimize import curve_fit
import itertools
from collections import OrderedDict
from scipy.stats import t, median_absolute_deviation
import pylab as pl
import re
from tkinter import ttk
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
import hdbscan
##matplotlib inline
sns.set_context('poster')
sns.set_style('white')
sns.set_color_codes()
plot_kwds = {'alpha' : 0.5, 's' : 80, 'linewidths':0}
matplotlib.rcParams['figure.constrained_layout.use'] = True
pd.options.mode.chained_assignment = None  # default='warn'

class FlashableLabel(tk.Label):
    def flash(self,count):
        bg = self.cget('background')
        fg = self.cget('foreground')
        self.configure(background=fg,foreground=bg)
        count -=1
        if (count > 0):
             self.after(500,self.flash, count)
             
class App(tk.Frame):
    def __init__(self,parent,eventsdb,ratedb,summary,events_folder,file_path_string):
        tk.Frame.__init__(self, parent)
        parent.deiconify()
        self.parent = parent
        self.initialize_database(eventsdb, ratedb, summary, events_folder, file_path_string)
        #initialize the layout of the GUI
        self.layout_stats_panel()
        self.layout_notebook_tabs()
        self.layout_db_panel()
        self.layout_status_panel()
        
        
#######################################

    def layout_status_panel(self):
        self.status_frame = tk.LabelFrame(self.parent, text='Status')
        self.status_frame.grid(row=1,column=1,sticky=tk.E+tk.W)

        self.status_string = tk.StringVar()
        self.status_string.set('Ready')
        self.status_display = FlashableLabel(self.status_frame, textvariable=self.status_string, background='black', foreground='white')

        self.status_display.grid(row=0,column=0,columnspan=6,sticky=tk.E+tk.W)

        
    def initialize_database(self, eventsdb, ratedb, summary, events_folder, file_path_string):
        #initialize event database files
        self.file_path_string = file_path_string
        self.events_folder = events_folder

        self.eventsdb = eventsdb
        [a,b] = self.eventsdb.shape
        self.eventsdb['adj_id'] = np.arange(0,a)
        self.clicks_remaining = 0
        self.ratedb = ratedb

        #initialize subset and plot options
        self.max_subsets = 11
        self.eventsdb_subset = dict(('Subset {0}'.format(i), self.eventsdb) for i in range(self.max_subsets))
        self.capture_rate_subset = dict.fromkeys(list(self.eventsdb_subset.keys()))
        self.filter_list = dict(('Subset {0}'.format(i), []) for i in range(self.max_subsets))
        self.plot_list = dict(('Subset {0}'.format(i), 0) for i in range(self.max_subsets))
        self.plot_list['Subset 0'] = 1
        self.init_plot_list = self.plot_list.copy()
        self.good_event_subset = []

        #initialize single event plotting options
        self.intra_threshold = 0
        self.intra_hysteresis = 0
        for line in summary:
            if 'intra_threshold' in line:
                line = re.split('=|\n',line)
                self.intra_threshold = float(line[1])
            if 'intra_hysteresis' in line:
                line = re.split('=|\n',line)
                self.intra_hysteresis = float(line[1])
        summary.close()

        #initialize columns that may be calculated during analysis if they do not already exists in the database file
        if 'event_shape' not in eventsdb.columns:
            eventsdb['event_shape']=""
        if 'trimmed_shape' not in eventsdb.columns:
            eventsdb['trimmed_shape']=""
        if 'trimmed_n_levels' not in eventsdb.columns:    
            eventsdb['trimmed_n_levels']=""
        if 'first_level' not in eventsdb.columns:
            eventsdb['first_level']=""
            eventsdb['last_level']=""
        if 'first_level_fraction' not in eventsdb.columns:
            eventsdb['first_level_fraction']=""
        if 'cluster_id' not in eventsdb.columns:
            eventsdb['cluster_id']=""
        
        #calculate new columns as needed
        self.first_level_fraction()
        self.folding_distribution()
        self.count()
        self.export_type = None
        self.manual_delete = []
        
        #initialize list of features that can be plotted
        column_list = list(eventsdb)
        self.column_list = column_list
        self.x_col_options = tk.StringVar()
        self.x_col_options.set('Level Duration (us)')
        self.y_col_options = tk.StringVar()
        self.y_col_options.set('Blockage Level (pA)')
        self.graph_list = tk.StringVar()
        self.graph_list.set('2D Histogram')
        self.alias_columns()
        
    def layout_stats_panel(self):
        #define and position the main panel on the left
        self.stats_container = tk.Frame(self.parent)
        self.stats_container.grid(row=0, column=0)
        self.stats_frame = tk.LabelFrame(self.stats_container, text='Statistics')
        self.stats_frame.grid(row=0,column=0)

        #Left panel children
        #define a figure canvas to go in the left panel
        self.stats_f = Figure(figsize=(7,5), dpi=100)
        self.stats_canvas = FigureCanvasTkAgg(self.stats_f, master=self.stats_frame)
        self.stats_toolbar_frame = tk.Frame(self.stats_frame)
        self.stats_toolbar = NavigationToolbar2Tk(self.stats_canvas, self.stats_toolbar_frame)
        self.stats_toolbar.update()
        self.stats_canvas.get_tk_widget().grid(row=0,column=0)
        self.stats_toolbar_frame.grid(row=1,column=0)

        #define a control panel for the left panel to go below the figure
        
        self.stats_control_frame = tk.LabelFrame(self.stats_container, text='Plotting Control')
        self.stats_control_frame.grid(row=1,column=0, sticky=tk.E+tk.W)

        self.plot_button = tk.Button(self.stats_control_frame,text='Update Plot',command=self.update_plot)
        self.export_plot_button = tk.Button(self.stats_control_frame,text='Export Data',command=self.export_plot_data)
        self.x_option = tk.OptionMenu(self.stats_control_frame, self.x_col_options, *[self.alias_dict.get(option,option) for option in self.column_list])
        self.y_option = tk.OptionMenu(self.stats_control_frame, self.y_col_options, *[self.alias_dict.get(option,option) for option in self.column_list])
        self.graph_option = tk.OptionMenu(self.stats_control_frame, self.graph_list, 'XY Plot', '1D Histogram', '2D Histogram', command=self.disable_options)
        self.include_baseline=tk.IntVar()
        self.include_baseline_check = tk.Checkbutton(self.stats_control_frame, text='Include Baseline', variable=self.include_baseline)
        self.x_log_var = tk.IntVar()
        self.x_log_check = tk.Checkbutton(self.stats_control_frame, text='Log X', variable = self.x_log_var)
        self.y_log_var = tk.IntVar()
        self.y_log_check = tk.Checkbutton(self.stats_control_frame, text='Log Y', variable = self.y_log_var)

        self.x_bins=tk.Label(self.stats_control_frame,text='X Bins:')
        self.y_bins=tk.Label(self.stats_control_frame,text='Y Bins:')

        self.xbin_entry = tk.Entry(self.stats_control_frame)
        self.xbin_entry.insert(0,100)
        self.ybin_entry = tk.Entry(self.stats_control_frame)
        self.ybin_entry.insert(0,100)

        self.n_states=tk.Label(self.stats_control_frame,text='Num States:')
        self.n_states_entry = tk.Entry(self.stats_control_frame)
        self.define_state_button = tk.Button(self.stats_control_frame,text='Redefine Blockage States',command=self.define_states)
        self.define_event_shapes_button = tk.Button(self.stats_control_frame,text='Redefine Event Shapes',command=self.define_shapes)


        self.x_log_check.grid(row=3,column=2,sticky=tk.E+tk.W)
        self.y_log_check.grid(row=4,column=2,sticky=tk.E+tk.W)
        self.x_bins.grid(row=3,column=3,sticky=tk.E+tk.W)
        self.y_bins.grid(row=4,column=3,sticky=tk.E+tk.W)
        self.xbin_entry.grid(row=3,column=4,sticky=tk.E+tk.W)
        self.ybin_entry.grid(row=4,column=4,sticky=tk.E+tk.W)
        self.graph_option.grid(row=3,column=0,sticky=tk.E+tk.W)
        self.include_baseline_check.grid(row=4,column=0,sticky=tk.E+tk.W)
        self.x_option.grid(row=3,column=1,sticky=tk.E+tk.W)
        self.y_option.grid(row=4,column=1,sticky=tk.E+tk.W)
        self.plot_button.grid(row=3,column=5,sticky=tk.E+tk.W)
        self.export_plot_button.grid(row=4,column=5,sticky=tk.E+tk.W)

        self.parent.bind("<Return>", self.enter_key_press)


        self.n_states.grid(row=5,column=0,sticky=tk.E+tk.W)
        self.n_states_entry.grid(row=5,column=1,sticky=tk.E+tk.W)
        self.define_state_button.grid(row=5,column=2,sticky=tk.E+tk.W)
        self.define_event_shapes_button.grid(row=5,column=3,sticky=tk.E+tk.W)



        self.parent.bind("<Control-Key>", self.key_press)

    def layout_notebook_tabs(self):
        #define and position the tab-enabled secondary panel on the right
        self.ntbk = ttk.Notebook(self.parent)
        self.ntbk.grid(row=0,column=1)

        #cluster container
        self.cluster_container= tk.Frame(self.ntbk)
        self.cluster_container.grid(row=0,column=0)
        self.ntbk.add(self.cluster_container, text='Clustering')
        self.cluster_frame = tk.LabelFrame(self.cluster_container, text='Clustering')
        self.cluster_frame.grid(row=0,column=0)

        #capture rate container
        self.rate_container = tk.Frame(self.ntbk)
        self.rate_container.grid(row=0, column=0)
        self.ntbk.add(self.rate_container, text='Capture Rate')
        self.rate_frame = tk.LabelFrame(self.rate_container, text='Capture Rate')
        self.rate_frame.grid(row=0,column=0)

        #single event view container
        self.event_container = tk.Frame(self.ntbk)
        self.event_container.grid(row=0, column=0)
        self.ntbk.add(self.event_container, text='Event Viewer')
        self.event_frame = tk.LabelFrame(self.event_container, text='Event Viewer')
        self.event_frame.grid(row=0,column=0)

        self.layout_cluster_tab()
        self.layout_rate_tab()
        self.layout_event_tab()

    def layout_cluster_tab(self):
        #cluster figure
        self.cluster_f = Figure(figsize=(7,5), dpi=100)
        self.cluster_canvas = FigureCanvasTkAgg(self.cluster_f, master=self.cluster_frame)
        self.cluster_toolbar_frame = tk.Frame(self.cluster_frame)
        self.cluster_toolbar = NavigationToolbar2Tk(self.cluster_canvas, self.cluster_toolbar_frame)
        self.cluster_toolbar.update()
        self.cluster_canvas.get_tk_widget().grid(row=0,column=0)
        self.cluster_toolbar_frame.grid(row=1,column=0)

        #cluster control panel
        self.cluster_controls_frame = tk.LabelFrame(self.cluster_container, text='Cluster Controls')
        self.cluster_controls_frame.grid(row=1,column=0, sticky=tk.E+tk.W)


        self.min_cluster_pts_label = tk.Label(self.cluster_controls_frame, text='Min Cluster Size')
        self.min_pts_label = tk.Label(self.cluster_controls_frame, text='Min Neighbours')
        self.eps_label = tk.Label(self.cluster_controls_frame, text='Distance Cutoff')
        self.min_cluster_pts = tk.IntVar()
        self.min_cluster_pts.set(30)
        self.min_pts = tk.IntVar()
        self.min_pts.set(5)
        self.eps = tk.DoubleVar()
        self.eps.set(0)
        self.min_cluster_pts_entry = tk.Entry(self.cluster_controls_frame, textvariable=self.min_cluster_pts)
        self.min_pts_entry = tk.Entry(self.cluster_controls_frame, textvariable=self.min_pts)
        self.eps_entry = tk.Entry(self.cluster_controls_frame, textvariable=self.eps)


        self.feature_col_options = []
        self.feature_col_options.append(tk.StringVar())
        self.feature_col_options[0].set('Dwell Time (us)')
        self.feature_col_options.append(tk.StringVar())
        self.feature_col_options[1].set('Maximum Blockage (pA)')

        self.featurelabel = tk.Label(self.cluster_controls_frame, text='Feature')
        self.loglabel = tk.Label(self.cluster_controls_frame, text='Log')
        self.plotlabel = tk.Label(self.cluster_controls_frame, text='Plot')
        self.normlabel = tk.Label(self.cluster_controls_frame, text='Normalization')
        self.dellabel = tk.Label(self.cluster_controls_frame, text='Delete')

        
        
        self.feature_options = []
        self.feature_options.append(tk.OptionMenu(self.cluster_controls_frame, self.feature_col_options[0], *[self.alias_dict.get(option,option) for option in self.column_list]))
        self.feature_options.append(tk.OptionMenu(self.cluster_controls_frame, self.feature_col_options[1], *[self.alias_dict.get(option,option) for option in self.column_list]))

        self.feature_options_log = []
        self.feature_options_log.append(tk.IntVar())
        self.feature_options_log.append(tk.IntVar())

        self.feature_options_log_check = []
        self.feature_options_log_check.append(tk.Checkbutton(self.cluster_controls_frame, text='', variable = self.feature_options_log[0]))
        self.feature_options_log_check.append(tk.Checkbutton(self.cluster_controls_frame, text='', variable = self.feature_options_log[1]))

        self.plot_options = []
        self.plot_options.append(tk.IntVar())
        self.plot_options.append(tk.IntVar())
        self.plot_options[0].set(1)
        self.plot_options[1].set(1)

        self.plot_options_check = []
        self.plot_options_check.append(tk.Checkbutton(self.cluster_controls_frame, text='', variable = self.plot_options[0], command=self.disable_plots))
        self.plot_options_check.append(tk.Checkbutton(self.cluster_controls_frame, text='', variable = self.plot_options[1], command=self.disable_plots))

        self.feature_norms = []
        self.feature_norms.append(tk.StringVar())
        self.feature_norms.append(tk.StringVar())
        self.feature_norms[0].set('Max')
        self.feature_norms[1].set('Max')
        self.normalization_options = ['Max', 'Gauss', 'MAD', 'None']
        self.norm_options = []
        self.norm_options.append(tk.OptionMenu(self.cluster_controls_frame, self.feature_norms[0], *self.normalization_options))
        self.norm_options.append(tk.OptionMenu(self.cluster_controls_frame, self.feature_norms[1], *self.normalization_options))

        
        self.add_feature_button = tk.Button(self.cluster_controls_frame, text='Add Feature', command=self.add_feature)
        self.delete_feature_button = []

        self.min_cluster_pts_label.grid(row=0,column=0,stick=tk.E+tk.W)
        self.min_pts_label.grid(row=1,column=0,stick=tk.E+tk.W)
        self.eps_label.grid(row=2,column=0,stick=tk.E+tk.W)
        self.min_cluster_pts_entry.grid(row=0,column=1,columnspan=2,sticky=tk.E+tk.W)
        self.min_pts_entry.grid(row=1,column=1,columnspan=2,sticky=tk.E+tk.W)
        self.eps_entry.grid(row=2,column=1,columnspan=2,sticky=tk.E+tk.W)


        sept = ttk.Separator(self.cluster_controls_frame, orient='horizontal')
        sept.grid(row=3,column=0,columnspan=5,sticky=tk.E+tk.W)
        self.featurelabel.grid(row=4,column=0,sticky=tk.E+tk.W)
        self.loglabel.grid(row=4,column=1,sticky=tk.E+tk.W)
        self.plotlabel.grid(row=4,column=2,sticky=tk.E+tk.W)
        self.normlabel.grid(row=4,column=3,sticky=tk.E+tk.W)
        self.dellabel.grid(row=4,column=4,sticky=tk.E+tk.W)
        sepb = ttk.Separator(self.cluster_controls_frame, orient='horizontal')
        sepb.grid(row=5,column=0,columnspan=5,sticky=tk.E+tk.W)

        
        self.gridcounter = 6
        for f,c,p,n in zip(self.feature_options, self.feature_options_log_check, self.plot_options_check, self.norm_options):
            f.grid(row=self.gridcounter, column=0, sticky=tk.E+tk.W)
            c.grid(row=self.gridcounter, column=1, sticky=tk.E+tk.W)
            p.grid(row=self.gridcounter, column=2, sticky=tk.E+tk.W)
            n.grid(row=self.gridcounter, column=3, sticky=tk.E+tk.W)
            self.gridcounter += 1
        self.add_feature_button.grid(row=self.gridcounter, column=0, columnspan=5,sticky=tk.E+tk.W)

        self.update_cluster_button = tk.Button(self.cluster_controls_frame, text='Update Clusters', command=self.update_cluster)
        self.update_cluster_button.grid(row=0,column=3,columnspan=2,sticky=tk.E+tk.W+tk.N+tk.S)
        
        default_cluster_subset = tk.StringVar()
        default_cluster_subset.set('Subset 0')
        cluster_subset_options = ['Subset {0}'.format(i) for i in range(self.max_subsets)]
        self.cluster_subset_option = tk.OptionMenu(self.cluster_controls_frame, default_cluster_subset, *cluster_subset_options)
        self.cluster_subset_option.grid(row=2,column=3,columnspan=2, sticky=tk.E+tk.W)
        
    

    def layout_rate_tab(self):
        #capture rate figure
        self.rate_f = Figure(figsize=(7,5), dpi=100)
        self.rate_canvas = FigureCanvasTkAgg(self.rate_f, master=self.rate_frame)
        self.rate_toolbar_frame = tk.Frame(self.rate_frame)
        self.rate_toolbar = NavigationToolbar2Tk(self.rate_canvas, self.rate_toolbar_frame)
        self.rate_toolbar.update()
        self.rate_canvas.get_tk_widget().grid(row=0,column=0)
        self.rate_toolbar_frame.grid(row=1,column=0)

        #capture rate control panel
        self.rate_control_frame = tk.LabelFrame(self.rate_container, text='Capture Rate Controls')
        self.rate_control_frame.grid(row=1,column=0, sticky=tk.E+tk.W)


        self.plot_subsets = tk.Button(self.rate_control_frame, text='Subsets to Plot',command=self.plot_subset_select)
        self.plot_subsets.grid(row=0,column=0,sticky=tk.E+tk.W)

        self.good_events = tk.Button(self.rate_control_frame, text='Good events',command=self.declare_good_events)
        self.good_events.grid(row=0,column=1,sticky=tk.E+tk.W)

        self.capture_rate_button = tk.Button(self.rate_control_frame,text='Fit Capture Rate',command=self.capture_rate)
        self.capture_rate_button.grid(row=5,column=4,sticky=tk.E+tk.W)
        self.use_histogram = tk.IntVar()
        self.use_histogram_check = tk.Checkbutton(self.rate_control_frame, text='Use Histogram', variable = self.use_histogram)
        self.use_histogram_check.grid(row=5,column=5,sticky=tk.E+tk.W)
        

        
    def layout_event_tab(self):
        #single event view figure
        self.event_f = Figure(figsize=(7,5), dpi=100)
        self.event_canvas = FigureCanvasTkAgg(self.event_f, master=self.event_frame)
        self.event_toolbar_frame = tk.Frame(self.event_frame)
        self.event_toolbar = NavigationToolbar2Tk(self.event_canvas, self.event_toolbar_frame)
        self.event_toolbar.update()
        self.event_canvas.get_tk_widget().grid(row=0,column=0)
        self.event_toolbar_frame.grid(row=1,column=0)

        #single event control panel
        self.event_control_frame = tk.LabelFrame(self.event_container, text='Event View Controls')
        self.event_control_frame.grid(row=1,column=0, sticky=tk.E+tk.W)

        self.event_info_string = tk.StringVar()
        self.event_index = tk.IntVar()
        self.event_index.set(self.eventsdb_subset['Subset 0']['id'][0])
        self.event_entry = tk.Entry(self.event_control_frame, textvariable=self.event_index)
        self.plot_event_button = tk.Button(self.event_control_frame,text='Plot Event',command=self.plot_event)
        self.next_event_button = tk.Button(self.event_control_frame,text='Next',command=self.next_event)
        self.prev_event_button = tk.Button(self.event_control_frame,text='Prev',command=self.prev_event)
        self.delete_event_button = tk.Button(self.event_control_frame,text='Delete',command=self.delete_event)
        self.replicate_delete = tk.Button(self.event_control_frame,text='Replicate Deletions',command=self.replicate_manual_deletions)
        self.save_event_button = tk.Button(self.event_control_frame,text='Export Data',command=self.export_event_data)
        self.event_info_string.set('Ready')
        self.event_info_display = tk.Label(self.event_control_frame, textvariable=self.event_info_string)
        self.plot_bad_events = tk.IntVar(0)
        self.plot_bad_events_check = tk.Checkbutton(self.event_control_frame, text='Plot Bad Events', variable = self.plot_bad_events)
        
        self.event_toolbar_frame.grid(row=1,column=0,columnspan=6)
        self.event_canvas.get_tk_widget().grid(row=0,column=0,columnspan=6)
        
        self.parent.bind("<Left>", self.left_key_press)
        self.parent.bind("<Right>", self.right_key_press)
        self.parent.bind("<Delete>", self.delete_key_press)

        self.event_entry.grid(row=2,column=0,columnspan=2,sticky=tk.E+tk.W)
        self.event_info_display.grid(row=2,column=2,columnspan=2,sticky=tk.W+tk.E)
        self.plot_event_button.grid(row=3,column=0,columnspan=2,sticky=tk.E+tk.W)
        self.save_event_button.grid(row=3,column=2,columnspan=2,sticky=tk.E+tk.W)
        self.next_event_button.grid(row=4,column=2,columnspan=2,sticky=tk.E+tk.W)
        self.prev_event_button.grid(row=4,column=0,columnspan=2,sticky=tk.E+tk.W)
        self.delete_event_button.grid(row=5,column=0,columnspan=2,sticky=tk.E+tk.W)
        self.replicate_delete.grid(row=5,column=2,columnspan=2,sticky=tk.E+tk.W)
        self.plot_bad_events_check.grid(row=4,column=4,columnspan=2,stick=tk.E+tk.W)


        

    def layout_db_panel(self):
        ##database control panel
        self.db_frame = tk.LabelFrame(self.parent, text='Database Controls')
        self.db_frame.grid(row=1,column=0,sticky=tk.E+tk.W)


        self.filter_entry = tk.Entry(self.db_frame)
        self.filter_entry.grid(row=0, column=0, sticky=tk.E+tk.W)

        default_subset = tk.StringVar()
        default_subset.set('Subset 0')
        options = ['Subset {0}'.format(i) for i in range(self.max_subsets)]
        self.subset_option = tk.OptionMenu(self.db_frame, default_subset, *options,command=self.update_count)
        self.filter_button = tk.Button(self.db_frame,text='Filter Subset',command=self.filter_db)
        self.reset_button = tk.Button(self.db_frame,text='Reset Subset',command=self.reset_db)
        self.draw_subset_details_button = tk.Button(self.db_frame, text='Display Filters', command=self.display_filters)
        self.save_subset_button = tk.Button(self.db_frame,text='Save Subset',command=self.save_subset)
        self.remove_nonconsecutive_button = tk.Button(self.db_frame,text='Remove Non-Consecutive',command=self.remove_nonconsecutive_events)
        self.filter_entry = tk.Entry(self.db_frame)

        
        self.filter_entry.grid(row=0,column=0,columnspan=6,sticky=tk.E+tk.W)
        self.subset_option.grid(row=1,column=0,columnspan=2,sticky=tk.E+tk.W)
        self.filter_button.grid(row=1,column=2,columnspan=2,sticky=tk.E+tk.W)
        self.reset_button.grid(row=1,column=4,columnspan=2,sticky=tk.E+tk.W)
        
        self.save_subset_button.grid(row=2,column=0,columnspan=2,sticky=tk.E+tk.W)
        self.draw_subset_details_button.grid(row=2,column=2,columnspan=2,sticky=tk.E+tk.W)
        self.remove_nonconsecutive_button.grid(row=2,column=4,columnspan=2,sticky=tk.E+tk.W)

        

        
    def update_cluster(self):
        plotsum = 0
        indices = []
        index = 0
        for p in self.plot_options:
            plotsum += p.get()
            if p.get() == 1:
                indices.append(index)
            index += 1
        if plotsum != 2 and plotsum != 3:
            return
        subset = self.cluster_subset_option.cget('text')

        features = len(self.feature_options)
        
        logscale_x = self.feature_options_log[indices[0]].get()
        logscale_y = self.feature_options_log[indices[1]].get()
        x_label = self.feature_options[indices[0]].cget('text')
        y_label = self.feature_options[indices[1]].cget('text')
        x_col = np.squeeze(np.array(self.parse_db_col(self.unalias_dict.get(x_label,x_label),subset)))
        y_col = np.squeeze(np.array(self.parse_db_col(self.unalias_dict.get(y_label,y_label),subset)))
        xsign = np.sign(np.average(x_col))
        ysign = np.sign(np.average(y_col))
        x = np.log10(xsign*x_col) if bool(logscale_x) else x_col
        y = np.log10(ysign*y_col) if bool(logscale_y) else y_col
       
        if plotsum == 3:
            logscale_z = self.feature_options_log[indices[2]].get()
            z_label = self.feature_options[indices[2]].cget('text')
            z_col = np.squeeze(np.array(self.parse_db_col(self.unalias_dict.get(z_label,z_label),subset)))
            zsign = np.sign(np.average(z_col))
            z = np.log10(zsign*z_col) if bool(logscale_z) else z_col

        data = []
        for i in range(features):
            norm = self.norm_options[i].cget('text')
            logscale = self.feature_options_log[i].get()
            label = self.feature_options[i].cget('text')
            col = np.squeeze(np.array(self.parse_db_col(self.unalias_dict.get(label,label),subset)))
            col = col.astype(np.float64)
            sign = np.sign(np.average(col))
            col = np.log10(sign*col) if bool(logscale) else col
            if norm == 'Max':
                col -= np.average(col)
                col /= np.max(np.absolute(col))
            elif norm == 'Gauss':
                col -= np.average(col)
                col /= np.std(col)
            elif norm == 'MAD':
                col -= np.average(col)
                mad = np.median([np.absolute(x-np.average(col)) for x in col])
                col /= mad
            elif norm == 'None':
                pass
            data.append(col)
        data = np.vstack(data).T


        
        ##perform clustering
        clusterer = hdbscan.HDBSCAN(min_cluster_size=self.min_cluster_pts.get(), min_samples=self.min_pts.get(), gen_min_span_tree=True, cluster_selection_epsilon=self.eps.get())
        clusterer.fit(data)
        palette = sns.color_palette()
        cluster_colors = [sns.desaturate(palette[col], sat)
                  if col >= 0 else (0,0,0) for col, sat in
                  zip(clusterer.labels_, clusterer.probabilities_)]
        #clusterer._min_samples_label = 0

        
        self.cluster_f.clf()
        if plotsum == 3:
            ax = self.cluster_f.add_subplot(111, projection = '3d')
        else:
            ax = self.cluster_f.add_subplot(111)

        fontsize = 15
        labelpad = 10
        labelsize = 15
        ax.set_xlabel(x_label, labelpad=labelpad, fontsize=fontsize)
        ax.set_ylabel(y_label, labelpad=labelpad, fontsize=fontsize)
        if logscale_x:
            ax.set_xlabel('Log(' +str(x_label)+')', labelpad=labelpad, fontsize=fontsize)
        if logscale_y:
            ax.set_ylabel('Log(' +str(y_label)+')', labelpad=labelpad, fontsize=fontsize)
        if plotsum == 3:
            ax.set_zlabel(z_label, labelpad=labelpad, fontsize=fontsize)
            if logscale_z:
                ax.set_ylabel('Log(' +str(y_label)+')', labelpad=labelpad, fontsize=fontsize)
        if plotsum == 3:
            ax.scatter(x, y, z, c=cluster_colors, **plot_kwds)
            ax.tick_params(axis='x', labelsize=labelsize)
            ax.tick_params(axis='y', labelsize=labelsize)
            ax.tick_params(axis='z', labelsize=labelsize)
        else:
            ax.scatter(x, y, c=cluster_colors, **plot_kwds)
            ax.tick_params(axis='x', labelsize=labelsize)
            ax.tick_params(axis='y', labelsize=labelsize)
        self.cluster_canvas.draw()

        self.eventsdb_subset[subset]['cluster_id'] = clusterer.labels_
        


    
    def disable_plots(self):
        plotsum = 0
        for p in self.plot_options:
            plotsum += p.get()
        if plotsum == 3:
            for p,c in zip(self.plot_options, self.plot_options_check):
                if p.get() == 0:
                    c['state'] = 'disabled'
                else:
                    c['state'] = 'normal'
        else:
            for c in self.plot_options_check:
                c['state'] = 'normal'
    
    def add_feature(self):
        self.feature_options_log.append(tk.IntVar())
        self.feature_col_options.append(tk.StringVar())
        self.plot_options.append(tk.IntVar())
        self.feature_col_options[-1].set('Number of Levels')
        self.feature_norms.append(tk.StringVar())
        self.feature_norms[-1].set('Max')
        self.plot_options_check.append(tk.Checkbutton(self.cluster_controls_frame, text='', variable = self.plot_options[-1], command=self.disable_plots))
        self.feature_options_log_check.append(tk.Checkbutton(self.cluster_controls_frame, text='', variable = self.feature_options_log[-1]))
        self.feature_options.append(tk.OptionMenu(self.cluster_controls_frame, self.feature_col_options[-1], *[self.alias_dict.get(option,option) for option in self.column_list]))
        self.norm_options.append(tk.OptionMenu(self.cluster_controls_frame, self.feature_norms[-1], *self.normalization_options))
        self.delete_feature_button.append(tk.Button(self.cluster_controls_frame, text='X'))
        button = self.delete_feature_button[-1]
        self.delete_feature_button[-1].bind('<Button-1>', func=lambda x: self.delete_feature(button))
        self.feature_options[-1].grid(row=self.gridcounter,column=0,sticky=tk.E+tk.W)
        self.feature_options_log_check[-1].grid(row=self.gridcounter, column=1, sticky=tk.E+tk.W)
        self.plot_options_check[-1].grid(row=self.gridcounter, column=2, sticky=tk.E+tk.W)
        self.norm_options[-1].grid(row=self.gridcounter, column=3, sticky=tk.E+tk.W)
        self.delete_feature_button[-1].grid(row=self.gridcounter, column=4,sticky=tk.E+tk.W)
        self.gridcounter += 1
        self.add_feature_button.grid(row=self.gridcounter,column=0, columnspan=5, sticky=tk.E+tk.W)
        self.disable_plots()

    def delete_feature(self, widget):
        index = self.delete_feature_button.index(widget) + 2 #+2 because there will always be a minimum of two features
        temp = self.delete_feature_button.pop(index-2)
        temp.destroy()
        temp = self.norm_options.pop(index)
        temp.destroy()
        temp = self.feature_options_log_check.pop(index)
        temp.destroy()
        temp = self.feature_options.pop(index)
        temp.destroy()
        temp = self.plot_options_check.pop(index)
        temp.destroy()
        temp = self.plot_options.pop(index)
        temp = self.feature_col_options.pop(index)
        temp = self.feature_options_log.pop(index)
        temp = self.feature_norms.pop(index)
        
        reset = self.feature_options[index:]
        for r in reset:
            r.grid(row = r.grid_info()['row']-1, column=0, stick=tk.E+tk.W)
        reset = self.feature_options_log_check[index:]
        for r in reset:
            r.grid(row = r.grid_info()['row']-1, column=1, stick=tk.E+tk.W)
        reset = self.plot_options_check[index:]
        for r in reset:
            r.grid(row = r.grid_info()['row']-1, column=2, stick=tk.E+tk.W)
        reset = self.norm_options[index:]
        for r in reset:
            r.grid(row = r.grid_info()['row']-1, column=3, stick=tk.E+tk.W)
        reset = self.delete_feature_button[index-2:]
        for r in reset:
            r.grid(row = r.grid_info()['row']-1, column=4, stick=tk.E+tk.W)
        self.gridcounter -= 1
        self.disable_plots()
        
                
        
            
    def plot_subset_select(self):
        self.window = tk.Toplevel()
        self.window.title("Subsets to plot")
        self.plot_subsets_btn = tk.Button(self.window, text='Selection Done',command=self.plot_subset_list_btn)
        self.plot_subsets_btn.grid(row=1,column=0,columnspan=3,sticky=tk.E+tk.W)
        self.plot_subset_select = tk.StringVar()
        b = len(self.plot_list)
        self.plot_subset_select.set(str(np.arange(0,b))[1:-1])
        self.lstbox = tk.Listbox(self.window,listvariable=self.plot_subset_select, selectmode = "multiple", width=20, height=11)
        self.lstbox.grid(column=0, row=0)

    def plot_subset_list_btn(self):
        plot_list_int = list()
        for i in self.lstbox.curselection():
            plot_list_int.append(self.lstbox.get(i))
        for key, val in self.plot_list.items():
            self.plot_list[key]=0     
        for val in plot_list_int:
            self.plot_list['Subset '+str(val)]=1
        self.window.destroy()


    def declare_good_events(self):
        subset = self.subset_option.cget('text')
        [a,b] = self.eventsdb_subset[subset].shape
        if 'Nonconsecutive Events Removed' not in self.filter_list[subset]:
            self.eventsdb_subset[subset]['index_ref'] = np.arange(0,a)
            if subset in self.good_event_subset:
                self.good_event_subset.remove(subset)
            self.good_event_subset.insert(0,subset)
            self.status_string.set(', '.join(self.good_event_subset)+' events are all considered successful')

        else:
            self.status_string.set('Cannot run operation after removing non-consecutive events. To operate, reset the subset and start over')

    def get_active_subsets(self,active):
        subset_list = []
        if self.plot_list == self.init_plot_list or active == 1:
            for key, val in self.filter_list.items():
                if key == 'Subset 0' or len(val) > 0:
                    subset_list.append(key)
        else:
            for key, val in self.plot_list.items():
                if val == 1:
                    subset_list.append(key)
        subset_list = sorted(subset_list)
        return subset_list

#######################################

        
    def remove_nonconsecutive_events(self):
        subset = self.subset_option.cget('text')
        if 'Nonconsecutive Events Removed' in self.filter_list[subset]:
            self.status_string.set('Cannot remove non-consecutive events twice. To apply further filters, reset the subset and start over')
            self.status_display.flash(6)
        else:
            self.capture_rate_subset[subset] = self.eventsdb_subset[subset]
            indices = self.eventsdb_subset[subset]['id'].values
            index_diff = np.diff(indices)
            index_diff = np.insert(index_diff,0,0)
            self.eventsdb_subset[subset]['index_diff'] = index_diff
            db = self.eventsdb_subset[subset]
            self.eventsdb_subset[subset] = sqldf('SELECT * from db where  index_diff = 1',locals())
            self.status_string.set('{0}: {1} events'.format(subset, len(self.eventsdb_subset[subset])))
            self.filter_list[subset].append('Nonconsecutive Events Removed')
        
    def update_count(self, *args):
        subset = self.subset_option.cget('text')
        try:
            self.status_string.set('{0}: {1} events'.format(subset,len(self.eventsdb_subset[subset])))
        except TypeError:
            self.status_string.set('Empty subset, try resetting')

    def ln_exponential(self, t, rate, amplitude): #define a fitting function form
        return np.log(amplitude)-rate*t

    def log_exp_pdf(self, logt, rate, amplitude):
        return amplitude * np.exp(-rate*10.0**logt) * 10.0**logt * np.log(10)

    def capture_rate(self):
        subset_list = self.get_active_subsets(0)
        self.rate_f.clf()
        self.a = self.rate_f.add_subplot(111)
        
        self.xdata = []
        self.ydata = []
        fit_string = ''
        self.export_type = 'capture_rate'
        for subset in subset_list:
            if 'Nonconsecutive Events Removed' not in self.filter_list[subset]:
                db = self.eventsdb_subset[subset]
            else:
                db = self.capture_rate_subset[subset]

            start_times = db['start_time_s'].values
            delays = np.diff(start_times)                        
            indices = db['id'].values
            index_diff = np.diff(indices)
            if 'index_ref' in db:
                ref_indices = db['index_ref']
                ref_indices_diff = np.diff(ref_indices)
                valid_delays = np.sort(delays[np.where((index_diff - ref_indices_diff) == 0)])
            else:
                valid_delays = np.sort(delays[np.where(index_diff == 1)])

            if not self.use_histogram.get():
                probability = np.squeeze(np.array([1.0-float(i)/float(len(valid_delays)) for i in range(len(valid_delays))]))
                lnprob = np.log(probability)
                popt, pcov = curve_fit(self.ln_exponential, valid_delays, lnprob)
                fit = np.exp(self.ln_exponential(valid_delays, popt[0], popt[1]))

                residuals = lnprob - np.log(fit)

                ss_res = np.sum(residuals**2)
                ss_tot = np.sum((lnprob-np.mean(lnprob))**2)
                rsquared = 1.0 - ss_res/ss_tot

                self.a.set_xlabel('Interevent Delay (s)')
                self.a.set_ylabel('Probability')
                self.a.plot(valid_delays,probability,'.',label='{0}'.format(subset))
                self.a.plot(valid_delays,fit,label='{0} Fit'.format(subset))
                self.a.set_yscale('log')
                fit_string = fit_string + '{0}: {1}/{2} events used. Capture Rate is {3:.3g} \u00B1 {4:.1g} Hz (R\u00B2 = {5:.2g})\n'.format(subset,len(valid_delays),len(indices), popt[0], -t.isf(0.975,len(valid_delays))*np.sqrt(np.diag(pcov))[0], rsquared)
                self.xdata.append(valid_delays)
                self.ydata.append(probability)
                self.a.legend(loc='best',prop={'size': 10})
                self.rate_canvas.draw()
                self.status_string.set(fit_string)
            else:
                log_delays = np.log10(valid_delays)
                numbins = int(self.xbin_entry.get())
                counts, edges  = np.histogram(log_delays, bins=numbins)
                bincenters = edges[:-1] + np.diff(edges)/2.0
                self.xdata.append(bincenters)
                self.ydata.append(counts)

                popt, pcov = curve_fit(self.log_exp_pdf, bincenters, counts)
                fit = self.log_exp_pdf(bincenters, popt[0], popt[1])

                residuals = fit - counts
                ss_res = np.sum(residuals**2)
                ss_tot = np.sum((counts - np.mean(counts))**2)
                rsquared = 1.0 - ss_res/ss_tot

                
                self.a.set_xlabel('Log(Interevent Delay (s))')
                self.a.set_ylabel('Count')
                self.a.plot(bincenters,counts,drawstyle='steps-mid',label='{0}'.format(subset))
                self.a.plot(bincenters,fit,label='{0} Fit'.format(subset))
                fit_string = fit_string + '{0}: {1}/{2} events used. Capture Rate is {3:.3g} \u00B1 {4:.1g} Hz (R\u00B2 = {5:.2g})\n'.format(subset,len(valid_delays),len(indices), popt[0], -t.isf(0.975,len(counts))*np.sqrt(np.diag(pcov))[0], rsquared)
                self.a.legend(loc='best',prop={'size': 10})
                self.rate_canvas.draw()
                self.status_string.set(fit_string)
        
    def not_implemented(self):
        top = tk.Toplevel()
        top.title('Not Implemented Warning')
        warning = tk.Label(top, text='This functionality is not yet implemented')
        warning.pack()

    def filter_db(self):
        filterstring = self.filter_entry.get()
        subset = self.subset_option.cget('text')
        self.eventsdb_prev = self.eventsdb_subset[subset]
        eventsdb_subset = self.eventsdb_subset[subset]
        if 'Nonconsecutive Events Removed' in self.filter_list[subset]:
            self.status_string.set('Cannot apply filters after removing non-consecutive events. To apply further filters, reset the subset and start over')
        else:
            self.eventsdb_subset[subset] = eventsdb_subset.query(filterstring)
            self.eventsdb_subset[subset]['adj_id'] = np.arange(0,len(self.eventsdb_subset[subset]))
            try:
                self.status_string.set('{0}: {1} events'.format(subset,len(self.eventsdb_subset[subset])))
                if filterstring not in self.filter_list[subset]:
                    self.filter_list[subset].append(filterstring)
                else:
                    self.status_string.set('Redundant Filter Ignored')
            except TypeError:
                self.status_string.set('Invalid Entry')
                self.status_display.flash(6)
                self.eventsdb_subset[subset] = self.eventsdb_prev
        
    def replicate_manual_deletions(self):
        subset_list = self.get_active_subsets(1)

        for subset in subset_list:
            self.eventsdb_prev = self.eventsdb_subset[subset]
            eventsdb_subset = self.eventsdb_subset[subset]
            self.eventsdb_subset[subset]
            manual_delete = self.manual_delete
            tempdict = dict()
            tempdict['deleted_id'] = manual_delete
            temptable = pd.DataFrame(tempdict)
            tempdb = sqldf('''SELECT * FROM eventsdb_subset t1 LEFT JOIN temptable t2 ON t1.id = t2.deleted_id''', locals())
            tempdb['deleted_id'].fillna(-1,inplace=True)
            self.eventsdb_subset[subset] = sqldf('''SELECT * FROM tempdb where deleted_id = -1''',locals())
            self.eventsdb_subset[subset].drop('deleted_id',1,inplace=True)
            try:
                self.status_string.set('{0}: {1} events'.format(subset,len(self.eventsdb_subset[subset])))
                for event in manual_delete:
                    filterstring = 'id != {0}'.format(event)
                    if filterstring not in self.filter_list[subset]:
                        self.filter_list[subset].append(filterstring)
                
            except TypeError:
                self.status_string.set('Unable to replicate deletions')
                self.eventsdb_subset[subset] = self.eventsdb_prev
    
    def display_filters(self):
        top = tk.Toplevel()
        top.title('Filters Used')


        subset_frame = dict((key, tk.LabelFrame(top, text=key)) for key, val in self.eventsdb_subset.items())
        subset_frame = OrderedDict(sorted(subset_frame.items()))
            
        filters = dict((key, tk.StringVar()) for key, val in subset_frame.items())
        msg = dict((key, tk.Entry(val, textvariable=filters[key], bg=subset_frame[key].cget('bg'), relief='flat')) for key, val in subset_frame.items())
        
        i = 0
        for key, val in subset_frame.items():
            top.columnconfigure(i,weight=1)
            val.grid(row=0, column=i, sticky=tk.E+tk.W)
            if (len(self.filter_list[key]) > 0):
                filters[key].set('%s' % '\n'.join(self.filter_list[key]))
            else:
                if key == 'Subset 0':
                    filters[key].set('None')
                else:
                    filters[key].set('Inactive')
            msg[key].grid(row=0,column=0,stick=tk.E+tk.W)
            i += 1


    def first_level_fraction(self):
        durations = [np.array(a,dtype=float)[1:-1] for a in self.eventsdb['level_duration_us'].str.split(';')]
        fraction = [duration[0]/(np.sum(duration)+duration[0]) for duration in durations]
        self.eventsdb['first_level_fraction'] = fraction
        for key, val in self.eventsdb_subset.items():
            val = self.eventsdb
        
    def folding_distribution(self):
        x = self.eventsdb['max_blockage_duration_us']/(self.eventsdb['duration_us']+self.eventsdb['max_blockage_duration_us'])
        self.eventsdb['folding'] = x
        for key, val in self.eventsdb_subset.items():
            val = self.eventsdb


    def count(self):
        eventsdb = self.eventsdb
        eventsdb_sorted = sqldf('SELECT * from eventsdb ORDER BY id',locals())
        numevents = len(eventsdb)
        count = [i for i in range(0,numevents)]
        eventsdb_sorted['count'] = count
        self.eventsdb = sqldf('SELECT * from eventsdb_sorted ORDER BY id',locals())
        for key, val in self.eventsdb_subset.items():
            val = self.eventsdb
        
                
    

    def reset_db(self):
        subset = self.subset_option.cget('text')
        self.eventsdb_subset[subset] = self.eventsdb
        self.capture_rate_subset[subset] = None
        self.filter_list[subset] = []
        self.status_string.set('{0}: {1} events'.format(subset,len(self.eventsdb_subset[subset])))
        if subset in self.good_event_subset:
            self.good_event_subset.remove(subset)


    def export_plot_data(self):
        data_path = tkinter.filedialog.asksaveasfilename(defaultextension='.csv')
        subset_list = self.get_active_subsets(0)
        if self.export_type == 'hist1d':
            data = OrderedDict()
            if len(subset_list) > 1:
                for i in range(len(subset_list)):
                    x_label = self.x_option.cget('text')
                    logscale_x = self.x_log_var.get()
                    if (logscale_x):
                        x_label = 'Log({0})'.format(x_label)
                    data['{0} {1}'.format(subset_list[i],x_label)] = self.xdata[i]
                    data['{0} Count'.format(subset_list[i])] = self.ydata[i]
            else:
                x_label = self.x_option.cget('text')
                logscale_x = self.x_log_var.get()
                if (logscale_x):
                    x_label = 'Log({0})'.format(x_label)
                data[x_label] = self.xdata
                data['{0} Count'.format(subset_list[0])] = self.ydata
            data_frame = pd.DataFrame(data)
            data_frame.to_csv(data_path, index=False)
        elif self.export_type == 'scatter':
            x_label = self.x_option.cget('text')
            y_label = self.y_option.cget('text')
            data = OrderedDict()
            data_frame = pd.DataFrame()
            column_names = []
            for i in range(len(subset_list)):
                x_string = '{0}_{1}'.format(subset_list[i],x_label)
                y_string = '{0}_{1}'.format(subset_list[i],y_label)
                column_names.append(x_string)
                column_names.append(y_string)
                if len(subset_list) > 1:
                    data[x_string] = self.xdata[i]
                    data[y_string] = self.ydata[i]
                else:
                    data[x_string] = self.xdata
                    data[y_string] = self.ydata
                data_frame = pd.concat([data_frame, pd.DataFrame(data[x_string]), pd.DataFrame(data[y_string])],axis=1)
            data_frame.columns = column_names
            data_frame.to_csv(data_path, index=False)
        elif self.export_type == 'hist2d':
            data = OrderedDict()
            logscale_x = self.x_log_var.get()
            logscale_y = self.y_log_var.get()
            x_label = self.x_option.cget('text')
            y_label = self.y_option.cget('text')
            data[x_label] = self.xdata
            data[y_label] = self.ydata
            data['Count'] = self.zdata
            data_frame = pd.DataFrame(data)
            data_frame.to_csv(data_path, index=False)
        elif self.export_type == 'capture_rate':
            data = OrderedDict()
            column_names = []
            for i in range(len(subset_list)):
                x_string = '{0} Event Delay (s)'.format(subset_list[i])
                y_string = '{0} Probability'.format(subset_list[i])
                    
                data[x_string] = self.xdata[i]
                data[y_string] = self.ydata[i]
            data_frame = pd.DataFrame({k : pd.Series(v) for k,v in data.items()})
            data_frame.to_csv(data_path, index=False)
        else:
            self.status_string.set("Unable to export plot")

    


    def on_click(self, event):
        if self.clicks_remaining > 0:
            if event.inaxes is not None:
                self.state_array[self.num_states*2 - self.clicks_remaining] = event.xdata
                self.clicks_remaining -= 1
                if self.clicks_remaining == 0:
                    self.define_state_array_flag = 0
                self.status_string.set('State Boundaries Defined: {0}'.format(self.state_array))
            else:
                self.status_string.set('Clicked ouside axes bounds but inside plot window')



    def define_states(self):
        setup = self.n_states_entry.get().split(';')
        self.ignore_list = []
        self.tolerance = 4

        
        self.num_states = int(setup[0])
        self.clicks_remaining = self.num_states*2
        self.status_string.set('Click on the 1D blockage level histogram {0} times'.format(self.clicks_remaining))
        self.state_array = np.zeros(self.num_states*2)

        if len(setup) > 1:
            self.ignore_list = np.array([int(i) if i.isdigit() else i for i in setup[1].split(',')])
        if len(setup) > 2:
            self.tolerance = float(setup[2])

    def multi_gauss(self, x, N, *args):
        f = np.zeros(len(x))
        args = args[0]
        for i in range(N):
            amp = args[3*i]
            mu = args[3*i+1]
            sig = args[3*i+2]
            f += amp * np.exp(-(x-mu)**2/(2.0*sig**2))
        return f

    def define_shapes(self):
        subset = self.subset_option.cget('text')
        if self.clicks_remaining > 0:
            self.status_string.set('Complete State Array First: {0} clicks remaining'.format(self.clicks_remaining))
        else:
            type_array = []
            trimmed_type = []
            trimmed_Nlev = []
            first_level=[]
            last_level=[]
            state_means = np.zeros(self.num_states)
            i = 0
            while i < self.num_states*2:
                state_means[int(i/2)] = 0.5*(self.state_array[i]+self.state_array[i+1])
                i += 2



            x = self.xdata
            y = self.ydata

            p0 = []
            for i in range(self.num_states):
                p0.append(y[np.abs(x-state_means[i]).argmin()])
                p0.append(state_means[i])
                p0.append(1.0/6.0 * (self.state_array[2*i+1]-self.state_array[2*i]))
            
            popt, pcov = curve_fit(lambda x, *p0: self.multi_gauss(x, self.num_states, p0), x, y, p0=p0)

            self.plot_1d_histogram()
            self.a.plot(x, self.multi_gauss(x, self.num_states,popt))
            self.stats_canvas.draw()
            
            blockage_levels = [np.array(a,dtype=float)[1:-1] for a in self.eventsdb_subset[subset]['blockages_pA'].str.split(';')]
            for b in blockage_levels:
                event_type = []
                indices = [(np.abs(state_means - blevel)).argmin() for blevel in b]
                for level,index in zip(b,indices):
                    if level > self.state_array[2*index] and level < self.state_array[2*index+1]:
                        event_type.append(index+1)
                    else:
                        event_type = [-1]
                        break
                typenum = int(''.join(map(str, event_type)))
                trim_type = []
                if typenum == -1:
                    trim_type.append('-1')
                    trim_type = int(''.join(map(str, trim_type)))
                    trimmed_Nlev.append(0)
                else:
                    str_typenum = str(typenum)
                    for i in range(len(str_typenum)-1):
                        if int(str_typenum[i]) != int(str_typenum[i+1]):
                            trim_type.append(str_typenum[i])
                    trim_type.append(str_typenum[-1])
                    trimmed_Nlev.append(len(trim_type))
                    trim_type = int(''.join(map(str, trim_type)))
                trimmed_type.append(trim_type)
                if typenum > 999999999:
                    typenum = -1
                type_array.append(typenum)
                if typenum != -1:
                    first_level.append(int(str(trim_type)[0]))
                    last_level.append(int(str(trim_type)[-1]))
                else:
                    first_level.append(-1)
                    last_level.append(-1)
            self.eventsdb_subset[subset]['event_shape'] = type_array
            self.eventsdb_subset[subset]['trimmed_shape'] = trimmed_type
            self.eventsdb_subset[subset]['trimmed_n_levels'] = trimmed_Nlev
            self.eventsdb_subset[subset]['first_level'] = first_level
            self.eventsdb_subset[subset]['last_level'] = last_level
            self.status_string.set('Event shapes recalculated. \nThis applies only to the current subset')
            self.eventsdb_subset[subset].loc[self.eventsdb_subset[subset]['event_shape'] == 1, 'folding'] = 0
            self.eventsdb_subset[subset].loc[self.eventsdb_subset[subset]['event_shape'] == 2, 'folding'] = 0.5

    def apply_limits(self):
        x_min = float(self.x_min.get())
        x_max = float(self.x_max.get())
        y_min = float(self.y_min.get())
        y_max = float(self.y_max.get())

        self.a.set_xlim([x_min, x_max])
        self.a.set_ylim([y_min, y_max])
        self.stats_canvas.draw()

        

    def set_axis_limits(self):
        try:
            limits = tk.Toplevel()
            limits.title('Axis Limits')

            x_min, x_max = self.a.get_xlim()
            y_min, y_max = self.a.get_ylim()

            lim_frame = tk.LabelFrame(limits, text='Axis Limits')
            x_label = tk.Label(limits, text='X')
            y_label = tk.Label(limits, text='Y')
            min_label = tk.Label(limits, text='Min')
            max_label = tk.Label(limits, text='Max')
            x_min_default = tk.StringVar()
            x_min_default.set(x_min)
            x_max_default = tk.StringVar()
            x_max_default.set(x_max)
            y_min_default = tk.StringVar()
            y_min_default.set(y_min)
            y_max_default = tk.StringVar()
            y_max_default.set(y_max)
            self.x_min = tk.Entry(limits,textvariable=x_min_default)
            self.x_max = tk.Entry(limits,textvariable=x_max_default)
            self.y_min = tk.Entry(limits,textvariable=y_min_default)
            self.y_max = tk.Entry(limits,textvariable=y_max_default)

            apply_button = tk.Button(limits,text='Apply',command=self.apply_limits)

            x_label.grid(row=1,column=0,sticky=tk.E+tk.W)
            y_label.grid(row=2,column=0,sticky=tk.E+tk.W)
            min_label.grid(row=0,column=1,sticky=tk.E+tk.W)
            max_label.grid(row=0,column=2,sticky=tk.E+tk.W)

            self.x_min.grid(row=1,column=1,sticky=tk.E+tk.W)
            self.x_max.grid(row=1,column=2,sticky=tk.E+tk.W)
            self.y_min.grid(row=2,column=1,sticky=tk.E+tk.W)
            self.y_max.grid(row=2,column=2,sticky=tk.E+tk.W)

            apply_button.grid(row=3,column=0,columnspan=3,sticky=tk.E+tk.W)
        except AttributeError:
            self.status_string.set('Plot something first')
            limits.destroy()


    #def on_click(self, event):
    #    pass#print event.xdata, event.ydata

    def key_press(self, event):
        if event.keysym == 'a':
            self.set_axis_limits()

    def plot_xy(self):
        subset_list = self.get_active_subsets(0)
        self.export_type = 'scatter'
        logscale_x = self.x_log_var.get()
        logscale_y = self.y_log_var.get()
        x_label = self.x_option.cget('text')
        y_label = self.y_option.cget('text')
        x_col = np.squeeze(np.array([self.parse_db_col(self.unalias_dict.get(x_label,x_label),key) for key in subset_list]))
        y_col = np.squeeze(np.array([self.parse_db_col(self.unalias_dict.get(y_label,y_label),key) for key in subset_list]))


        xsign = np.sign(np.average(x_col[0])) if len(subset_list) > 1 else np.sign(np.average(x_col))
        ysign = np.sign(np.average(y_col[0])) if len(subset_list) > 1 else np.sign(np.average(y_col))

        self.stats_f.clf()
        self.a = self.stats_f.add_subplot(111)
        labelsize=15
        self.a.tick_params(axis='x', labelsize=labelsize)
        self.a.tick_params(axis='y', labelsize=labelsize)
        self.a.figure.canvas.mpl_connect('button_press_event', self.on_click)
        self.a.set_xlabel(x_label, fontsize=labelsize)
        self.a.set_ylabel(y_label, fontsize=labelsize)
        
        self.xdata = np.array(x_col*xsign)
        self.ydata = np.array(y_col*ysign)


        if len(subset_list) > 1:
            for i in range(len(subset_list)):
                self.a.plot(self.xdata[i],self.ydata[i],marker='.',linestyle='None',label=subset_list[i],alpha=0.2)
            self.a.legend(loc='best',prop={'size': 10})
        else:
            self.a.plot(self.xdata,self.ydata,marker='.',linestyle='None')
        if logscale_x:
            self.a.set_xscale('log')
        if logscale_y:
            self.a.set_yscale('log')
        self.stats_canvas.draw()

    def plot_1d_histogram(self):
        subset_list = self.get_active_subsets(0)
        self.export_type = 'hist1d'
        logscale_x = self.x_log_var.get()
        logscale_y = self.y_log_var.get()
        x_label = self.x_option.cget('text')
        col = np.squeeze(np.array([self.parse_db_col(self.unalias_dict.get(x_label,x_label),key) for key in subset_list]))
        numbins = self.xbin_entry.get()
        self.stats_f.clf()
        self.a = self.stats_f.add_subplot(111)
        self.xdata = []
        self.ydata = []
        labelsize=15
        self.a.tick_params(axis='x', labelsize=labelsize)
        self.a.tick_params(axis='y', labelsize=labelsize)
        if logscale_x:
            self.a.set_xlabel('Log(' +str(x_label)+')', fontsize=labelsize)
            self.a.set_ylabel('Count', fontsize=labelsize)
            if len(subset_list) > 1:
                for i in range(len(subset_list)):
                    col[i] *= np.sign(np.average(col[i]))
                    col[i] = np.log10(col[i])
                    y, x, patches = self.a.hist(col[i],bins=int(numbins),log=bool(logscale_y),histtype='step',stacked=False,fill=False,label=subset_list[i])
                    self.xdata.append(x)
                    self.ydata.append(y)
            else:
                col *= np.sign(np.average(col))
                col = np.log10(col)
                self.ydata, self.xdata, patches = self.a.hist(col,bins=int(numbins),log=bool(logscale_y),histtype='step',stacked=False,fill=False,label=subset_list)
        else:
            self.a.set_xlabel(x_label, fontsize=labelsize)
            self.a.set_ylabel('Count', fontsize=labelsize)
            if len(subset_list) > 1:
                for i in range(len(subset_list)):
                    if x_label == 'Fold Fraction':
                        y, self.xdata, patches = self.a.hist(col[i],range=(0,0.5),bins=(0,0.1,0.2,0.3,0.4,0.5),log=bool(logscale_y),histtype='step',stacked=False,fill=False,label=subset_list[i])
                        self.ydata.append(y)
                    else:
                        y, x, patches = self.a.hist(col[i],bins=int(numbins),log=bool(logscale_y),histtype='step',stacked=False,fill=False,label=subset_list[i])
                        self.xdata.append(x)
                        self.ydata.append(y)
            else:
                if x_label == 'Fold Fraction':
                    self.ydata, self.xdata, patches = self.a.hist(col,range=(0,0.5),bins=(0,0.1,0.2,0.3,0.4,0.5),log=bool(logscale_y),histtype='step',stacked=False,fill=False,label=subset_list)
                else:
                    self.ydata, self.xdata, patches = self.a.hist(col,bins=int(numbins),log=bool(logscale_y),histtype='step',stacked=False,fill=False,label=subset_list)
        self.a.legend(loc='best',prop={'size': 10})
        
        
        for i in range(len(subset_list)):
            try:
                self.xdata[i] = self.xdata[i][:-1] + np.diff(self.xdata[i])/2.0
            except IndexError:
                self.xdata = self.xdata[:-1] + np.diff(self.xdata)/2.0
        self.stats_canvas.draw()
        self.stats_canvas.callbacks.connect('button_press_event', self.on_click)

        
    def plot_2d_histogram(self):
        subset = self.subset_option.cget('text')
        self.export_type = 'hist2d'
        logscale_x = self.x_log_var.get()
        logscale_y = self.y_log_var.get()
        x_label = self.x_option.cget('text')
        y_label = self.y_option.cget('text')
        x_col = np.squeeze(np.array(self.parse_db_col(self.unalias_dict.get(x_label,x_label),subset)))
        y_col = np.squeeze(np.array(self.parse_db_col(self.unalias_dict.get(y_label,y_label),subset)))
        xbins = self.xbin_entry.get()
        ybins = self.ybin_entry.get()
        self.stats_f.clf()
        self.a = self.stats_f.add_subplot(111)
        labelsize=15
        self.a.set_xlabel(x_label, fontsize=labelsize)
        self.a.set_ylabel(y_label, fontsize=labelsize)
        if logscale_x:
            self.a.set_xlabel('Log(' +str(x_label)+')', fontsize=labelsize)
        if logscale_y:
            self.a.set_ylabel('Log(' +str(y_label)+')', fontsize=labelsize)
        self.a.tick_params(axis='x', labelsize=labelsize)
        self.a.tick_params(axis='y', labelsize=labelsize)
        xsign = np.sign(np.average(x_col))
        ysign = np.sign(np.average(y_col))
        x = np.log10(xsign*x_col) if bool(logscale_x) else x_col
        y = np.log10(ysign*y_col) if bool(logscale_y) else y_col

        z, x, y, image = self.a.hist2d(x,y,bins=[int(xbins),int(ybins)],norm=matplotlib.colors.LogNorm())
        x = x[:-1] + np.diff(x)/2.0
        y = y[:-1] + np.diff(y)/2.0
        xy = [list(zip([a]*len(y),y)) for a in x]
        z = np.ravel(z)
        xy = np.reshape(xy,(len(z),2))
        self.xdata = xy[:,0]
        self.ydata = xy[:,1]
        self.zdata = z
        self.stats_canvas.draw()
        

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
            try:
                self.plot_xy()
            except AttributeError:
                self.status_string.set("X and Y must have the same length")
        elif option == '1D Histogram':
            self.plot_1d_histogram()
        elif option == '2D Histogram':
            try:
                self.plot_2d_histogram()
            except AttributeError:
                self.status_string.set("X and Y must have the same length")
                raise
        else:
            pass

    def parse_db_col(self, col, subset):
        if col in ['blockages_pA','level_current_pA','level_duration_us','stdev_pA']:
            if self.include_baseline.get():
                return_col = np.hstack([np.array(a,dtype=float) for a in self.eventsdb_subset[subset][col].str.split(';')])
            else:
                return_col = np.hstack([np.array(a,dtype=float)[1:-1] for a in self.eventsdb_subset[subset][col].str.split(';')])
        else:
            return_col = self.eventsdb_subset[subset][col]
        
        return return_col.astype(np.float64)

    def parse_list(self, semilist):
        semilist = np.squeeze(semilist)
        return np.hstack([np.array(a,dtype=float) for a in str(semilist).split(';')]).astype(np.float64)

    def plot_event(self):
        subset = self.subset_option.cget('text')
        ratedb = self.ratedb
        index = self.event_index.get()
        if any(self.eventsdb_subset[subset]['id']==index) or self.plot_bad_events.get():
            try:
                event_file_path = self.events_folder+'/event_%05d.csv' % index
                event_file = pd.read_csv(event_file_path,encoding='utf-8')
            except IOError:
                try:
                    event_file_path = self.events_folder+'/event_%08d.csv' % index
                    event_file = pd.read_csv(event_file_path,encoding='utf-8')
                except IOError:
                    self.event_info_string.set(event_file_path+' not found')
                    return
            eventsdb_subset = self.eventsdb_subset[subset]
            self.event_export_file = event_file
            try:
                event_type = sqldf('SELECT type from eventsdb_subset WHERE id=%d' % index,locals())['type'][0]
            except IndexError:
                event_type = 0
            self.event_export_type = event_type
            if event_type == 0:
                event_file.columns = ['time','current','cusum']
            elif event_type == 1:
                event_file.columns = ['time','current','cusum','stepfit']
            if ratedb is not None:
                try:
                    crossings = self.parse_list(sqldf('SELECT intra_crossing_times_us from ratedb WHERE id=%d' % index,locals()).values)
                    local_stdev = np.squeeze(sqldf('SELECT local_stdev from ratedb WHERE id=%d' % index,locals()).values)
                    local_baseline = np.squeeze(sqldf('SELECT local_baseline from ratedb WHERE id=%d' % index,locals()).values)
                    crossings = zip(crossings[::2], crossings[1::2])
                except:
                    ratedb = None
                    self.ratedb = None

                
            self.event_f.clf()
            a = self.event_f.add_subplot(111)

            labelsize=15
            a.tick_params(axis='x', labelsize=labelsize)
            a.tick_params(axis='y', labelsize=labelsize)

        
            a.set_xlabel('Time (us)', fontsize=labelsize)
            a.set_ylabel('Current (pA)', fontsize=labelsize)
            if event_type == 0:
                a.plot(event_file['time'],event_file['current'],event_file['time'],event_file['cusum'])
            elif event_type == 1:
                a.plot(event_file['time'],event_file['current'],event_file['time'],event_file['cusum'],event_file['time'],event_file['stepfit'])
            if self.intra_threshold > 0 and ratedb is not None:
                a.plot(event_file['time'], np.sign(event_file['current'][0])*np.ones(len(event_file['time']))*(local_baseline - self.intra_threshold * local_stdev), '--', color='y')
                a.plot(event_file['time'], np.sign(event_file['current'][0])*np.ones(len(event_file['time']))*(local_baseline - (self.intra_threshold - self.intra_hysteresis) * local_stdev), '--', color='g')
                for start, end in crossings:
                    a.axvspan(start,end,color='g',alpha=0.3)
            self.event_canvas.draw()
            self.event_info_string.set('Successfully plotted event {0}'.format(index))
        else:
            self.event_info_string.set('Event {0} is missing or deleted'.format(index))

    def export_event_data(self):
        data_path = tkinter.filedialog.asksaveasfilename(defaultextension='.csv')
        if self.event_export_type == 0:
            np.savetxt(data_path,np.c_[self.event_export_file['time'],self.event_export_file['current'],self.event_export_file['cusum']],delimiter=',')
        elif self.event_export_type == 1:
            np.savetxt(data_path,np.c_[self.event_export_file['time'],self.event_export_file['current'],self.event_export_file['cusum'], self.event_export_file['stepfit']],delimiter=',')

    def next_event(self):
        if not self.plot_bad_events.get():
            subset = self.subset_option.cget('text')
            try:
                current_index = self.eventsdb_subset[subset][self.eventsdb_subset[subset]['id'] == self.event_index.get()].index.tolist()[0]
            except IndexError:
                self.event_info_string.set('Event not found, resetting')
                current_index = -1
            if current_index < max(self.eventsdb['id']):
                next_index = self.eventsdb_subset[subset][self.eventsdb_subset[subset]['id'] > self.event_index.get()].index.tolist()[0]
                self.event_index.set(int(self.eventsdb_subset[subset]['id'][next_index]))
                self.plot_event()
            else:
                pass
        else:
            current_index = self.event_index.get()
            if current_index < max(self.eventsdb['id']):
                next_index = current_index + 1
                self.event_index.set(next_index)
                self.plot_event()
            else:
                pass
            

    def prev_event(self):
        if not self.plot_bad_events.get():
            subset = self.subset_option.cget('text')
            try:
                current_index = self.eventsdb_subset[subset][self.eventsdb_subset[subset]['id'] == self.event_index.get()].index.tolist()[0]
            except IndexError:
                self.event_info_string.set('Event not found, resetting')
                current_index = 1
            if current_index > 0:
                try:
                    prev_index = self.eventsdb_subset[subset][self.eventsdb_subset[subset]['id'] < self.event_index.get()].index.tolist()[-1]
                    self.event_index.set(int(self.eventsdb_subset[subset]['id'][prev_index]))
                    self.plot_event()
                except IndexError:
                    pass
            else:
                pass
        else:
            current_index = self.event_index.get()
            if current_index > 0:
                next_index = current_index - 1
                self.event_index.set(next_index)
                self.plot_event()
            else:
                pass

    def delete_event(self):
        subset = self.subset_option.cget('text')
        event_index = self.event_index.get()
        try:
            current_index = self.eventsdb_subset[subset][self.eventsdb_subset[subset]['id'] == self.event_index.get()].index.tolist()[0]
        except IndexError:
            self.event_info_string.set('Event not found, resetting')
            current_index = -1
        if current_index < len(self.eventsdb_subset[subset])-1:
            self.next_event()
        elif current_index > 0:
            self.prev_event()
        else:
            self.event_index.set(self.eventsdb_subset[subset]['id'][0])
            self.plot_event()
        eventsdb_subset = self.eventsdb_subset[subset]
        self.eventsdb_subset[subset] = sqldf('SELECT * from eventsdb_subset WHERE id != %d' % event_index,locals())
        self.status_string.set('{0}: {1} events'.format(subset,len(self.eventsdb_subset[subset])))

        if 'id != {0}'.format(event_index) not in self.filter_list[subset]:
            self.filter_list[subset].append('id != {0}'.format(event_index))

        if event_index not in self.manual_delete:
            self.manual_delete.append(event_index)


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
                      'adj_id': 'Adjusted Event Number',
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
                      'intra_crossings': 'Intra-Event Threshold Crossings',
                      'intra_crossing_times_us': 'Intra-Event Threshold Crossing Times (us)',
                      'cluster_id': 'Cluster ID',
                      'rc_const1_us': 'RC Constant 1 (us)',
                      'rc_const2_us': 'RC Constant 2 (us)',
                      'level_current_pA': 'Level Current (pA)',
                      'level_duration_us': 'Level Duration (us)',
                      'blockages_pA': 'Blockage Level (pA)',
                      'residual_pA': 'Residuals (pA)',
                      'stdev_pA': 'Level Standard Deviation (pA)',
                      'count': 'Event Count',
                      'folding': 'Fold Fraction',
                      'event_shape': 'Event Shape',
                      'max_deviation_pA': 'Maximum Deviation (pA)',
                      'trimmed_shape': 'Trimmed Shape',
                      'trimmed_n_levels':'Trimmed N Levels',
                      'first_level':'First Level',
                      'last_level':'Last Level',
                      'first_level_fraction':'First Level Fraction',
                      'min_blockage_pA': 'Minimum Blockage (pA)',
                      'relative_min_blockage': 'Relative Minimum Blockage (unitless)',
                      'min_blockage_duration_us': 'Minimum Blockage Duration (us)'}
        self.unalias_dict = dict (list(zip(list(self.alias_dict.values()),list(self.alias_dict.keys()))))

    def save_subset(self):
        subset = self.subset_option.cget('text')
        folder = os.path.dirname(os.path.abspath(self.file_path_string))
        subset_file_path = folder + '\eventsdb-{0}.csv'.format(subset)
        subset_file = open(subset_file_path,'w')
        filter_file_path = folder + '\eventsdb-{0}-filters.txt'.format(subset)
        filter_file = open(filter_file_path,'w')
        self.eventsdb_subset[subset].to_csv(subset_file,index=False)
        for item in self.filter_list[subset]:
            filter_file.write('{0}\n'.format(item))
        subset_file.close()
        filter_file.close()

    def onclick(event):
        self.status_string.set('button=%d, x=%d, y=%d, xdata=%f, ydata=%f' % (event.button, event.x, event.y, event.xdata, event.ydata))

        
                
        
def main():
    root=tk.Tk()
    root.withdraw()
    file_path_string = tkinter.filedialog.askopenfilename(initialdir='C:/Users/kbrig035/Analysis/CUSUM/output/')
    folder = os.path.dirname(os.path.abspath(file_path_string))
    ratefile = folder + '\\rate.csv'
    summary = folder +'\\summary.txt'
    title = "CUSUM Tools: " + folder
    folder = folder + '\events\\'
    root.wm_title(title)
    summary = open(summary, 'r')
    eventsdb = pd.read_csv(file_path_string,encoding='utf-8')
    try:
        ratedb = pd.read_csv(ratefile, encoding='utf-8')
    except:
        ratedb=None
    App(root,eventsdb,ratedb,summary,folder,file_path_string).grid(row=0,column=0)
    root.mainloop()

if __name__=="__main__":
    main()

