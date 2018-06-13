"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Utility functions for processing dictionaries
"""
import copy


__version__ = '$Rev: 251774 $'


def dict_update(original, update):
    """
    Merges two dictionaries, with preference for the values from the "update"
    dictionary when the associated keys match.  Recursively merges values if
    they are both dictionaries.
    
    :param original: base dictionary
    :type  original: dict
    :param update: dictionary with preferred values
    :type  update: dict
    """
    result = copy.deepcopy(original)
    for k, v in update.iteritems():
        if not isinstance(v, dict) or not isinstance(original.get(k), dict):
            result[k] = update[k]
            continue

        result[k] = dict_update(original.get(k, {}), v)

    return result


def dict_get_first(d, keys):
    """
    Gets the value of the first key that exists in the dictionary.

    :param d: dictionary to get from
    :type  d: dict
    :param keys: keys to get
    :type  keys: list
    """
    for key in keys:
        if key in d:
            return key, d[key]

    return None, None
