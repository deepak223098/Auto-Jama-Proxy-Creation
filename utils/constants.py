"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Constant values used throughout the common utils
"""
import os


__version__ = '$Rev: 251774 $'

# path to temp directory
TEMP_DIR = 'C:\\Temp'

# subdirectories expected under a test directory
TEST_SUBDIRS = (
    '/log',
    '/logs',
    '/test_case',
    '/test_cases',
    '/test_procedure',
    '/test_procedures',
    '/vectorcast_environment',
    '/host',
    '/target')

# path to browsers used to open report files
BROWSERS = (
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe')

# path to be used if svnversion.exe not found on PATH
DEFAULT_SVNVERSION = 'C:\\Program Files\\TortoiseSVN\\bin\\svnversion.exe'

# path to the common directory
COMMON_DIR = os.path.dirname(os.path.dirname(__file__))

# path to the resources directory
RESOURCES_DIR = os.path.join(COMMON_DIR, 'resources')

# path to the Jama parser binary
JAMA_PARSER_BIN = os.path.join(
    COMMON_DIR, 'jama_report_to_json', 'jama_report_to_json.exe')
