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

import numpy.random.common
import numpy.random.bounded_integers
import numpy.random.entropy
import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import tkinter.filedialog
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import scipy.io as sio
from scipy.signal import bessel, filtfilt, welch
from scipy.optimize import curve_fit
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
        self.trace_toolbar = NavigationToolbar2Tk(self.trace_canvas, self.trace_toolbar_frame)
        self.trace_toolbar.update()

        
        self.trace_frame.grid(row=0,column=0,columnspan=6,sticky=tk.N+tk.S)
        self.trace_toolbar_frame.grid(row=1,column=0,columnspan=6)
        self.trace_canvas.get_tk_widget().grid(row=0,column=0,columnspan=6)


        

        ##### PSD plotting widgets #####
        self.psd_frame = tk.LabelFrame(parent,text='Power Spectrum')
        self.psd_fig = Figure(figsize=(7,5), dpi=100)
        self.psd_canvas = FigureCanvasTkAgg(self.psd_fig, master=self.psd_frame)
        self.psd_toolbar_frame = tk.Frame(self.psd_frame)
        self.psd_toolbar = NavigationToolbar2Tk(self.psd_canvas, self.psd_toolbar_frame)
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

        self.psd_length_entry = tk.Entry(self.control_frame)
        self.psd_length_label = tk.Label(self.control_frame, text='PSD Length (s)')
        self.psd_length_label.grid(row=0,column=4,sticky=tk.E+tk.W)
        self.psd_length_entry.grid(row=0,column=5,sticky=tk.E+tk.W)

        self.cutoff_entry = tk.Entry(self.control_frame)
        self.cutoff_entry.insert(0,'900000')
        self.cutoff_label = tk.Label(self.control_frame, text='Cutoff (Hz)')
        self.cutoff_label.grid(row=1,column=0,sticky=tk.E+tk.W)
        self.cutoff_entry.grid(row=1,column=1,sticky=tk.E+tk.W)

        self.order_entry = tk.Entry(self.control_frame)
        self.order_entry.insert(0,'8')
        self.order_label = tk.Label(self.control_frame, text='Filter Order')
        self.order_label.grid(row=1,column=2,sticky=tk.E+tk.W)
        self.order_entry.grid(row=1,column=3,sticky=tk.E+tk.W)

        self.downsample_entry = tk.Entry(self.control_frame)
        self.downsample_label = tk.Label(self.control_frame, text='Downsample')
        self.downsample_label.grid(row=1,column=4,sticky=tk.E+tk.W)
        self.downsample_entry.grid(row=1,column=5,sticky=tk.E+tk.W)

        self.plot_trace = tk.Button(self.control_frame, text='Update Trace', command=self.update_trace)
        self.plot_trace.grid(row=2,column=0,columnspan=2,sticky=tk.E+tk.W)

        self.normalize = tk.IntVar()
        self.normalize.set(0)
        self.normalize_check = tk.Checkbutton(self.control_frame, text='Normalize', variable = self.normalize)
        self.normalize_check.grid(row=2,column=2,sticky=tk.E+tk.W)
        
        self.plot_psd = tk.Button(self.control_frame, text='Update PSD', command=self.update_psd)
        self.plot_psd.grid(row=2,column=3,sticky=tk.E+tk.W)

        self.update_data = tk.Button(self.control_frame, text='Update Data', command=self.update_data)
        self.update_data.grid(row=2,column=4,columnspan=1,sticky=tk.E+tk.W)

        self.overlay_cusum = tk.Button(self.control_frame, text='Overlay CUSUM', command=self.overlay_cusum)
        self.overlay_cusum.grid(row=2,column=5,columnspan=1,sticky=tk.E+tk.W)
        

        ##### Feedback Widgets #####
        self.feedback_frame = tk.LabelFrame(parent, text='Status')
        self.feedback_frame.grid(row=2,column=6,columnspan=6,sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.wildcard = tk.StringVar()
        self.wildcard_label = tk.Label(self.feedback_frame, textvariable=self.wildcard)
        self.wildcard_label.grid(row=0,column=0,columnspan=6,sticky=tk.E+tk.W)
        self.export_psd = tk.Button(self.feedback_frame, text='Export PSD',command=self.export_psd)
        self.export_psd.grid(row=1,column=0,columnspan=6,sticky=tk.E+tk.W)
        self.export_trace = tk.Button(self.feedback_frame, text='Export Trace',command=self.export_trace)
        self.export_trace.grid(row=2,column=0,columnspan=6,sticky=tk.E+tk.W)
        self.get_filenames(self.file_path)
        self.load_memmaps()
        self.initialize_samplerate()

    ##### utility functions #####

    


    def overlay_cusum(self):
        analysis_dir = tkinter.filedialog.askdirectory(initialdir='G:/NPN/Filter Scaling/K435PC/500bp',title='Choose analysis directory')
        baseline_path = analysis_dir + '/baseline.csv'
        ratefile_path = analysis_dir + '/rate.csv'
        config_path = analysis_dir + '/summary.txt'
        self.events_flag = True
        self.baseline_flag = True
        try:
            self.ratefile = pd.read_csv(ratefile_path,encoding='utf-8')
        except IOError:
            self.overlay_flag = False
            self.wildcard.set('rate.csv not found in given directory')
        try:
            self.baseline_file = pd.read_csv(baseline_path,encoding='utf-8')
        except IOError:
            self.overlay_flag = False
            self.wildcard.set('baseline.csv not found in given directory')
        with open(config_path,'r') as config:
            for line in config:
                if 'threshold' in line:
                    line = re.split('=|\n',line)
                    self.threshold = float(line[1])
                if 'hysteresis' in line:
                    line = re.split('=|\n',line)
                    self.hysteresis = float(line[1])
                if 'cutoff' in line:
                    line = re.split('=|\n',line)
                    self.config_cutoff = int(line[1])
                if 'poles' in line:
                    line = re.split('=|\n',line)
                    self.config_order = int(line[1])


    def export_psd(self):
        try:
            data_path = tkinter.filedialog.asksaveasfilename(defaultextension='.csv',initialdir='G:/PSDs for Sam')
            np.savetxt(data_path,np.c_[self.f, self.Pxx, self.rms],delimiter=',')
        except AttributeError:
            self.wildcard.set('Plot the PSD first')

    def export_trace(self):
        try:
            data_path = tkinter.filedialog.asksaveasfilename(defaultextension='.csv',initialdir='G:/Analysis/Pores/NPN/PSDs')
            np.savetxt(data_path,self.plot_data,delimiter=',')
        except AttributeError:
            self.wildcard.set('Plot the trace first')

    def get_file_index(self, samplenum):
        i = 0
        try:
            while self.file_start_index[i+1] < samplenum:
                i += 1
        except IndexError:
            i = len(self.file_start_index)
        return i
        
        
    def load_mapped_data(self):
        if self.start_entry.get()!='':
            self.start_time = float(self.start_entry.get())
            start_index = int((float(self.start_entry.get())*self.samplerate))
        else:
            self.start_time = 0
            start_index = 0
            
        
        start_f = self.get_file_index(start_index)


        if self.end_entry.get()!='':
            self.end_time = float(self.end_entry.get())
            end_index = int((float(self.end_entry.get())*self.samplerate))
            if end_index > self.total_samples:
                end_index = self.total_samples
        else:
            end_index = start_index + len(self.maps[start_f])        
        
        end_f = self.get_file_index(end_index)

        if start_f == end_f:
            filesize = len(self.maps[start_f])
            tempdata = self.maps[start_f][start_index - self.file_start_index[start_f]:end_index - self.file_start_index[start_f]]
            settings = self.settings[start_f]
            data = self.scale_raw_data(tempdata,settings)     
        else:
            filesize = len(self.maps[start_f])
            tempdata = self.maps[start_f][start_index - self.file_start_index[start_f]:]
            settings = self.settings[start_f]
            data = self.scale_raw_data(tempdata,settings)
            for i in range(start_f+1,end_f):
                tempdata = self.maps[i]
                settings = self.settings[i]
                data = np.concatenate((data,self.scale_raw_data(tempdata,settings)))
            tempdata = self.maps[end_f]
            settings = self.settings[end_f]
            filesize = len(self.maps[end_f])
            data = np.concatenate((data, self.scale_raw_data(self.maps[end_f][:end_index - self.file_start_index[end_f]],settings)))
        self.data = data

    def scale_raw_data(self,tempdata,settings):
        samplerate = np.floor(np.squeeze(settings['ADCSAMPLERATE']))
        TIAgain = np.squeeze(settings['SETUP_TIAgain'])
        preADCgain = np.squeeze(settings['SETUP_preADCgain'])
        currentoffset = np.squeeze(settings['SETUP_pAoffset'])
        voltageoffset = np.squeeze(settings['SETUP_mVoffset'])
        ADCvref = np.squeeze(settings['SETUP_ADCVREF'])
        ADCbits = np.squeeze(settings['SETUP_ADCBITS'])
        if samplerate != self.samplerate:
            self.wildcard.set('One of your files does not match the global sampling rate!')
        closedloop_gain = TIAgain*preADCgain
        bitmask = (2**16 - 1) - (2**(16-ADCbits) - 1)
        tempdata = tempdata.astype(np.uint16) & bitmask
        tempdata = ADCvref - (2*ADCvref) * tempdata.astype(float)/ float(2**16)
        tempdata = -tempdata/float(closedloop_gain) + float(currentoffset)
        return tempdata * 1e12
            
    def load_memmaps(self):
        columntypes = np.dtype([('current', np.uint16)])
        self.maps = [np.memmap(str(f), dtype=columntypes, mode='r')['current'] for f in self.sorted_files]
        self.settings = [sio.loadmat(f.replace('.log','.mat')) for f in self.sorted_files]
        total = 0
        self.file_start_index = [0]
        for m in self.maps:
            total += len(m)
            self.file_start_index.append(total)
        self.total_samples = total
        self.file_start_index = np.array(self.file_start_index,dtype=np.int64)
        
    def get_filenames(self, initialfile):
        pattern = initialfile[:-19] + '*.log'
        files = glob.glob(pattern)
        timelist = [os.path.basename(fname)[-19:-4] for fname in files]
        etimestamps = [time.mktime(time.strptime(stamp,"%Y%m%d_%H%M%S")) for stamp in timelist]
        self.sorted_files = [fname for (estamp, fname) in sorted(zip(etimestamps, files), key=lambda pair: pair[0])]
        self.wildcard.set('Found {0} files matching {1}'.format(len(self.sorted_files),pattern))
        
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

    def downsample_data(self):
        self.downsampled_data = self.filtered_data[::int(self.samplerate / self.downsample_entry.get())]

    def initialize_samplerate(self):
        settings = self.settings[0]
        self.samplerate = np.floor(np.squeeze(settings['ADCSAMPLERATE']))

    ##### Plot Updating functions #####
    def update_trace(self):
        self.load_mapped_data()
        self.filtered_data = self.data
        self.plot_data = self.filtered_data
        plot_samplerate = self.samplerate
        
        if self.cutoff_entry.get()!='' and self.order_entry!='':
            self.filter_data()
            self.plot_data = self.filtered_data
        if self.downsample_entry.get()!='':
            self.downsample_data()
            self.plot_data = self.downsampled_data
            plot_samplerate = float(self.downsample_entry.get())
        

        
        
        self.trace_fig.clf()
        a = self.trace_fig.add_subplot(111)

        if self.events_flag:
            db = self.ratefile
            start_time = self.start_time
            end_time = self.end_time
            good_start = np.squeeze(sqldf('SELECT start_time_s from db WHERE start_time_s >= {0} AND start_time_s < {1} AND type IN (0,1)'.format(start_time,end_time),locals()).values)*1e6
            bad_start = np.squeeze(sqldf('SELECT start_time_s from db WHERE start_time_s >= {0} AND start_time_s < {1} AND type>1'.format(start_time,end_time),locals()).values)*1e6
            good_end = np.squeeze(sqldf('SELECT end_time_s from db WHERE end_time_s >= {0} AND end_time_s < {1} AND type IN (0,1)'.format(start_time,end_time),locals()).values)*1e6
            bad_end = np.squeeze(sqldf('SELECT end_time_s from db WHERE end_time_s >= {0} AND end_time_s < {1} AND type>1'.format(start_time,end_time),locals()).values)*1e6

            for gs, ge in zip(np.atleast_1d(good_start),np.atleast_1d(good_end)):
                a.axvspan(gs,ge,color='g',alpha=0.3)
            for bs, be in zip(np.atleast_1d(bad_start),np.atleast_1d(bad_end)):
                a.axvspan(bs,be,color='r',alpha=0.3)

        

        time = np.linspace(1.0/plot_samplerate,len(self.plot_data)/float(plot_samplerate),len(self.plot_data))+self.start_time
        
        a.set_xlabel(r'Time ($\mu s$)')
        a.set_ylabel('Current (pA)')
        self.trace_fig.subplots_adjust(bottom=0.14,left=0.21)
        a.plot(time*1e6,self.plot_data,'.',markersize=1)

        if self.baseline_flag:
            if self.config_cutoff != int(self.cutoff_entry.get()) or self.config_order != int(self.order_entry.get()):
                self.wildcard.set('Filter settings in config file do not match plotting filter settings, overlay will be inaccurate')
            db = self.baseline_file
            start_time = self.start_time
            end_time = self.end_time
            times = np.squeeze(sqldf('SELECT time_s from db',locals()).values)
            times = np.sort(times)

            start_block = times[0]
            for time in times:
                if time <= start_time and time >= start_block:
                    start_block = time
            


            baseline_db = sqldf('SELECT * from db WHERE time_s >= {0} and time_s < {1}'.format(start_block,end_time),locals())
            times = baseline_db['time_s'].values
            means = baseline_db['baseline_pA'].values
            stdevs = baseline_db['stdev_pA'].values
  
            numblocks = len(means)
            for i in range(numblocks):
                if i == 0:
                    xmin = start_time
                else:
                    xmin = times[i]
                if i+1 == numblocks:
                    xmax = end_time
                else:
                    xmax = times[i+1]
                
                sign = np.sign(means[i])
                a.plot((xmin*1e6,xmax*1e6), (means[i]-sign*(self.threshold - self.hysteresis)*stdevs[i],means[i]-sign*(self.threshold - self.hysteresis)*stdevs[i]), '--',color='y')
                a.plot((xmin*1e6,xmax*1e6), (means[i]-sign*self.threshold*stdevs[i],means[i]-sign*self.threshold*stdevs[i]), '--',color='y')
                a.plot((xmin*1e6,xmax*1e6), (means[i],means[i]), '--', color='black')
                
        self.trace_canvas.draw()

    def update_psd(self):
        self.load_mapped_data()
        self.filtered_data = self.data
        self.plot_data = self.filtered_data
        plot_samplerate = self.samplerate
        bandwidth = 1.0e6
        
        if self.cutoff_entry.get()!='' and self.order_entry!='':
            self.filter_data()
            self.plot_data = self.filtered_data
            maxf = 2*float(self.cutoff_entry.get())
            bandwidth = maxf/2.0
        else:
            maxf = 2e6
        if (self.psd_length_entry.get()!=''):
            length = 2**np.ceil(np.log2(float(self.psd_length_entry.get())*plot_samplerate))
            if (length > len(self.filtered_data)):
                length = len(self.filtered_data)
        else:
            length = np.minimum(2**20,len(self.filtered_data))
        end_index = int(np.floor(len(self.filtered_data)/length)*length)

        current = np.average(self.filtered_data[:end_index])
        
        f, Pxx = welch(self.filtered_data, plot_samplerate,nperseg=length)
        self.rms = self.integrate_noise(f, Pxx)
        
        if self.normalize.get():
            Pxx /= current**2
            Pxx *= bandwidth
            self.rms /= np.absolute(current)
           
        self.f = f
        self.Pxx = Pxx
        
        minf = 1  
        BW_index = np.searchsorted(f, maxf/2)
        logPxx = np.log10(Pxx[1:BW_index])
        minP = 10**np.floor(np.amin(logPxx))
        maxP = 10**np.ceil(np.amax(logPxx))


        df = f[1]-f[0]
        fitmax = 10000
        freqstop = len(f[f<=100])
        N = len(f[f<fitmax])
        fnorm = self.f[1:N]
        if self.normalize.get():
            Pxx_norm = self.Pxx[1:N]
        else:
            Pxx_norm = self.Pxx[1:N]*bandwidth/current**2

        #popt, pcov = curve_fit(self.fitfunc, fnorm, np.log10(Pxx_norm), p0=[1.0,1,1000.0, 0.0001], sigma=np.sqrt(np.arange(1,N)+np.sqrt(3)/3), maxfev=100000)
            
        #f0 = popt[0]
        #alpha = popt[1]
        #fstar = popt[2]
        #offset = popt[3]
        
        #L_simple = self.old_L(Pxx_norm[:freqstop], df, bandwidth)
        #L_adj = self.corrected_L(fnorm[:freqstop], Pxx_norm[:freqstop], f0, alpha, fstar, offset, df, bandwidth)
        
        self.psd_fig.clf()
        a = self.psd_fig.add_subplot(111)
        a.set_xlabel('Frequency (Hz)')
        a.set_ylabel(r'Spectral Power ($\mathrm{pA}^2/\mathrm{Hz}$)')
        a.set_xlim(minf, maxf)
        a.set_ylim(minP, maxP)
        self.psd_fig.subplots_adjust(bottom=0.14,left=0.21)
        a.loglog(f[1:],Pxx[1:],'b-')
        #if self.normalize.get():
        #    a.loglog(fnorm, 10**self.fitfunc(f[1:N], f0, alpha, fstar, offset),'g')
        #else:
        #    a.loglog(fnorm, 10**self.fitfunc(f[1:N], f0, alpha, fstar, offset)*current**2/bandwidth,'g')
        for tick in a.get_yticklabels():
            tick.set_color('b')

        
        a2 = a.twinx()
        a2.semilogx(f, self.rms, 'r-')
        a2.set_ylabel('RMS Noise (pA)')
        a2.set_xlim(minf, maxf)
        for tick in a2.get_yticklabels():
            tick.set_color('r')
        a2.format_coord = make_format(a2, a)
        
        self.psd_canvas.draw()

        #psd1hz = 10**self.fitfunc(1.0, f0, alpha, fstar, offset)*current**2/bandwidth

       # self.wildcard.set('RMS = {:0.2f} pA\tL[old] = {:.3g}\tL[adjusted] = {:.3g}\tPSD@1Hz = {:.3g} pA\u00b2/Hz'.format(np.std(self.filtered_data), L_simple, L_adj,psd1hz))
  
        
    def fitfunc(self, f, f0, alpha, fstar, offset):
        return np.log10((f0/f)**alpha + alpha*(f0/fstar)**(1+alpha)*(f/f0) + offset)


    def corrected_L(self, f, Pxx, f0, alpha, fstar, offset, df, B):
        integrand = Pxx - alpha*(f0/fstar)**(1+alpha)*(f/f0) - offset
        return np.sqrt(np.sum(integrand)*df/B)

    def old_L(self, Pxx, df, B):
        return np.sqrt(np.sum(Pxx)*df/B)

    
    def update_data(self):
        self.get_filenames(self.file_path)
        self.load_memmaps()
        self.initialize_samplerate()


def main():
    root=tk.Tk()
    root.withdraw()
    file_path = tkinter.filedialog.askopenfilename(initialdir='C:/Data/')
    App(root,file_path).grid(row=0,column=0)
    root.mainloop()

if __name__=="__main__":
    main()

