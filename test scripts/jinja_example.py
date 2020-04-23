from jinja2 import FileSystemLoader, Environment
import os


class CodeWriter:
    def __init__(self):
        self.input_variables = {}
        self.output_variables = {}
        self.commands = []
        temp = '../templates/'
        TEMPLATE_FILE = "template.py.j2"
        template_dir = os.path.join(os.path.dirname(__file__), temp)
        templateLoader = FileSystemLoader(searchpath=template_dir)
        templateEnv = Environment(loader=templateLoader)
        self.tm = templateEnv.get_template(TEMPLATE_FILE)

    def command_parser(self, commands):
        for level, line in enumerate(commands):
            cmd = line['code']
            for var in self.input_variables.keys():
                if var in cmd:
                    cmd = cmd.replace(var, '{' + var + '}')
            for var_saved_result in self.output_variables.keys():
                cmd = cmd.replace(var_saved_result, '{' + var_saved_result + '}')
            commands[level]['code'] = "f'" + cmd + "'"
        return commands

    def generate_code(self, instr_config, input_variables, permutate, commands, output_variables):
        """
        https://stackoverflow.com/a/45719723/3382269
        :param instr_config:
        :param input_variables:
        :param permutate:
        :param commands:
        :param output_variables:
        :return:
        """
        self.input_variables = input_variables
        self.output_variables = output_variables
        self.commands = self.command_parser(commands)

        OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '../output/output.py')
        self.tm.stream(instr_config=instr_config,
                       data=self.input_variables,
                       permutate=permutate,
                       commands=self.commands).dump(OUTPUT_FILE)


def main():
    input_variables = {'cur': [1, 2, 3, 4, 5], 'freq': [10, 20, 30, 40, 50], 'volt': [100, 200, 300, 400, 500]}
    output_variables = {'rslt': 2}
    permutate = True

    config = {'f5560A': {'ip_address': '129.196.136.130', 'port': '3490', 'gpib_address': '', 'mode': 'SOCKET'},
              'k34461A': {'ip_address': '10.205.92.67', 'port': '3490', 'gpib_address': '', 'mode': 'SOCKET'},
              'f8846A': {'ip_address': '10.205.92.248', 'port': '3490', 'gpib_address': '', 'mode': 'SOCKET'},
              'f5520A': {'ip_address': '', 'port': '', 'gpib_address': '6', 'mode': 'GPIB'}}

    commands = [{'choice': 'f5560A', 'code': 'out curA; out freqHz', 'variable': ''},
                {'choice': 'f5560A', 'code': 'oper', 'variable': ''},
                {'choice': 'f8846A', 'code': 'READ?', 'variable': 'rslt'},
                {'choice': 'f5560A', 'code': 'STBY', 'variable': ''}]

    config_in_commands = {key: config[key] for cmd in commands if (key := cmd['choice']) in config.keys()}

    CW = CodeWriter()
    CW.generate_code(instr_config=config_in_commands,
                     input_variables=input_variables,
                     output_variables=output_variables,
                     permutate=permutate,
                     commands=commands)


if __name__ == "__main__":
    main()
