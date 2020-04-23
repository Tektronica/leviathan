import pyunivisa
import csv
import sys
import time
import numpy as np


# FOLDER SETUP ---------------------------------------------------------------------------------------------------------
Path('results').mkdir(parents=True, exist_ok=True)
filename = 'test'
path_to_file = f'results\\{filename}_{time.strftime("%Y%m%d_%H%M")}'


# ESTABLISH COMMUNICATION TO INSTRUMENTS -------------------------------------------------------------------------------
f5560A_ip = '129.196.136.130'
k34461A_ip = '10.205.92.67'
f8846A_ip = '10.205.92.248'
f5790A_ip = '6'  # this is its GPIB address


# FOLDER SETUP ---------------------------------------------------------------------------------------------------------
Path('results').mkdir(parents=True, exist_ok=True)
filename = 'test'
path_to_file = f'results\\{filename}_{time.strftime("%Y%m%d_%H%M")}'


# ESTABLISH COMMUNICATION TO INSTRUMENTS -------------------------------------------------------------------------------
f5560A_ip = '129.196.136.130'
k34461A_ip = '10.205.92.67'
f8846A_ip = '10.205.92.248'
f5790A_ip = '6'  # this is its GPIB address


# FILE PATH TO SAVE CSV ------------------------------------------------------------------------------------------------
csv_path = 'output\\csv\\'
fig_path = 'output\\figures\\'


# FUNCTION DEFINITIONS -------------------------------------------------------------------------------------------------
def average_reading(instrument, cmd):
	time.sleep(2)
    for idx in range(samples):
        data.append(float(instrument.read(cmd).split(',')[0]))
        time.sleep(0.20)
    array = np.asarray(data)
    mean = array.mean()
    std = np.sqrt(np.mean(abs(array - mean) ** 2))
    return mean, std


# RUN FUNCTION ---------------------------------------------------------------------------------------------------------
def run():
    _cur = [1, 2, 3, 4, 5]
    _freq = [10, 20, 30, 40, 50]
    _volt = [100, 200, 300, 400, 500]

    # Note that if x and y are not the same length, zip will truncate to the shortest list.
    for cur in _cur:
        for freq in _freq:
            for volt in _volt:
                f5560A.write(f'out {cur}A; out {freq}Hz')
                rslt = average_reading(f8846A, f'READ?')
                f5560A.write(f'STBY')
    	


if __name__ == "__main__":
	run()
