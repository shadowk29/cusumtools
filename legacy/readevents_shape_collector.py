import pandas as pd
from pandasql import sqldf
import numpy as np
import os
import tkinter.filedialog
import tkinter as tk
import ntpath

def get_files():
    files = []
    while True:
        print('Select file.\n')
        files.append(tkinter.filedialog.askopenfilename(initialdir='E:/DATA/2017/'))
        another = input('Select another file?  (y/n)\n--> ')
        if another.strip().lower()[0] == 'n':
            files = [_f for _f in files if _f]
            return files

def get_data(files):
    shape_stats = []
    all_shapes = []
    for i in range(len(files)):
        temp_data = pd.read_csv(files[i],encoding='utf-8')
        temp_shapes = sqldf('SELECT trimmed_shape as {0} from temp_data'.format(ntpath.basename(files[i].replace('.csv',''))),locals())['{0}'.format(ntpath.basename(files[i].replace('.csv','')))].value_counts()
        Ngood = len(sqldf('SELECT trimmed_shape as {0} from temp_data WHERE trimmed_shape>-1'.format(ntpath.basename(files[i].replace('.csv',''))),locals())['{0}'.format(ntpath.basename(files[i].replace('.csv','')))])
        fractions = pd.Series((100*temp_shapes/Ngood).round(1),name='Fraction of good')
        temp_shapes = pd.concat([temp_shapes,fractions],axis=1)
        all_shapes.append(temp_shapes)
    all_shapes = pd.concat(all_shapes,axis=1).fillna(0)
    print(all_shapes)
    return all_shapes


def save_data(all_shapes):
        save_file = tkinter.filedialog.asksaveasfile(initialdir='C:\\Users\BEAMISH\Documents\Nanopore files\\',mode='wb', defaultextension='.csv')
        all_shapes.to_csv(save_file,index=True)
        save_file.close()


def main():
    root=tk.Tk()
    root.withdraw()
    files = get_files()
    all_shapes = get_data(files)
    save_data(all_shapes)

if __name__=="__main__":
    main()

