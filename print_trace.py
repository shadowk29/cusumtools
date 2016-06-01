import tkFileDialog
import Tkinter as tk
import numpy as np


def main():
    root=tk.Tk()
    root.withdraw()
    file_path_string = tkFileDialog.askopenfilename(initialdir='C:/Data/')
    root.destroy()
    length_s = 9
    start_s = 10
    samplingfreq = 500000
    start = start_s * samplingfreq
    with open(file_path_string, 'rb') as f:
        columntypes = np.dtype([('curr_pA', '>f8'), ('volt_mV', '>f8')])
        current = np.memmap(f, dtype=columntypes, mode='r')['curr_pA']
        index = file_path_string.find('.bin')
        outname = file_path_string[:index]+'_'+str(start_s)+'_'+str(length_s)+'.csv'
        np.savetxt(outname,current[start_s+samplingfreq:(start_s+length_s)*samplingfreq])

    
if __name__=='__main__':
    main()
