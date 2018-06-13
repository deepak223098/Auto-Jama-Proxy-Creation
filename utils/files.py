"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Utility functions for processing file system paths
"""
import errno
import os
import re
import shutil
import subprocess
import urllib
import webbrowser

import symlink
from constants import BROWSERS


__version__ = '$Rev: 254955 $'

# matches a root (drive letter) path (except C: or S:)
RE_DRIVE = re.compile(r'[A-BD-RTV-Z]:\\')


class PathNotFoundException(Exception):
    """Exception for when a local path does not exist"""
    pass


def _format_drive(drive):
    """
    Formats the given path as a drive.

    :param drive: path to be reformatted
    :type  drive: basestring
    :return: drive version of the path
    :rtype: basestring
    """
    if drive.endswith(os.path.sep):
        drive = drive[:-1]

    if drive.endswith(':'):
        drive = drive[:-1]

    return '{}:\\'.format(drive.upper())


def real(path, cwd=None, preserve_symlinks=True):
    """
    Converts a path to its normal, absolute equivalent.

    :param path: path to be converted
    :type  path: basestring
    :param cwd: current working directory used when converting to absolute paths
    :type  cwd: basestring
    :param preserve_symlinks: whether to expand symlinks
    :type  preserve_symlinks: bool
    :return: normal, absolute version of the path
    :rtype: basestring
    """
    path = os.path.expanduser(path)
    old_cwd = os.getcwd()
    if cwd is not None:
        os.chdir(cwd)

    if not preserve_symlinks:
        path = symlink.realpath(path)

    path = os.path.abspath(os.path.realpath(path))
    if cwd is not None:
        os.chdir(old_cwd)

    return path


def real_directory(dirpath, cwd=None):
    """
    Validates an existing directory path and converts it to its normal, absolute
    equivalent.

    :param dirpath: path to a directory
    :type  dirpath: basestring
    :param cwd: current working directory used when converting to absolute paths
    :type  cwd: basestring
    :return: normal, absolute version of the path
    :rtype: basestring
    """
    if not os.path.isdir(dirpath):
        # try interpreting the directory as a drive letter
        drive = _format_drive(dirpath)
        if not os.path.isdir(drive):
            raise PathNotFoundException(
                'Could not find a directory at "{}".'.format(dirpath))

        dirpath = drive

    return real(dirpath, cwd)


def real_file(filepath, cwd=None):
    """
    Validates an existing file path and converts it to its normal, absolute
    equivalent.

    :param filepath: path to a file
    :type  filepath: basestring
    :param cwd: current working directory used when converting to absolute paths
    :type  cwd: basestring
    :return: normal, absolute version of the path
    :rtype: basestring
    """
    if not os.path.isfile(filepath):
        raise PathNotFoundException(
            'Could not find a file at "{}".'.format(filepath))

    return real(filepath, cwd)


def real_drive(drive):
    """
    Validates an existing drive path and converts it to its normal, absolute
    equivalent.

    :param drive: path to a drive
    :type  drive: basestring
    :return: normal, absolute version of the path
    :rtype: basestring
    """
    drive = _format_drive(drive)
    if not RE_DRIVE.match(drive):
        raise PathNotFoundException(
            'The given drive is not valid: "{}".'.format(drive))

    # remove the trailing '\'
    return real(drive[:-1])


def filename(filepath, url=False):
    """
    Gets the name of a file without the file extension.

    :param filepath: path to a file
    :type  filepath: basestring
    :param url: whether the path is a URL instead of a local file
    :type  url: bool
    :return: name of the file without the extension
    :rtype: basestring
    """
    if url:
        return filepath.rsplit('/', 1)[-1].rsplit('.', 1)[0]

    return os.path.split(filepath)[1].rsplit('.', 1)[0]


def rmdir(path):
    """
    Removes the directory tree under the specified path.

    :param path: path to a directory
    :type  path: basestring
    """
    if os.path.isdir(path):
        shutil.rmtree(path)


def mkdir(path, delete=False):
    """
    Creates a directory tree to the specified path.

    :param path: path to a directory
    :type  path: basestring
    :param delete: whether the existing directory should be deleted
    :type  delete: bool
    """
    if delete:
        rmdir(path)

    try:
        os.makedirs(path)

    except OSError as e:
        if e.errno != errno.EEXIST or not os.path.isdir(path):
            raise e


def open_dir(path):
    """
    Opens a directory in the Windows explorer.

    :param path: path to the directory
    :type  path: basestring
    """
    subprocess.Popen(
        'explorer "{}"'.format(path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)


def open_dir_func(path):
    """
    Creates a function to open a directory in the Windows explorer.

    :param path: path to the directory
    :type  path: basestring
    :return: function to open the directory
    :rtype: callable
    """
    return lambda: open_dir(path)


def open_webpage(url, local=False):
    """
    Opens a webpage in the preferred browser.

    :param url: URL to the webpage
    :type  url: basestring
    :param local: whether the URL is a local file path
    :type  local: bool
    """
    if local:
        url = 'file:///{}'.format(urllib.pathname2url(os.path.abspath(url)))

    for browser in BROWSERS:
        if os.path.isfile(browser):
            subprocess.Popen(
                '"{bin}" "{url}"'.format(bin=browser, url=url),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

            break

    else:
        webbrowser.open(url)


def open_webpage_func(url, local=False):
    """
    Creates a function to open a webpage in the preferred browser.

    :param url: URL to the webpage
    :type  url: basestring
    :param local: whether the URL is a local file path
    :type  local: bool
    :return: function to open the webpage
    :rtype: callable
    """
    return lambda: open_webpage(url, local=local)
