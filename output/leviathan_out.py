from pathlib import Path
import numpy as np
import csv
import sys
import time
import pyvisa

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
        self.mode = self.instr_info['mode']

        self.INSTR = None
        self.address = None
        self.port = None

        self.rm = pyvisa.ResourceManager()
        self.timeout = 3000  # 1 (60e3) minute timeout

        # TODO - verify this works as intended... Otherwise leave INSTR lines commented
        # if mode is SOCKET:
        if self.mode == 'SOCKET':
            self.address = self.instr_info['ip_address']
            self.port = self.instr_info['port']
            # self.INSTR = self.rm.open_resource(f'TCPIP::{self.address}::{self.port}::SOCKET')
            # self.INSTR.read_termination = '\n'

        # if mode is GPIB:
        elif self.mode == 'GPIB':
            self.address = self.instr_info['gpib_address']
            # self.INSTR = self.rm.open_resource(f'GPIB0::{self.address}::INSTR')

        # if mode is INSTR:
        elif self.mode == 'INSTR':
            self.address = self.instr_info['ip_address']
            # self.INSTR = self.rm.open_resource(f'TCPIP::{self.address}::INSTR')
            # self.INSTR.read_termination = '\n'

        # if mode is SERIAL:
        elif self.mode == 'SERIAL':
            self.address = self.instr_info['ip_address']
            # self.INSTR = self.rm.open_resource(f'{self.address}')
            # self.INSTR.read_termination = '\n'

        # TODO - http://lampx.tugraz.at/~hadley/num/ch9/python/9.2.php
        # if mode is SERIAL:
        elif self.mode == 'USB':
            self.address = self.instr_info['ip_address']
            # self.INSTR = self.rm.open_resource(f'{self.address}')
            # self.INSTR.read_termination = '\n'

        # if mode is NIGHTHAWK:
        elif self.mode == 'NIGHTHAWK':
            self.address = self.instr_info['ip_address']
            self.port = self.instr_info['port']
            # self.INSTR = self.rm.open_resource(f'TCPIP::{self.address}::{self.port}::SOCKET')
            # self.INSTR.read_termination = '>'
            # self.INSTR.read()
        else:
            print('Failed to connect.')

        # TODO - Leave commented until after verifying visa communication works
        # self.INSTR.timeout = self.timeout

    def info(self):
        print(self.instr_info)

    def identify(self):
        print()
        try:
            identity = self.query('*IDN?')
            print(identity + '\n')
        # TODO - do not use bare except. how to find visa?
        # except visa.VisaIOError:
        except:
            print('Failed to connect to address: ' + self.address)

    def write(self, cmd):
        self.INSTR.write(f'{cmd}')

    def read(self):
        response = None
        if self.mode == 'NIGHTHAWK':
            response = (self.INSTR.read().split("\r")[0].lstrip())
        else:
            response = self.INSTR.read()
        return response

    def query(self, cmd):
        response = None
        if self.mode == 'NIGHTHAWK':
            response = (self.INSTR.query(f'{cmd}')).split("\r")[0].lstrip()
        else:
            response = (self.INSTR.query(f'{cmd}'))
        return response

    def close(self):
        self.INSTR.close()


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
        k34461A_id = {'ip_address': '10.205.92.67', 'port': '3490', 'gpib_address': '', 'mode': 'SOCKET'}

        # ESTABLISH COMMUNICATION WITH INSTRUMENTS ---------------------------------------------------------------------
        self.f5560A = Visa(f5560A_id)
        self.f5520A = Visa(f5520A_id)
        self.f8846A = Visa(f8846A_id)
        self.k34461A = Visa(k34461A_id)

    # RUN FUNCTION -----------------------------------------------------------------------------------------------------
    def run(self):
        _cur = [0, 1.20E-03, 4.00E-03, 6.00E-03, 9.00E-03, 1.19E-02, 1.2, 11.9, 12, 119, 120, 1000]
        _freq = [0, 50, 70, 100, 200, 500]
        _phase = [0]

        # Note that if x and y are not the same length, zip will truncate to the shortest list.
        for cur, freq, phase in zip(_cur, _freq, _phase):
            self.f5560A.write(f'out {cur}A; out {freq}Hz')
            self.f5560A.write(f'oper')
            self.f5520A.write(f'SYST:REM')
            self.f8846A.write(f'CONF:VOLT:AC')
            rslt, *_ = average_reading(self.f8846A, f'READ?')
            new = rslt + 1
            self.k34461A.write(f'CONF:AC:{new}')
            print(phase)


def main():
    T = Test()
    T.run()


if __name__ == "__main__":
    main()
