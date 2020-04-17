import yaml
import pyunivisa
import os


def ReadConfig():
    if os.path.exists("instrument_config.yaml"):
        with open("instrument_config.yaml", 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
    else:
        pass


def CreateInstance(item):
    if item['mode'] == 'Ethernet':
        instr = {'name': item['name'], 'mode': item['mode'], 'ip_address': item['ip_address'], 'port': item['port']}
    elif item['mode'] == 'GPIB':
        instr = {'name': item['name'], 'mode': item['mode'], 'gpib_address': item['gpib_address']}
    else:
        instr = {'name': item['name'], 'mode': item['mode'], 'ip_address': item['ip_address'], 'port': item['port']}
    return Visa(instr)


# This is the pyunivisa import
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

    def identify(self):
        if self.mode == 'Ethernet':
            print(f'[*IDN?] TCPIP::{self.address}::{self.port}::SOCKET')
        elif self.mode == 'GPIB':
            print(f'[*IDN?] GPIB0::{self.address}::INSTR')

    def setup_instrument(self):
        if self.mode == 'Ethernet':
            self.a = pyunivisa.Client(address=self.address, port=self.port, communication_type='SOCKET')
        elif self.mode == 'GPIB':
            self.a = pyunivisa.Client(address=self.address, communication_type='GPIB')


def initialize(size):
    instr_list = [None for m in range(size)]
    config_dict = ReadConfig()
    return tuple(CreateInstance(config_dict[i]) for i in range(size))
