# -*- coding: utf-8 -*-
# above is for compatibility of python2.7.11

import logging
import os
import subprocess, sys   
from lemniscat.core.util.helpers import LogUtil
import re

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.setLoggerClass(LogUtil)
log = logging.getLogger(__name__.replace('lemniscat.', ''))

class FileTransform:
    def __init__(self):
        pass
    
    # parse yaml file to dict
    @staticmethod
    def parseYamlFile(filePath) -> dict:
        import yaml
        with open(filePath, 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                log.error(exc)
                return None
            
    # parse json file to dict
    @staticmethod
    def parseJsonFile(filePath) -> dict:
        import json
        with open(filePath, 'r') as stream:
            try:
                return json.load(stream)
            except json.JSONDecodeError as exc:
                log.error(exc)
                return None
            
    # save dict to yaml file
    @staticmethod
    def saveYamlFile(filePath, data: dict) -> None:
        import yaml
        with open(filePath, 'w') as stream:
            try:
                yaml.dump(data, stream, indent=4)
            except yaml.YAMLError as exc:
                log.error(exc)

    # save dict to json file
    @staticmethod
    def saveJsonFile(filePath, data: dict) -> None:
        import json
        with open(filePath, 'w') as stream:
            try:
                json.dump(data, stream, indent=4)
            except json.JSONDecodeError as exc:
                log.error(exc)
                
    # get files path match pattern in directory
    @staticmethod
    def getFilesPathMatchPattern(directory, pattern) -> list:
        import glob
        return glob.glob(f'{directory}/{pattern}')
    
    @staticmethod
    def getFileNameFromPath(filePath) -> str:
        return os.path.basename(filePath)

    # replace variable in dict
    @staticmethod
    def replaceVariable(data: dict, key: str, value: object, prefix: str = '') -> dict:
        for k, v in data.items():
            if(f'{prefix}{k}'.casefold() == key.casefold()):
                log.info(f'Found {key}. Replace {key}...')
                data[k] = value
            else:
                if(isinstance(v, dict) and key.casefold().startswith(f'{prefix}{k}'.casefold()) ):
                    data[k] = FileTransform.replaceVariable(v.copy(), key, value, f'{prefix}{k}.')
        return data

    def run(self, folderPath: str, targetFiles: str, fileType: str, folderOutPath: str, variables: dict = {}) -> None:
        # get all files path match pattern
        files = self.getFilesPathMatchPattern(folderPath, targetFiles)
        # loop files
        for file in files:
            # parse file
            if(fileType == 'yaml'):
                data = self.parseYamlFile(file)
            elif(fileType == 'json'):
                data = self.parseJsonFile(file)
            else:
                log.error('File type not supported')
                return 1, '','File type not supported'
            # replace variables
            for key, value in variables.items():
                data = self.replaceVariable(data, key, value.value)
            # save file
            outfile = f'{folderOutPath}/{self.getFileNameFromPath(file)}'
            if(fileType == 'yaml'):
                self.saveYamlFile(outfile, data)
            elif(fileType == 'json'):
                self.saveJsonFile(outfile, data)
            else:
                log.error('File type not supported')
                return 1, '','File type not supported'
        return 0, '',''