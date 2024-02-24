
import argparse
import ast
import logging
import os
from logging import Logger
import re
from lemniscat.core.contract.engine_contract import PluginCore
from lemniscat.core.model.models import Meta, TaskResult, VariableValue
from lemniscat.core.util.helpers import FileSystem, LogUtil

from lemniscat.plugin.filetransform.filetransform import FileTransform

_REGEX_CAPTURE_VARIABLE = r"(?:\${{(?P<var>[^}]+)}})"

class Action(PluginCore):

    def __init__(self, logger: Logger) -> None:
        super().__init__(logger)
        plugin_def_path = os.path.abspath(os.path.dirname(__file__)) + '/plugin.yaml'
        manifest_data = FileSystem.load_configuration_path(plugin_def_path)
        self.meta = Meta(
            name=manifest_data['name'],
            description=manifest_data['description'],
            version=manifest_data['version']
        )

    def __interpret(self, parameterValue: str, variables: dict) -> str:
        isSensible = False
        if(parameterValue is None):
            return None
        if(isinstance(parameterValue, str)):
            matches = re.findall(_REGEX_CAPTURE_VARIABLE, parameterValue)
            if(len(matches) > 0):
                for match in matches:
                    var = str.strip(match)
                    if(var in variables):
                        parameterValue = parameterValue.replace(f'${{{{{match}}}}}', variables[var].value)
                        if(variables[var].sensitive):
                            isSensible = True
                        self._logger.debug(f"Interpreting variable: {var} -> {variables[var]}")
                    else:
                        parameterValue = parameterValue.replace(f'${{{{{match}}}}}', "")
                        self._logger.debug(f"Variable not found: {var}. Replaced by empty string.")
        return VariableValue(parameterValue, isSensible) 

    def __run_filetransform(self, parameters: dict = {}, variables: dict = {}) -> TaskResult:
        # launch powershell command
        filetransform = FileTransform()
        if(parameters.keys().__contains__('folderOutPath') == False):
            parameters['folderOutPath'] = parameters['folderPath']
                 
        result = filetransform.run(self.__interpret(parameters['folderPath'], variables).value, self.__interpret(parameters['targetFiles'], variables).value, self.__interpret(parameters['fileType'], variables).value, self.__interpret(parameters['folderOutPath'], variables).value, variables)
                
        if(result[0] != 0):
            return TaskResult(
                name=f'FileTransform run',
                status='Failed',
                errors=result[2])
        else:
            return TaskResult(
                name='FileTransform run',
                status='Completed',
                errors=[0x0000]
        )
        

    def invoke(self, parameters: dict = {}, variables: dict = {}) -> TaskResult:
        self._logger.debug(f'Transform file for {parameters["fileType"]} -> {self.meta}')
        task = self.__run_filetransform(parameters, variables)
        return task
    
    def test_logger(self) -> None:
        self._logger.debug('Debug message')
        self._logger.info('Info message')
        self._logger.warning('Warning message')
        self._logger.error('Error message')
        self._logger.critical('Critical message')

def __init_cli() -> argparse:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p', '--parameters', required=True, 
        help="""(Required) Supply a dictionary of parameters which should be used. The default is {}
        """
    )
    parser.add_argument(
        '-v', '--variables', required=True, help="""(Optional) Supply a dictionary of variables which should be used. The default is {}
        """
    )                
    return parser
        
if __name__ == "__main__":
    logger = LogUtil.create()
    action = Action(logger)
    __cli_args = __init_cli().parse_args()   
    variables = {}   
    vars = ast.literal_eval(__cli_args.variables)
    for key in vars:
        variables[key] = VariableValue(vars[key])
    action.invoke(ast.literal_eval(__cli_args.parameters), variables)