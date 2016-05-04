import glob
import shutil
import os
import tkFileDialog
import Tkinter as tk
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



import time
import scipy.io as sio
import numpy as np

def get_filenames(initialfile):
    pattern = initialfile[:-19] + '*.log'
    name = initialfile[:-20] + '.log'
    settingsname = initialfile[:-20] + '.txt'
    files = glob.glob(pattern)
    timelist = [os.path.basename(fname)[-19:-4] for fname in files]
    etimestamps = [time.mktime(time.strptime(stamp,"%Y%m%d_%H%M%S")) for stamp in timelist]
    sorted_files = [fname for (estamp, fname) in sorted(zip(etimestamps, files), key=lambda pair: pair[0])]
    settings = sio.loadmat(sorted_files[0].replace('.log','.mat'))

    with open(settingsname, 'w') as f:
        for key, val in settings.iteritems():
            f.write('{0}={1}\n'.format(key, np.squeeze(val)))
        
    print 'Found {0} files matching {1}'.format(len(sorted_files),pattern)
    return sorted_files, name

def concatenate_files(file_list, name):        
    destination = open(name, 'wb')
    i=0
    for filename in file_list:
        i += 1
        print 'file {0} of {1}'.format(i,len(file_list))
        shutil.copyfileobj(open(filename, 'rb'), destination)
    destination.close()

def main():
    root=tk.Tk()
    root.withdraw()
    file_path = tkFileDialog.askopenfilename(initialdir='C:/Data/')
    file_list, name = get_filenames(file_path)
    concatenate_files(file_list, name)

if __name__=="__main__":
    main()
