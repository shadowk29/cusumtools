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
import tkFileDialog
import Tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from scipy.optimize import curve_fit
import itertools
from collections import OrderedDict
from scipy.stats import t
import pylab as pl

class FlashableLabel(tk.Label):
    def flash(self,count):
        bg = self.cget('background')
        fg = self.cget('foreground')
        self.configure(background=fg,foreground=bg)
        count -=1
        if (count > 0):
             self.after(500,self.flash, count) 

    
class App(tk.Frame):
    def __init__(self, parent,eventsdb,events_folder,file_path_string):
        tk.Frame.__init__(self, parent)
        
        self.file_path_string = file_path_string
        self.events_folder = events_folder
        self.eventsdb = eventsdb

        self.clicks_remaining = 0
        
        eventsdb['event_shape']=""
        eventsdb['trimmed_shape']=""
        eventsdb['trimmed_n_levels']=""
        


        max_subsets = 11
        self.eventsdb_subset = dict(('Subset {0}'.format(i), self.eventsdb) for i in range(max_subsets))
        self.capture_rate_subset = dict.fromkeys(list(self.eventsdb_subset.keys()))
        self.filter_list = dict(('Subset {0}'.format(i), []) for i in range(max_subsets))
        #self.survival_probability()
        #self.delay_probability()
        self.folding_distribution()
        self.count()

        self.export_type = None

        self.manual_delete = []
        
        column_list = list(eventsdb)
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
        self.export_plot_button = tk.Button(self.stats_frame,text='Export Data',command=self.export_plot_data)
        self.x_option = tk.OptionMenu(self.stats_frame, self.x_col_options, *[self.alias_dict.get(option,option) for option in self.column_list])
        self.y_option = tk.OptionMenu(self.stats_frame, self.y_col_options, *[self.alias_dict.get(option,option) for option in self.column_list])
        self.graph_option = tk.OptionMenu(self.stats_frame, self.graph_list, 'XY Plot', '1D Histogram', '2D Histogram', command=self.disable_options)
        self.include_baseline=tk.IntVar()
        self.include_baseline_check = tk.Checkbutton(self.stats_frame, text='Include Baseline', variable=self.include_baseline)
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

        self.n_states=tk.Label(self.stats_frame,text='Num States:')
        self.n_states_entry = tk.Entry(self.stats_frame)
        self.define_state_button = tk.Button(self.stats_frame,text='Redefine Blockage States',command=self.define_states)
        self.define_event_shapes_button = tk.Button(self.stats_frame,text='Redefine Event Shapes',command=self.define_shapes)

        self.capture_rate_button = tk.Button(self.stats_frame,text='Fit Capture Rate',command=self.capture_rate)
        self.use_histogram = tk.IntVar()
        self.use_histogram_check = tk.Checkbutton(self.stats_frame, text='Use Histogram', variable = self.use_histogram)


        self.stats_frame.grid(row=0,column=0,columnspan=6,sticky=tk.N+tk.S)
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

        parent.bind("<Return>", self.enter_key_press)


        self.n_states.grid(row=5,column=0,sticky=tk.E+tk.W)
        self.n_states_entry.grid(row=5,column=1,sticky=tk.E+tk.W)
        self.define_state_button.grid(row=5,column=2,sticky=tk.E+tk.W)
        self.define_event_shapes_button.grid(row=5,column=3,sticky=tk.E+tk.W)
        self.capture_rate_button.grid(row=5,column=4,sticky=tk.E+tk.W)
        self.use_histogram_check.grid(row=5,column=5,sticky=tk.E+tk.W)


        parent.bind("<Control-Key>", self.key_press)


        
        

        #Single Event widgets

        self.events_frame = tk.LabelFrame(parent,text='Single Event View')
        self.events_frame.columnconfigure(0, weight=1)
        self.events_frame.columnconfigure(3, weight=1)
        self.event_f = Figure(figsize=(7,5), dpi=100)
        self.event_canvas = FigureCanvasTkAgg(self.event_f, master=self.events_frame)
        self.event_toolbar_frame = tk.Frame(self.events_frame)
        self.event_toolbar = NavigationToolbar2TkAgg(self.event_canvas, self.event_toolbar_frame)
        self.event_toolbar.update()
        self.event_info_string = tk.StringVar()
        self.event_index = tk.IntVar()
        self.event_index.set(self.eventsdb_subset['Subset 0']['id'][0])
        self.event_entry = tk.Entry(self.events_frame, textvariable=self.event_index)
        self.plot_event_button = tk.Button(self.events_frame,text='Plot Event',command=self.plot_event)
        self.next_event_button = tk.Button(self.events_frame,text='Next',command=self.next_event)
        self.prev_event_button = tk.Button(self.events_frame,text='Prev',command=self.prev_event)
        self.delete_event_button = tk.Button(self.events_frame,text='Delete',command=self.delete_event)
        self.replicate_delete = tk.Button(self.events_frame,text='Replicate Deletions',command=self.replicate_manual_deletions)
        self.save_event_button = tk.Button(self.events_frame,text='Export Data',command=self.export_event_data)
        self.event_info_string.set('Ready')
        self.event_info_display = tk.Label(self.events_frame, textvariable=self.event_info_string)

        
        self.event_toolbar_frame.grid(row=1,column=0,columnspan=6)
        self.event_canvas.get_tk_widget().grid(row=0,column=0,columnspan=6)
        
        parent.bind("<Left>", self.left_key_press)
        parent.bind("<Right>", self.right_key_press)
        parent.bind("<Delete>", self.delete_key_press)

        self.events_frame.grid(row=0,column=6,columnspan=6,sticky=tk.N+tk.S)
        self.event_entry.grid(row=2,column=0,columnspan=3,sticky=tk.E+tk.W)
        self.event_info_display.grid(row=2,column=3,columnspan=3,sticky=tk.W+tk.E)
        self.plot_event_button.grid(row=3,column=0,columnspan=3,sticky=tk.E+tk.W)
        self.save_event_button.grid(row=3,column=3,columnspan=3,sticky=tk.E+tk.W)
        self.next_event_button.grid(row=4,column=3,columnspan=3,sticky=tk.E+tk.W)
        self.prev_event_button.grid(row=4,column=0,columnspan=3,sticky=tk.E+tk.W)
        self.delete_event_button.grid(row=5,column=0,columnspan=3,sticky=tk.E+tk.W)
        self.replicate_delete.grid(row=5,column=3,columnspan=3,sticky=tk.E+tk.W)
        
        


        #Datbase widgets

        self.db_frame = tk.LabelFrame(parent,text='Database Controls')
        self.db_frame.columnconfigure(0, weight=1)
        self.db_frame.columnconfigure(2, weight=1)
        self.db_frame.columnconfigure(4, weight=1)

        default_subset = tk.StringVar()
        default_subset.set('Subset 0')
        options = ['Subset {0}'.format(i) for i in range(max_subsets)]
        self.subset_option = tk.OptionMenu(self.db_frame, default_subset, *options,command=self.update_count)
        self.filter_button = tk.Button(self.db_frame,text='Filter Subset',command=self.filter_db)
        self.reset_button = tk.Button(self.db_frame,text='Reset Subset',command=self.reset_db)
        self.show_subset_details_button = tk.Button(self.db_frame, text='Display Filters', command=self.display_filters)
        self.save_subset_button = tk.Button(self.db_frame,text='Save Subset',command=self.save_subset)
        self.remove_nonconsecutive_button = tk.Button(self.db_frame,text='Remove Non-Consecutive',command=self.remove_nonconsecutive_events)
        self.filter_entry = tk.Entry(self.db_frame)

        
        self.db_frame.grid(row=2,column=0,columnspan=6,sticky=tk.E+tk.W+tk.S+tk.N)
        self.filter_entry.grid(row=0,column=0,columnspan=6,sticky=tk.E+tk.W)
        self.subset_option.grid(row=1,column=0,columnspan=2,sticky=tk.E+tk.W)
        self.filter_button.grid(row=1,column=2,columnspan=2,sticky=tk.E+tk.W)
        self.reset_button.grid(row=1,column=4,columnspan=2,sticky=tk.E+tk.W)
        
        self.save_subset_button.grid(row=2,column=0,columnspan=2,sticky=tk.E+tk.W)
        self.show_subset_details_button.grid(row=2,column=2,columnspan=2,sticky=tk.E+tk.W)
        self.remove_nonconsecutive_button.grid(row=2,column=4,columnspan=2,sticky=tk.E+tk.W)

        #Folder widgets

        #Status Update widgets
        self.status_frame = tk.LabelFrame(parent,text='Status')
        self.status_frame.grid(row=2,column=6,columnspan=6,sticky=tk.E+tk.W+tk.S+tk.N)
        self.status_string = tk.StringVar()
        self.status_string.set('Ready')
        self.status_display = FlashableLabel(self.status_frame, textvariable=self.status_string, background='black', foreground='white')

        self.status_display.grid(row=0,column=0,columnspan=6,sticky=tk.E+tk.W+tk.S+tk.N)

    def get_active_subsets(self):
        subset_list = []
        for key, val in self.filter_list.iteritems():
            if key == 'Subset 0' or len(val) > 0:
                subset_list.append(key)
        subset_list = sorted(subset_list)
        return subset_list

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
        subset_list = self.get_active_subsets()
        self.f.clf()
        self.a = self.f.add_subplot(111)
        
        self.f.subplots_adjust(bottom=0.14,left=0.21)
        self.xdata = []
        self.ydata = []
        fit_string = ''
        self.export_type = 'capture_rate'
        for subset in subset_list:
            if 'Nonconsecutive Events Removed' not in self.filter_list[subset]:
                db = self.eventsdb_subset[subset]
            else:
                db = self.capture_rate_subset[subset]
                
            indices = db['id'].values
            start_times = db['start_time_s'].values
            delays = np.diff(start_times)
            index_diff = np.diff(indices)
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
                fit_string = fit_string + u'{0}: {1}/{2} events used. Capture Rate is {3:.3g} \u00B1 {4:.1g} Hz (R\u00B2 = {5:.2g})\n'.format(subset,len(valid_delays),len(indices), popt[0], -t.isf(0.975,len(valid_delays))*np.sqrt(np.diag(pcov))[0], rsquared)
                self.xdata.append(valid_delays)
                self.ydata.append(probability)
                self.a.legend(loc='best',prop={'size': 10})
                self.canvas.show()
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
                fit_string = fit_string + u'{0}: {1}/{2} events used. Capture Rate is {3:.3g} \u00B1 {4:.1g} Hz (R\u00B2 = {5:.2g})\n'.format(subset,len(valid_delays),len(indices), popt[0], -t.isf(0.975,len(counts))*np.sqrt(np.diag(pcov))[0], rsquared)
                self.a.legend(loc='best',prop={'size': 10})
                self.canvas.show()
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
        subset_list = self.get_active_subsets()

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


        subset_frame = dict((key, tk.LabelFrame(top, text=key)) for key, val in self.eventsdb_subset.iteritems())
        subset_frame = OrderedDict(sorted(subset_frame.items()))
            
        filters = dict((key, tk.StringVar()) for key, val in subset_frame.iteritems())
        msg = dict((key, tk.Label(val, textvariable=filters[key])) for key, val in subset_frame.iteritems())
        
        i = 0
        for key, val in subset_frame.iteritems():
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
            
