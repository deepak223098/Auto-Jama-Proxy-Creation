"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Dialog prompts for arguments
"""
import os
import Tkinter as tk
import tkFileDialog
import tkMessageBox
import tkSimpleDialog

from common.utils import files


__version__ = '$Rev: 254921 $'


class InvalidArgumentException(Exception):
    """Raised when an argument value is invalid"""
    pass


class MissingArgumentException(InvalidArgumentException):
    """Raised when an argument is not given by the user"""
    pass


def dir_path(args, arg_name, required=True, must_exist=True, **kwargs):
    """
    Prompts the user for a directory path if one was not given.

    :param args: arguments supplied by the user
    :type  args: namespace
    :param arg_name: name of the argument to prompt for
    :type  arg_name: basestring
    :param required: whether the argument is required
    :type  required: bool
    :param must_exist: whether the directory path must already exist
    :type  must_exist: bool
    :return: directory path given by the user
    :rtype: basestring
    """
    path = getattr(args, arg_name)
    if path is None:
        tk.Tk().withdraw()
        path = tkFileDialog.askdirectory(**kwargs)

        if not path:
            if not required:
                return None

            raise MissingArgumentException(
                'Missing directory argument "{}"'.format(arg_name))

    path = files.real(path)
    if must_exist and not os.path.isdir(path):
        raise InvalidArgumentException(
            'Directory does not exist at "{}"'.format(path))

    return path


def file_path(args, arg_name, required=True, must_exist=True, **kwargs):
    """
    Prompts the user for a file path if one was not given.

    :param args: arguments supplied by the user
    :type  args: namespace
    :param arg_name: name of the argument to prompt for
    :type  arg_name: basestring
    :param required: whether the argument is required
    :type  required: bool
    :param must_exist: whether the file path must already exist
    :type  must_exist: bool
    :return: file path given by the user
    :rtype: basestring
    """
    path = getattr(args, arg_name)
    if path is None:
        tk.Tk().withdraw()
        if must_exist:
            path = tkFileDialog.askopenfilename(**kwargs)

        else:
            path = tkFileDialog.asksaveasfilename(**kwargs)

        if not path:
            if not required:
                return None

            raise MissingArgumentException(
                'Missing file argument "{}"'.format(arg_name))

    path = files.real(path)
    if must_exist and not os.path.isfile(path):
        raise InvalidArgumentException(
            'File does not exist at "{}"'.format(path))

    return path


def file_paths(
        args, arg_name, required=True, must_exist=True, recursive=False,
        **kwargs):
    """
    Prompts the user for a directory path if one was not given.

    :param args: arguments supplied by the user
    :type  args: namespace
    :param arg_name: name of the argument to prompt for
    :type  arg_name: basestring
    :param required: whether the argument is required
    :type  required: bool
    :param must_exist: whether the file paths must already exist
    :type  must_exist: bool
    :param recursive: whether to search directories recursively
    :type  recursive: bool
    :return: file paths given by the user
    :rtype: list[basestring]
    """
    paths = getattr(args, arg_name)
    if paths is None:
        tk.Tk().withdraw()
        paths = tkFileDialog.askdirectory(**kwargs)

        if not paths:
            if not required:
                return None

            raise MissingArgumentException(
                'Missing directory argument "{}"'.format(arg_name))

    if not isinstance(paths, list):
        paths = [paths]

    arg = []
    paths = [files.real(path) for path in paths]
    for path in paths:
        if os.path.isdir(path):
            if recursive:
                arg.extend([
                    os.path.join(dirpath, f)
                    for dirpath, _, fs in os.walk(path)
                    for f in fs])

                continue

            arg.extend([os.path.join(path, f) for f in os.listdir(path)])
            continue

        if must_exist and not os.path.isfile(path):
            raise InvalidArgumentException(
                'File does not exist at "{}"'.format(path))

        arg.append(path)

    return arg


def string(args, arg_name, required=True, **kwargs):
    """
    Prompts the user for a string if one was not given.

    :param args: arguments supplied by the user
    :type  args: namespace
    :param arg_name: name of the argument to prompt for
    :type  arg_name: basestring
    :param required: whether the argument is required
    :type  required: bool
    :return: string given by the user
    :rtype: basestring
    """
    arg = getattr(args, arg_name)
    if arg is None:
        tk.Tk().withdraw()
        arg = tkSimpleDialog.askstring(**kwargs)

        if not arg:
            if not required:
                return None

            raise MissingArgumentException(
                'Missing string argument "{}"'.format(arg_name))

    return arg


def ok(args, arg_name, **kwargs):
    """
    Prompts the user for confirmation.

    :param args: arguments supplied by the user
    :type  args: namespace
    :param arg_name: name of the argument to prompt for
    :type  arg_name: basestring
    :return: confirmation given by the user
    :rtype: bool
    """
    arg = getattr(args, arg_name)
    if arg is None:
        tk.Tk().withdraw()
        arg = tkMessageBox.askokcancel(**kwargs)

    return arg
