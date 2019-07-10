import numpy as np
import matplotlib.pyplot as pl
import pandas as pd
from scipy.optimize import curve_fit
import tkFileDialog
import Tkinter

def fitfunc(f, f0, alpha, fstar, offset):
    return np.log10((f0/f)**alpha + alpha*(f0/fstar)**(1+alpha)*(f/f0) + offset)


def corrected_L(f, S, f0, alpha, fstar, offset, df, B):
    integrand = S - alpha*(f0/fstar)**(1+alpha)*(f/f0) - offset
    return np.sqrt(np.sum(integrand)*df/B)

def old_L(f, S, df, B):
    return np.sqrt(np.sum(S)*df/B)

def main():
    root = Tkinter.Tk()
    root.withdraw()
    psdfile = tkFileDialog.askopenfilename()
    psdfile = psdfile.replace('.bin','.psd')
    root.destroy()
    B = 100000
    N = 10000
    psd = pd.read_csv(psdfile,sep='\t',names=['f','S','integral','norm'])
    f = psd['f'].values[1:N]
    df = f[1]-f[0]
    S = psd['norm'].values[1:N]
    popt, pcov = curve_fit(fitfunc, f, np.log10(S), p0=[1.0,1,1000.0, 0.0001], sigma=np.sqrt(np.arange(1,N)+np.sqrt(3)/3), maxfev=100000)
    print popt
    print np.sqrt(np.diag(pcov))


    f0 = popt[0]
    alpha = popt[1]
    fstar = popt[2]
    offset = popt[3]
    
    pl.loglog(f,S)
    pl.loglog(f, 10**fitfunc(f, f0, alpha, fstar, offset))
    pl.show()

    print 'Adjusted L: {0:.6f}'.format(corrected_L(f[:100], S[:100], f0, alpha, fstar, offset, df, B))
    print 'Old L: {0:.6f}'.format(old_L(f[:100], S[:100], df, B))
    print 'New alpha: {0:.6f}'.format(popt[1])
    
    
if __name__=="__main__":
    main()
