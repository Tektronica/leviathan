from pathlib import Path
import numpy as np
import pyunivisa
import csv
import sys
import time

# FILE PATH TO SAVE CSV ------------------------------------------------------------------------------------------------
csv_path = 'output\\csv\\'
fig_path = 'output\\figures\\'

# FOLDER SETUP ---------------------------------------------------------------------------------------------------------
Path('results').mkdir(parents=True, exist_ok=True)
filename = 'test'
path_to_file = f'results\\{filename}_{time.strftime("%Y%m%d_%H%M")}'


class Visa:
    def __init__(self, _instr_info):
        self.instr_info = _instr_info
        self.instr = None   # visa isntance of instrument

        self.mode = self.instr_info['mode']
        # if mode is Ethernet:
        if self.mode == 'Ethernet':
            self.address = self.instr_info['ip_address']
            self.port = self.instr_info['port']

        # if mode is GPIB:
        elif self.mode == 'GPIB':
            self.address = self.instr_info['gpib_address']

        else:
            pass

    def info(self):
        print(self.instr_info)

    def idn(self):
        print(self.read('*IDN?'))

    def setup_instrument(self):
        if self.mode == 'Ethernet':
            self.a = pyunivisa.Client(address=self.address, port=self.port, communication_type='SOCKET')
        elif self.mode == 'GPIB':
            self.a = pyunivisa.Client(address=self.address, communication_type='GPIB')


# FUNCTION DEFINITIONS -------------------------------------------------------------------------------------------------
def CreateInstance(item):
    if item['mode'] == 'Ethernet':
        instr = {'name': item['name'], 'mode': item['mode'], 'ip_address': item['ip_address'], 'port': item['port']}
    elif item['mode'] == 'GPIB':
        instr = {'name': item['name'], 'mode': item['mode'], 'gpib_address': item['gpib_address']}
    else:
        instr = {'name': item['name'], 'mode': item['mode'], 'ip_address': item['ip_address'], 'port': item['port']}
    return Visa(instr)


def average_reading(instrument, cmd, samples=10):
    data = []
    time.sleep(2)
    for idx in range(samples):
        data.append(float(instrument.read(cmd).split(',')[0]))
        time.sleep(0.20)
    array = np.asarray(data)
    mean = array.mean()
    std = np.sqrt(np.mean(abs(array - mean) ** 2))
    return mean, std


class Test:
    def __init__(self):
        # CONFIGURED INSTRUMENTS ---------------------------------------------------------------------------------------
        f5560A_id = {'ip_address': '129.196.136.130', 'port': '3490', 'gpib_address': '', 'mode': 'SOCKET'}
        f5520A_id = {'ip_address': '', 'port': '', 'gpib_address': '6', 'mode': 'GPIB'}
        f8846A_id = {'ip_address': '10.205.92.248', 'port': '3490', 'gpib_address': '', 'mode': 'SOCKET'}

        # ESTABLISH COMMUNICATION WITH INSTRUMENTS ---------------------------------------------------------------------
        self.f5560A = CreateInstance(f5560A_id)
        self.f5520A = CreateInstance(f5520A_id)
        self.f8846A = CreateInstance(f8846A_id)

    # RUN FUNCTION -----------------------------------------------------------------------------------------------------
    def run(self):
        _cur = 0, 1.20E-03, 4.00E-03, 6.00E-03, 9.00E-03, 1.19E-02, 1.2, 11.9, 12, 119, 120, 1000
        _freq = 0, 50, 70, 100, 200, 500
                
        for cur in _cur:
            for freq in _freq:
                self.f5560A.write(f'out {cur}A; out {freq}Hz')
                self.f5560A.write(f'oper')
                self.f5520A.write(f'SYST:REM')
                self.f8846A.write(f'CONF:VOLT:AC')
                rslt = average_reading(self.f8846A, f'READ?')
                new = average_reading(self., f'{rslt}+1')
        	

def main():
    T = Test()
    T.run()


if __name__ == "__main__":
    main()
