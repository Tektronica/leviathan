import pyvisa
from pyvisa import VisaIOError  # Here is the error handle to use...
import yaml
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
        instr = {'instr': item['instr'], 'mode': item['mode'], 'ip_address': item['ip_address'], 'port': item['port']}
    elif item['mode'] == 'GPIB':
        instr = {'instr': item['instr'], 'mode': item['mode'], 'gpib_address': item['gpib_address']}
    else:
        instr = {'instr': item['instr'], 'mode': item['mode'], 'ip_address': item['ip_address'], 'port': item['port']}
    return Client(instr)


class Client:
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


def initialize(size):
    instr_list = [None for m in range(size)]
    config_dict = ReadConfig()
    return tuple(CreateInstance(config_dict[i]) for i in range(size))
