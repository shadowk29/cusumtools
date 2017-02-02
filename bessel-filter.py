import matplotlib
matplotlib.use('TkAgg')
import numpy as np
from scipy.signal import bessel, filtfilt
from scipy.optimize import curve_fit
import Tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import pylab as pl

class App(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        parent.deiconify()

        #Plot Widgets
        self.plot_frame = tk.LabelFrame(parent,text='Filter Data')
        self.plot_fig = Figure(figsize=(7,5), dpi=100)
        self.plot_canvas = FigureCanvasTkAgg(self.plot_fig, master=self.plot_frame)
        self.plot_toolbar_frame = tk.Frame(self.plot_frame)
        self.plot_toolbar = NavigationToolbar2TkAgg(self.plot_canvas, self.plot_toolbar_frame)
        self.plot_toolbar.update()

        self.plot_frame.grid(row=0,column=0,columnspan=6,sticky=tk.N+tk.S)
        self.plot_toolbar_frame.grid(row=1,column=0,columnspan=6)
        self.plot_canvas.get_tk_widget().grid(row=0,column=0,columnspan=6)


        #Control Widgets
        self.control_frame = tk.LabelFrame(parent, text='Controls')
        self.control_frame.grid(row=1,column=0,columnspan=6,sticky=tk.N+tk.S+tk.E+tk.W)

        self.fs_entry = tk.Entry(self.control_frame)
        self.fs_entry.insert(0,'500')
        self.fs_label = tk.Label(self.control_frame, text='Sampling Frequency (kHz)')
        self.fs_label.grid(row=0,column=0,sticky=tk.E+tk.W)
        self.fs_entry.grid(row=0,column=1,sticky=tk.E+tk.W)

        self.fc_entry = tk.Entry(self.control_frame)
        self.fc_entry.insert(0,'95')
        self.fc_label = tk.Label(self.control_frame, text='Cutoff Frequency (kHz)')
        self.fc_label.grid(row=0,column=2,sticky=tk.E+tk.W)
        self.fc_entry.grid(row=0,column=3,sticky=tk.E+tk.W)

        self.poles = tk.IntVar(parent)
        self.poles.set(8)
        self.pole_option = tk.OptionMenu(self.control_frame, self.poles, 2, 4, 6, 8, 10)
        self.pole_label = tk.Label(self.control_frame, text='Poles')
        self.pole_label.grid(row=0,column=4,sticky=tk.E+tk.W)
        self.pole_option.grid(row=0,column=5,sticky=tk.E+tk.W)

        self.fit_button = tk.Button(self.control_frame, text='Fit Filter', command=self.update_filter)
        self.fit_button.grid(row=1,column=2,sticky=tk.E+tk.W)

        #Feedback Widgets
        self.feedback_frame = tk.LabelFrame(parent, text='Fit Parameters')
        self.feedback_frame.grid(row=2,column=0,columnspan=6,sticky=tk.N+tk.S+tk.E+tk.W)

        self.fit_report = tk.StringVar()
        self.fit_report_label = tk.Label(self.feedback_frame, textvariable=self.fit_report)
        self.fit_report_label.grid(row=0,column=0,columnspan=6,sticky=tk.E+tk.W)

    def update_report(self):
        self.fit_report.set('Rise time for this filter is {:0.2f} +/- {:0.2f} samples, or {:0.2f} +/- {:0.2f} us'.format(self.popt[1],self.errors[1],self.popt[1]*1.0e6/self.fs,self.errors[1]*1.0e6/self.fs))

    def bessel_shape(self, t, t0, tau):
        return 1.0 / (1.0 + np.exp(-(t-t0)/tau))
        
    def fit_filter(self, length, samples):
        self.popt, self.pcov = curve_fit(self.bessel_shape, samples, self.filtered_data)
        self.filter_fit = self.bessel_shape(samples, self.popt[0],self.popt[1])
        self.errors = np.sqrt(np.diag(self.pcov))

    def update_filter(self):
        self.fc = 1000 * float(self.fc_entry.get())
        self.fs = 1000 * float(self.fs_entry.get())
        length = int(5*self.fs/self.fc)
        self.generate_step(length)
        self.filter_data()
        samples = np.arange(0,length)

        self.fit_filter(length, samples)
        
        self.plot_fig.clf()
        a = self.plot_fig.add_subplot(111)
        a.set_xlabel('Sample Number')
        a.set_ylabel('Amplitude (Arb. Units)')
        a.set_ylim(-0.05,1.05)
        a.plot(samples,self.filtered_data,samples,self.filter_fit)
        self.plot_canvas.show()

        self.update_report()
        

    def filter_data(self):
        fc = 1000 * float(self.fc_entry.get())
        fs = 1000 * float(self.fs_entry.get())
        poles = int(self.poles.get())
        Wn = 2.0 * fc/fs
        b, a = bessel(poles, Wn, 'low')
        padded = np.pad(self.perfect_data, pad_width=poles, mode='edge')
        self.filtered_data = filtfilt(b, a, padded, method='pad', padlen=None)[poles:-poles]

    def generate_step(self, length):
        self.perfect_data = np.zeros(length)
        for i in range(length/2,length):
            self.perfect_data[i] = 1


def main():
    root=tk.Tk()
    root.withdraw()
    App(root).grid(row=0,column=0)
    root.mainloop()

if __name__=="__main__":
    main()

    
