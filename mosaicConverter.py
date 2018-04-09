##                                COPYRIGHT
##    Copyright (C) 2017 Philipp Karau (pkara031<at>uottawa.ca)
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

import glob
import os
import numpy as np
import sqlite3
import mosaic.mdio.sqlite3MDIO as sql
import Tkinter as tk
import pandas as pd
import pandasql as sqldf
import tkFileDialog
from progress.bar import ChargingBar, Bar
db=sql.sqlite3MDIO()

pd.options.mode.chained_assignment = None

def do_Stuff(file_path_string,events_directory_path,directory_path):
    db.openDB(glob.glob(file_path_string)[-1])
    q = "SELECT * from metadata WHERE ProcessingStatus='normal'"
    column_list = ['recIDX',
                   'ProcessingStatus',
                   'OpenChCurrent',
                   'NStates',
                   'CurrentStep',
                   'BlockDepth',
                   'EventStart',
                   'EventEnd',
                   'EventDelay',
                   'StateResTime',
                   'ResTime',
                   'RCConstant',
                   'AbsEventStart',
                   'ReducedChiSquared',
                   'ProcessTime',
                   'TimeSeries']

    column_list2 = ['id',
                    'type',
                    'start_time_s',
                    'event_delay_s',
                    'duration_us',
                    'baseline_before_pA',
                    'baseline_after_pA',
                    'effective_baseline_pA',
                    'average_blockage_pA',
                    'relative_average_blockage',
                    'max_blockage_pA',
                    'relative_max_blockage',
                    'max_blockage_duration_us',
                    'n_levels',
                    'rc_const1_us',
                    'residual_pA',
                    'max_deviation_pA',
                    'min_blockage_pA',
                    'relative_min_blockage',
                    'min_blockage_duration_us',
                    'level_current_pA',
                    'level_duration_us',
                    'blockages_pA',
                    'stdev_pA']

                             
    eventsdb = pd.DataFrame(db.queryDB(q), columns=column_list, dtype=object)
    eventsdb_converted = pd.DataFrame(columns=column_list2, dtype=object)
    
    bar = ChargingBar('Processing Events', max=len(eventsdb))
    for index in range(len(eventsdb)):
        eventid = int(eventsdb['recIDX'][index])
        eventtype = int()
        start_time_s = eventsdb['AbsEventStart'][index] / 1000.
        if index == 0:
            event_delay_s = start_time_s
        else:
            event_delay_s = (eventsdb['AbsEventStart'][index] - eventsdb['AbsEventStart'][index-1]) /1000.
        duration_us = eventsdb['ResTime'][index] * 1000.
        effective_baseline_pA = eventsdb['OpenChCurrent'][index]
        n_levels = eventsdb['NStates'][index] + 1
        rc_const1_us = eventsdb['RCConstant'][index][0] * 1000.
        
        max_blockage_pA = (1 - min(eventsdb['BlockDepth'][index])) * effective_baseline_pA
        relative_max_blockage = (1 - min(eventsdb['BlockDepth'][index]))
        max_blockage_duration_us = eventsdb['StateResTime'][index][eventsdb['BlockDepth'][index].index(min(eventsdb['BlockDepth'][index]))] * 1000.
        min_blockage_pA = (1 - max(eventsdb['BlockDepth'][index])) * effective_baseline_pA
        relative_min_blockage = (1 - max(eventsdb['BlockDepth'][index]))
        min_blockage_duration_us = eventsdb['StateResTime'][index][eventsdb['BlockDepth'][index].index(max(eventsdb['BlockDepth'][index]))] * 1000.
        
        timeseries = np.array(eventsdb['TimeSeries'][index])
        eventdelay = np.array(eventsdb['EventDelay'][index]) * 1000.
        currentstep = np.array(eventsdb['CurrentStep'][index])
        timescale = np.arange(len(timeseries)) * 1/4.16666666667
        eventfit = np.zeros_like(timeseries)
        for i in range(len(eventfit)):
            n = 1
            eventfit[i] = -effective_baseline_pA
            for j in range(len(eventdelay) - 1):
                if (timescale[i] > eventdelay[j]) and (timescale[i] < eventdelay[j+1]):
                    for k in range(n):
                        eventfit[i] = eventfit[i] - currentstep[k]
                    break
                else:
                    n += 1
        residual_pA = np.std(timeseries - eventfit)
        max_deviation_pA = max(abs(timeseries + effective_baseline_pA))
        baseline_before = timescale < eventdelay[0]
        baseline_after = timescale > eventdelay[-1]
        baseline_before_series = timeseries[baseline_before]
        baseline_after_series = timeseries[baseline_after]
        baseline_before_pA = -np.mean(baseline_before_series)
        baseline_after_pA = -np.mean(baseline_after_series)
        event = timeseries[~baseline_before & ~baseline_after]
        average_blockage_pA = effective_baseline_pA - np.mean(event)
        relative_average_blockage = average_blockage_pA / effective_baseline_pA
        stdev = []
        level_current = []
        level_duration = []
        level_current = np.append(level_current, baseline_before_pA)
        stdev = np.append(stdev, np.std(baseline_before_series))
        level_duration = np.append(level_duration, len(baseline_before)/4.16666666667)
        for level_index in range(len(eventdelay)-1):
            before_level = timescale < eventdelay[level_index]
            after_level = timescale > eventdelay[level_index+1]
            level = timeseries[~before_level & ~after_level]
            level_stdev = np.std(level)
            stdev = np.append(stdev, level_stdev)
            level_current = np.append(level_current, -np.mean(level))
            level_duration = np.append(level_duration, len(level)/4.16666666667)
        level_current = np.append(level_current, baseline_after_pA)
        stdev = np.append(stdev, np.std(baseline_after_series))
        blockages = [(1 - eventsdb['BlockDepth'][index][i]) * effective_baseline_pA for i in range(len(eventsdb['BlockDepth'][index]))]
        blockages = [baseline_before_pA - effective_baseline_pA] + blockages + [(baseline_after_pA - effective_baseline_pA)]
        
        level_duration = np.append(level_duration, len(baseline_after)/4.16666666667)
        level_current_pA = ''
        stdev_pA = ''
        blockages_pA =''
        level_duration_us = ''
        for i in range(len(level_current)):
            level_current_pA = level_current_pA + '%.16g;' %level_current[i]
            level_duration_us = level_duration_us + '%.16g;' %level_duration[i]
            blockages_pA = blockages_pA + '%.16g;' %blockages[i]
            stdev_pA = stdev_pA + '%.16g;' %stdev[i]
            
        level_current_pA = level_current_pA[:-1]
        level_duration_us = level_duration_us[:-1]
        blockages_pA = blockages_pA[:-1]
        stdev_pA = stdev_pA[:-1]
        
        area_pC = 0.
        for I in event:
            delta_t = 1/4.16666666667
            delta_A = I * delta_t
            area_pC = area_pC + delta_A

        column_dict_converted = {'id' : eventid,
                                 'type' : eventtype,
                                 'start_time_s' : start_time_s,
                                 'event_delay_s' : event_delay_s,
                                 'duration_us' : duration_us,
                                 'baseline_before_pA' : baseline_before_pA,
                                 'baseline_after_pA' : baseline_after_pA,
                                 'effective_baseline_pA' : effective_baseline_pA,
                                 'average_blockage_pA' : average_blockage_pA,
                                 'relative_average_blockage' : relative_average_blockage,
                                 'max_blockage_pA' : max_blockage_pA,
                                 'relative_max_blockage' : relative_max_blockage,
                                 'max_blockage_duration_us' : max_blockage_duration_us,
                                 'n_levels' : n_levels,
                                 'rc_const1_us' : rc_const1_us,
                                 'residual_pA' : residual_pA,
                                 'max_deviation_pA' : max_deviation_pA,
                                 'min_blockage_pA' : min_blockage_pA,
                                 'relative_min_blockage' : relative_min_blockage,
                                 'min_blockage_duration_us' : min_blockage_duration_us,
                                 'level_current_pA' : level_current_pA,
                                 'level_duration_us' : level_duration_us,
                                 'blockages_pA' : blockages_pA,
                                 'stdev_pA' : stdev_pA}
        
        eventtrace = pd.DataFrame(data=np.array([timescale, timeseries, eventfit]).T)
        eventfile = 'event_%08d.csv' %(eventid)
        event_file_name = events_directory_path + eventfile
        with open(event_file_name, 'wb'):
            eventtrace.to_csv(event_file_name, index=False, header=False)

        eventsdb_converted = eventsdb_converted.append(column_dict_converted, ignore_index=True)
        bar.next()

    bar.finish()
    file_name = os.path.basename(file_path_string)
    filename = directory_path + file_name[:-7] + '_converted.csv'
    with open(filename, 'wb'):
        eventsdb_converted.to_csv(filename, index=False)

def main():
    root=tk.Tk()
    root.withdraw()
    #file_path_string = 'F:\\Chimera Data\\20161222 - PK079-1\\eventMD-20170110-115345.sqlite'
    file_path_string = tkFileDialog.askopenfilename(initialdir='F:\\Chimera Data\\')
    directory_path = os.path.dirname(os.path.abspath(file_path_string))
    directory_path = directory_path + '\\' + file_name[:-7] + '\\'
    events_directory_path = directory_path + 'events\\'
    do_Stuff(file_path_string,events_directory_path,directory_path)
    

if __name__=="__main__":
    main()
