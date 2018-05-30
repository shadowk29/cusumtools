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

import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import tkFileDialog
import Tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import scipy.io as sio
from scipy.signal import bessel, filtfilt, welch
from scikits.samplerate import resample
import pylab as pl
import glob
import os
import time
import pandas as pd
from pandasql import sqldf
import re

def make_format(current, other):
    # current and other are axes
    def format_coord(x, y):
        # x, y are data coordinates
        # convert to display coords
        display_coord = current.transData.transform((x,y))
        inv = other.transData.inverted()
        # convert back to data coords with respect to ax
        ax_coord = inv.transform(display_coord)
        coords = [ax_coord, (x, y)]
        return ('Left: {:<40}    Right: {:<}'
                .format(*['({:.3f}, {:.3f})'.format(x, y) for x,y in coords]))
    return format_coord

    
class App(tk.Frame):
    def __init__(self, parent,file_path):
        tk.Frame.__init__(self, parent)
        parent.deiconify()
        self.events_flag = False
        self.baseline_flag = False
        self.file_path = file_path
                
        ##### Trace plotting widgets #####
        self.trace_frame = tk.LabelFrame(parent,text='Current Trace')
        self.trace_fig = Figure(figsize=(7,5), dpi=100)
        self.trace_canvas = FigureCanvasTkAgg(self.trace_fig, master=self.trace_frame)
        self.trace_toolbar_frame = tk.Frame(self.trace_frame)
        self.trace_toolbar = NavigationToolbar2TkAgg(self.trace_canvas, self.trace_toolbar_frame)
        self.trace_toolbar.update()

        
        self.trace_frame.grid(row=0,column=0,columnspan=6,sticky=tk.N+tk.S)
        self.trace_toolbar_frame.grid(row=1,column=0,columnspan=6)
        self.trace_canvas.get_tk_widget().grid(row=0,column=0,columnspan=6)


        

        ##### PSD plotting widgets #####
        self.psd_frame = tk.LabelFrame(parent,text='Power Spectrum')
        self.psd_fig = Figure(figsize=(7,5), dpi=100)
        self.psd_canvas = FigureCanvasTkAgg(self.psd_fig, master=self.psd_frame)
        self.psd_toolbar_frame = tk.Frame(self.psd_frame)
        self.psd_toolbar = NavigationToolbar2TkAgg(self.psd_canvas, self.psd_toolbar_frame)
        self.psd_toolbar.update()
        

        self.psd_frame.grid(row=0,column=6,columnspan=6,sticky=tk.N+tk.S)
        self.psd_toolbar_frame.grid(row=1,column=6,columnspan=6)
        self.psd_canvas.get_tk_widget().grid(row=0,column=6,columnspan=6)



        ##### Control widgets #####
        self.control_frame = tk.LabelFrame(parent, text='Controls')
        self.control_frame.grid(row=2,column=0,columnspan=6,sticky=tk.N+tk.S+tk.E+tk.W)


        self.start_entry = tk.Entry(self.control_frame)
        self.start_entry.insert(0,'0')
        self.start_label = tk.Label(self.control_frame, text='Start Time (s)')
        self.start_label.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.start_entry.grid(row=0,column=1,sticky=tk.E+tk.W)

        self.end_entry = tk.Entry(self.control_frame)
        self.end_entry.insert(0,'10')
        self.end_label = tk.Label(self.control_frame, text='End Time (s)')
        self.end_label.grid(row=0,column=2,sticky=tk.E+tk.W)
        self.end_entry.grid(row=0,column=3,sticky=tk.E+tk.W)

        self.cutoff_entry = tk.Entry(self.control_frame)
        self.cutoff_entry.insert(0,'')
        self.cutoff_label = tk.Label(self.control_frame, text='Cutoff (Hz)')
        self.cutoff_label.grid(row=1,column=0,sticky=tk.E+tk.W)
        self.cutoff_entry.grid(row=1,column=1,sticky=tk.E+tk.W)

        self.order_entry = tk.Entry(self.control_frame)
        self.order_entry.insert(0,'')
        self.order_label = tk.Label(self.control_frame, text='Filter Order')
        self.order_label.grid(row=1,column=2,sticky=tk.E+tk.W)
        self.order_entry.grid(row=1,column=3,sticky=tk.E+tk.W)


        self.samplerate_entry = tk.Entry(self.control_frame)
        self.samplerate_entry.insert(0,'250000')
        self.samplerate_label = tk.Label(self.control_frame, text='Sampling Frequency (Hz)')
        self.samplerate_label.grid(row=1,column=4,sticky=tk.E+tk.W)
        self.samplerate_entry.grid(row=1,column=5,sticky=tk.E+tk.W)

        self.savegain_entry = tk.Entry(self.control_frame)
        self.savegain_entry.insert(0,'1')
        self.savegain_label = tk.Label(self.control_frame, text='Sampling Frequency (Hz)')
        self.savegain_label.grid(row=0,column=4,sticky=tk.E+tk.W)
        self.savegain_entry.grid(row=0,column=5,sticky=tk.E+tk.W)

        
        self.plot_trace = tk.Button(self.control_frame, text='Update Trace', command=self.update_trace)
        self.plot_trace.grid(row=2,column=0,columnspan=2,sticky=tk.E+tk.W)

        self.normalize = tk.IntVar()
        self.normalize.set(0)
        self.normalize_check = tk.Checkbutton(self.control_frame, text='Normalize', variable = self.normalize)
        self.normalize_check.grid(row=2,column=2,sticky=tk.E+tk.W)
        
        self.plot_psd = tk.Button(self.control_frame, text='Update PSD', command=self.update_psd)
        self.plot_psd.grid(row=2,column=3,sticky=tk.E+tk.W)

        ##### Feedback Widgets #####
        self.feedback_frame = tk.LabelFrame(parent, text='Status')
        self.feedback_frame.grid(row=2,column=6,columnspan=6,sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.export_psd = tk.Button(self.feedback_frame, text='Export PSD',command=self.export_psd)
        self.export_psd.grid(row=1,column=0,columnspan=6,sticky=tk.E+tk.W)
        self.export_trace = tk.Button(self.feedback_frame, text='Export Trace',command=self.export_trace)
        self.export_trace.grid(row=2,column=0,columnspan=6,sticky=tk.E+tk.W)

        self.load_memmap()
        self.initialize_samplerate()

    def export_psd(self):
        try:
            data_path = tkFileDialog.asksaveasfilename(defaultextension='.csv',initialdir='G:\PSDs for Sam')
            np.savetxt(data_path,np.c_[self.f, self.Pxx, self.rms],delimiter=',')
        except AttributeError:
            self.wildcard.set('Plot the PSD first')

    def export_trace(self):
        try:
            data_path = tkFileDialog.asksaveasfilename(defaultextension='.csv',initialdir='G:\Analysis\Pores\NPN\PSDs')
            np.savetxt(data_path,self.plot_data,delimiter=',')
        except AttributeError:
            self.wildcard.set('Plot the trace first')

    def load_mapped_data(self):
        self.total_samples = len(self.map)
        self.samplerate = int(self.samplerate_entry.get())
        if self.start_entry.get()!='':
            self.start_time = float(self.start_entry.get())
            start_index = int((float(self.start_entry.get())*self.samplerate))
        else:
            self.start_time = 0
            start_index = 0
            

        if self.end_entry.get()!='':
            self.end_time = float(self.end_entry.get())
            end_index = int((float(self.end_entry.get())*self.samplerate))
            if end_index > self.total_samples:
                end_index = self.total_samples

        self.data = self.map[start_index:end_index]
        self.data = float(self.savegain_entry.get()) * self.data
            
    def load_memmap(self):
        columntypes = np.dtype([('current', '>i2'), ('voltage', '>i2')])
        self.map = np.memmap(self.file_path, dtype=columntypes, mode='r')['current']        
        
    def integrate_noise(self, f, Pxx):
        df = f[1]-f[0]
        return np.sqrt(np.cumsum(Pxx * df))

    def filter_data(self):
        cutoff = float(self.cutoff_entry.get())
        order = int(self.order_entry.get())
        Wn = 2.0 * cutoff/float(self.samplerate)
        b, a = bessel(order,Wn,'low')
        padding = 1000
        padded = np.pad(self.data, pad_width=padding, mode='median')
        self.filtered_data = filtfilt(b, a, padded, padtype=None)[padding:-padding]

    def initialize_samplerate(self):
        self.samplerate = float(self.samplerate_entry.get())

    ##### Plot Updating functions #####
    def update_trace(self):
        self.initialize_samplerate()
        self.load_mapped_data()
        self.filtered_data = self.data
        self.plot_data = self.filtered_data
        plot_samplerate = self.samplerate
        
        if self.cutoff_entry.get()!='' and self.order_entry!='':
            self.filter_data()
            self.plot_data = self.filtered_data

        self.trace_fig.clf()
        a = self.trace_fig.add_subplot(111)
       

        time = np.linspace(1.0/self.samplerate,len(self.plot_data)/float(self.samplerate),len(self.plot_data))+self.start_time
        
        a.set_xlabel(r'Time ($\mu s$)')
        a.set_ylabel('Current (pA)')
        self.trace_fig.subplots_adjust(bottom=0.14,left=0.21)
        a.plot(time*1e6,self.plot_data,'.',markersize=1)
                
        self.trace_canvas.show()

    def update_psd(self):
        self.initialize_samplerate()
        self.load_mapped_data()
        self.filtered_data = self.data
        self.plot_data = self.filtered_data
        plot_samplerate = self.samplerate
        
        if self.cutoff_entry.get()!='' and self.order_entry!='':
            self.filter_data()
            self.plot_data = self.filtered_data
            maxf = 2*float(self.cutoff_entry.get())       
        else:
            maxf = 2*float(self.samplerate_entry.get())

        length = np.minimum(2**18,len(self.filtered_data))
        end_index = int(np.floor(len(self.filtered_data)/length)*length)

        current = np.average(self.filtered_data[:end_index])

        f, Pxx = welch(self.filtered_data, plot_samplerate,nperseg=length)
        self.rms = self.integrate_noise(f, Pxx)
        
        if self.normalize.get():
            Pxx /= current**2
            Pxx *= maxf/2.0
            self.rms /= np.absolute(current)
           
        self.f = f
        self.Pxx = Pxx
        
        minf = 1  
        BW_index = np.searchsorted(f, maxf/2)
        logPxx = np.log10(Pxx[1:BW_index])
        minP = 10**np.floor(np.amin(logPxx))
        maxP = 10**np.ceil(np.amax(logPxx))
        
        
        self.psd_fig.clf()
        a = self.psd_fig.add_subplot(111)
        a.set_xlabel('Frequency (Hz)')
        a.set_ylabel(r'Spectral Power ($\mathrm{pA}^2/\mathrm{Hz}$)')
        a.set_xlim(minf, maxf)
        a.set_ylim(minP, maxP)
        self.psd_fig.subplots_adjust(bottom=0.14,left=0.21)
        a.loglog(f[1:],Pxx[1:],'b-')
        for tick in a.get_yticklabels():
            tick.set_color('b')

        
        a2 = a.twinx()
        a2.semilogx(f, self.rms, 'r-')
        a2.set_ylabel('RMS Noise (pA)')
        a2.set_xlim(minf, maxf)
        for tick in a2.get_yticklabels():
            tick.set_color('r')
        a2.format_coord = make_format(a2, a)
        
        self.psd_canvas.show()

def main():
    root=tk.Tk()
    root.withdraw()
    file_path = tkFileDialog.askopenfilename(initialdir='C:/Data/')
    App(root,file_path).grid(row=0,column=0)
    root.mainloop()

if __name__=="__main__":
    main()

