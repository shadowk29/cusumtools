import numpy as np
from scipy.signal import welch
from scipy.optimize import curve_fit
import matplotlib.pyplot as pl


class Pore:
    def __init__(self, tracefiles, samplerate, psdlength, cutoff, diameters, concentration, conductances, conductivity, thickness):
        ##physical constants and initial guesses
        Na = 6.022e23
        e = 1.602e-19 ## C
        surface_charge = 1.0e-19 ## C/nm^2 https://doi.org/10.1088/0957-4484/21/33/335703
        K_mobility = 1.0e11 ## nm^2/Vs https://doi.org/10.1021/nl052107w
        self.conductivity = conductivity
        self.lengthscale = (concentration * Na / 1.0e24)**(1.0/3.0)

        
        self.spectra = []
        for f in tracefiles:
            self.spectra.append(SpectrumSample(f, samplerate, psdlength, cutoff))
            
        self.ell = thickess * lengthscale
        self.charge = e/surface_charge * self.lengthscale**2
        self.mobility = 4.0 * K_mobility * surface_charge / conductivity * self.lengthscale 
        self.surface = 2.0e-3 ## https://doi.org/10.1088/1361-6528/ab2d35
        self.bulk = 1.5e-6 ## https://doi.org/10.1088/1361-6528/ab2d35
        self.access = 1.5e-6 ## https://doi.org/10.1088/1361-6528/ab2d35
            
    def fit_spectra(self):
        for s in self.spectra:
            s.fit_spectrum()
        self.pinknoises = [s.pink for s in self.spectra]
            

    
        
class SpectrumSample:
    def __init__(self, tracefile, samplerate, psdlength, cutoff):
        with open(tracefile, 'rb') as f:
            columntypes = np.dtype([('curr_pA', '>f8'), ('volt_mV', '>f8')])
            self.raw = np.memmap(f, dtype=columntypes, mode='r')['curr_pA']
        self.f, self.Pxx = welch(self.raw, samplerate,nperseg=psdlength)
        inds = [self.f <= cutoff]
        self.f = self.f[inds]
        self.Pxx = self.Pxx[inds]
        self.current = np.average(self.raw)
        self.Pxx *= cutoff/self.current**2
        self.Pxx *= self.f

    def fit_spectrum(self):
        self.thermal = 1.0e-3 ##needs testing
        self.pink = 1
        self.brown = 1.0e-3
        self.p0 = [self.thermal, self.pink, self.brown]
        popt, pcov = curve_fit(psd_fit, self.f, self.Pxx, self.p0)
        self.thermal, self.pink, self.brown = popt
        pl.loglog(self.f, self.Pxx, self.f, psd_fit(self.f, self.thermal, self.pink, self.brown))
        pl.show()
        

def psd_fit(f, thermal, pink, brown):
    return thermal*f + pink + brown/f

def noise_fit(x, bulk, surface, access, length, charge, mobility):
    fac = 1.0 / (1.0 + (4.0/np.pi)*(length/(x + mobility)))
    noise = fac**2
    npose *= 1.0/x**3
    noise *= (6.0*access + fac**2 * (4.0*x/length*bulk + charge*x**2/length*surface))
    return noise
    
        
        
        
        