##    def delay_probability(self):
##        eventsdb = self.eventsdb
##        eventsdb_sorted = sqldf('SELECT * from eventsdb ORDER BY event_delay_s',locals())
##        numevents = len(eventsdb)
##        delay = [1.0 - float(i)/float(numevents) for i in range(0,numevents)]
##        eventsdb_sorted['delay_probability'] = delay
##        self.eventsdb = sqldf('SELECT * from eventsdb_sorted ORDER BY id',locals())
##        for key, val in self.eventsdb_subset.iteritems():
##            val = self.eventsdb
##        
##    def survival_probability(self):
##        eventsdb = self.eventsdb
##        eventsdb_sorted = sqldf('SELECT * from eventsdb ORDER BY duration_us',locals())
##        numevents = len(eventsdb)
##        survival = [1.0 - float(i)/float(numevents) for i in range(0,numevents)]
##        eventsdb_sorted['survival_probability'] = survival
##        self.eventsdb = sqldf('SELECT * from eventsdb_sorted ORDER BY id',locals())
##        for key, val in self.eventsdb_subset.iteritems():
##            val = self.eventsdb

    def folding_distribution(self):
        x = self.eventsdb['max_blockage_duration_us']/(self.eventsdb['duration_us']+self.eventsdb['max_blockage_duration_us'])
        self.eventsdb['folding'] = x
        for key, val in self.eventsdb_subset.iteritems():
            val = self.eventsdb


    def count(self):
        eventsdb = self.eventsdb
        eventsdb_sorted = sqldf('SELECT * from eventsdb ORDER BY id',locals())
        numevents = len(eventsdb)
        count = [i for i in range(0,numevents)]
        eventsdb_sorted['count'] = count
        self.eventsdb = sqldf('SELECT * from eventsdb_sorted ORDER BY id',locals())
        for key, val in self.eventsdb_subset.iteritems():
            val = self.eventsdb
        
                
    

    def reset_db(self):
        subset = self.subset_option.cget('text')
        self.eventsdb_subset[subset] = self.eventsdb
        self.capture_rate_subset[subset] = None
        self.filter_list[subset] = []
        self.status_string.set('{0}: {1} events'.format(subset,len(self.eventsdb_subset[subset])))

    def export_plot_data(self):
        data_path = tkFileDialog.asksaveasfilename(defaultextension='.csv')
        subset_list = self.get_active_subsets()
        if self.export_type == 'hist1d':
            x_label = self.x_option.cget('text')
            logscale_x = self.x_log_var.get()
            if (logscale_x):
                x_label = 'Log({0})'.format(x_label)
            data = OrderedDict()
            data[x_label] = self.xdata
            if len(subset_list) > 1:
                for i in range(len(subset_list)):
                    data['{0} Count'.format(subset_list[i])] = self.ydata[i]
            else:
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
            data_frame = pd.DataFrame({k : pd.Series(v) for k,v in data.iteritems()})
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
        self.num_states = int(self.n_states_entry.get())
        self.clicks_remaining = self.num_states*2
        self.status_string.set('Click on the 1D blockage level histogram {0} times'.format(self.clicks_remaining))
        self.state_array = np.zeros(self.num_states*2)


    def define_shapes(self):
        subset = self.subset_option.cget('text')
        if self.clicks_remaining > 0:
            self.status_string.set('Complete State Array First')
        else:
            type_array = []
            trimmed_type = []
            trimmed_Nlev = []
            state_means = np.zeros(self.num_states)
            i = 0
            while i < self.num_states*2:
                state_means[i/2] = 0.5*(self.state_array[i]+self.state_array[i+1])
                i += 2
            blockage_levels = [np.array(a,dtype=float)[1:-1] for a in self.eventsdb_subset[subset]['blockages_pA'].str.split(';')]
            for b in blockage_levels:
                event_type = []
                indices = [(np.abs(state_means - blevel)).argmin() for blevel in b]
                for level,index in itertools.izip(b,indices):
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
            self.eventsdb_subset[subset]['event_shape'] = type_array
            self.eventsdb_subset[subset]['trimmed_shape'] = trimmed_type
            self.eventsdb_subset[subset]['trimmed_n_levels'] = trimmed_Nlev
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
        self.canvas.show()

        

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


    def on_click(self, event):
        pass#print event.xdata, event.ydata

    def key_press(self, event):
        if event.keysym == 'a':
            self.set_axis_limits()

    def plot_xy(self):
        subset_list = self.get_active_subsets()
        self.export_type = 'scatter'
        logscale_x = self.x_log_var.get()
        logscale_y = self.y_log_var.get()
        x_label = self.x_option.cget('text')
        y_label = self.y_option.cget('text')
        x_col = np.squeeze(np.array([self.parse_db_col(self.unalias_dict.get(x_label,x_label),key) for key in subset_list]))
        y_col = np.squeeze(np.array([self.parse_db_col(self.unalias_dict.get(y_label,y_label),key) for key in subset_list]))


        xsign = np.sign(np.average(x_col[0])) if len(subset_list) > 1 else np.sign(np.average(x_col))
        ysign = np.sign(np.average(y_col[0])) if len(subset_list) > 1 else np.sign(np.average(y_col))

        self.f.clf()
        self.a = self.f.add_subplot(111)
        self.a.figure.canvas.mpl_connect('button_press_event', self.on_click)
        self.a.set_xlabel(x_label)
        self.a.set_ylabel(y_label)
        self.f.subplots_adjust(bottom=0.14,left=0.21)
        
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
        self.canvas.show()

    def plot_1d_histogram(self):
        subset_list = self.get_active_subsets()
        self.export_type = 'hist1d'
        logscale_x = self.x_log_var.get()
        logscale_y = self.y_log_var.get()
        x_label = self.x_option.cget('text')
        col = np.squeeze(np.array([self.parse_db_col(self.unalias_dict.get(x_label,x_label),key) for key in subset_list]))
        numbins = self.xbin_entry.get()
        self.f.clf()
        self.a = self.f.add_subplot(111)
        self.f.subplots_adjust(bottom=0.14,left=0.21)
        self.ydata = []
        if logscale_x:
            self.a.set_xlabel('Log(' +str(x_label)+')')
            self.a.set_ylabel('Count')
            if len(subset_list) > 1:
                for i in range(len(subset_list)):
                    col[i] *= np.sign(np.average(col[i]))
                    col[i] = np.log10(col[i])
                    y, self.xdata, patches = self.a.hist(col[i],bins=int(numbins),log=bool(logscale_y),histtype='step',stacked=False,fill=False,label=subset_list[i])
                    self.ydata.append(y)
            else:
                col *= np.sign(np.average(col))
                col = np.log10(col)
                self.ydata, self.xdata, patches = self.a.hist(col,bins=int(numbins),log=bool(logscale_y),histtype='step',stacked=False,fill=False,label=subset_list)
        else:
            self.a.set_xlabel(x_label)
            self.a.set_ylabel('Count')
            if len(subset_list) > 1:
                for i in range(len(subset_list)):
                    if x_label == 'Fold Fraction':
                        self.ydata, self.xdata, patches = self.a.hist(col[i],range=(0,0.5),bins=(0,0.1,0.2,0.3,0.4,0.5),log=bool(logscale_y),histtype='step',stacked=False,fill=False,label=subset_list[i])
                    else:
                        self.ydata, self.xdata, patches = self.a.hist(col[i],bins=int(numbins),log=bool(logscale_y),histtype='step',stacked=False,fill=False,label=subset_list[i])
            else:
                if x_label == 'Fold Fraction':
                    self.ydata, self.xdata, patches = self.a.hist(col,range=(0,0.5),bins=(0,0.1,0.2,0.3,0.4,0.5),log=bool(logscale_y),histtype='step',stacked=False,fill=False,label=subset_list)
                else:
                    self.ydata, self.xdata, patches = self.a.hist(col,bins=int(numbins),log=bool(logscale_y),histtype='step',stacked=False,fill=False,label=subset_list)
        self.a.legend(loc='best',prop={'size': 10})
        self.xdata = self.xdata[:-1] + np.diff(self.xdata)/2.0
        self.canvas.show()
        self.canvas.callbacks.connect('button_press_event', self.on_click)

        
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
        self.f.clf()
        self.a = self.f.add_subplot(111)
        self.a.set_xlabel(x_label)
        self.a.set_ylabel(y_label)
        if logscale_x:
            self.a.set_xlabel('Log(' +str(x_label)+')')
        if logscale_y:
            self.a.set_ylabel('Log(' +str(y_label)+')')
        self.f.subplots_adjust(bottom=0.14,left=0.21)
        xsign = np.sign(np.average(x_col))
        ysign = np.sign(np.average(y_col))
        z, x, y, image = self.a.hist2d(np.log10(xsign*x_col) if bool(logscale_x) else x_col,np.log10(ysign*y_col) if bool(logscale_y) else y_col,bins=[int(xbins),int(ybins)],norm=matplotlib.colors.LogNorm())
        x = x[:-1] + np.diff(x)/2.0
        y = y[:-1] + np.diff(y)/2.0
        xy = [zip([a]*len(y),y) for a in x]
        z = np.ravel(z)
        xy = np.reshape(xy,(len(z),2))
        self.xdata = xy[:,0]
        self.ydata = xy[:,1]
        self.zdata = z
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

    def plot_event(self):
        subset = self.subset_option.cget('text')
        index = self.event_index.get()
        if any(self.eventsdb_subset[subset]['id']==index):
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
            event_type = sqldf('SELECT type from eventsdb_subset WHERE id=%d' % index,locals())['type'][0]
            self.event_export_type = event_type
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
            self.event_info_string.set('Successfully plotted event {0}'.format(index))
        else:
            self.event_info_string.set('Event {0} is missing or deleted'.format(index))

    def export_event_data(self):
        data_path = tkFileDialog.asksaveasfilename(defaultextension='.csv')
        if self.event_export_type == 0:
            np.savetxt(data_path,np.c_[self.event_export_file['time'],self.event_export_file['current'],self.event_export_file['cusum']],delimiter=',')
        elif self.event_export_type == 1:
            np.savetxt(data_path,np.c_[self.event_export_file['time'],self.event_export_file['current'],self.event_export_file['cusum'], self.event_export_file['stepfit']],delimiter=',')

    def next_event(self):
        subset = self.subset_option.cget('text')
        try:
            current_index = self.eventsdb_subset[subset][self.eventsdb_subset[subset]['id'] == self.event_index.get()].index.tolist()[0]
        except IndexError:
            self.event_info_string.set('Event not found, resetting')
            current_index = -1
        if current_index < len(self.eventsdb_subset[subset])-1:
            next_index = self.eventsdb_subset[subset][self.eventsdb_subset[subset]['id'] > self.event_index.get()].index.tolist()[0]
            self.event_index.set(int(self.eventsdb_subset[subset]['id'][next_index]))
            self.plot_event()
        else:
            pass
            

    def prev_event(self):
        subset = self.subset_option.cget('text')
        try:
            current_index = self.eventsdb_subset[subset][self.eventsdb_subset[subset]['id'] == self.event_index.get()].index.tolist()[0]
        except IndexError:
            self.event_info_string.set('Event not found, resetting')
            current_index = 1
        if current_index > 0:
            prev_index = self.eventsdb_subset[subset][self.eventsdb_subset[subset]['id'] < self.event_index.get()].index.tolist()[-1]
            self.event_index.set(int(self.eventsdb_subset[subset]['id'][prev_index]))
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
                      'residual_pA': 'Residuals (pA)',
                      #'survival_probability': 'Survival Probablity',
                      #'delay_probability': 'Delay Probablity',
                      'stdev_pA': 'Level Standard Deviation (pA)',
                      'count': 'Event Count',
                      'folding': 'Fold Fraction',
                      'event_shape': 'Event Shape',
                      'max_deviation_pA': 'Maximum Deviation (pA)',
                      'trimmed_shape': 'Trimmed Shape',
                      'trimmed_n_levels':'Trimmed N Levels',
                      'min_blockage_pA': 'Minimum Blockage (pA)',
                      'relative_min_blockage': 'Relative Minimum Blockage (unitless)',
                      'min_blockage_duration_us': 'Minimum Blockage Duration (us)'}
        self.unalias_dict = dict (zip(self.alias_dict.values(),self.alias_dict.keys()))

    def save_subset(self):
        subset = self.subset_option.cget('text')
        folder = os.path.dirname(os.path.abspath(self.file_path_string))
        subset_file_path = folder + '\eventsdb-{0}.csv'.format(subset)
        subset_file = open(subset_file_path,'wb')
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
    file_path_string = tkFileDialog.askopenfilename(initialdir='C:/Users/kbrig035/Analysis/CUSUM/output/')
    folder = os.path.dirname(os.path.abspath(file_path_string))
    folder = folder + '\events\\'
    root.wm_title("CUSUM Tools")
    eventsdb = pd.read_csv(file_path_string,encoding='utf-8')
    App(root,eventsdb,folder,file_path_string).grid(row=0,column=0)
    root.mainloop()

if __name__=="__main__":
    main()

