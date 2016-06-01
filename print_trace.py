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
