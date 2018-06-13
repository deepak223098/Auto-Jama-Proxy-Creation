"""
+------------------------------------------------------------------------------+
|                     Copyright 2016-2017 Rockwell Collins                     |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Utility functions for validating items with the voluptuous library
"""
import voluptuous as vol

import files
import strings


__version__ = '$Rev: 244668 $'

# validates the value is a boolean string and coerces it to a bool
boolstr = vol.All(
    vol.Lower, vol.Any('true', 'false'), lambda val: val == 'true')

# coerces the values to a "plain" string
plainstr = lambda x: strings.plainstr(x)

# coerces the keys of a dictionary value to "plain" strings
plainstr_dict = lambda x: {
    strings.plainstr(k): strings.plainstr(v) for k, v in x.iteritems()}


def filepath(cwd=None):
    """
    Validates the value is an existing file path and coerces it to a normal,
    absolute path.

    :param cwd: current working directory used when converting to absolute paths
    :type  cwd: basestring
    :return: validation function
    :rtype: callable
    """
    def f(val):
        if val is None:
            return None

        return files.real(str(val), cwd=cwd)

    return f
