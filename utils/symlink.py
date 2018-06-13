"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Utility functions for interfacing with Windows symlinks

Implementation from
https://stackoverflow.com/questions/1143260/create-ntfs-junction-point-in-python
"""
import os

import win32file
from winioctlcon import FSCTL_GET_REPARSE_POINT


__version__ = '$Rev: 251582 $'
__all__ = ['islink', 'readlink']


FILE_ATTRIBUTE_REPARSE_POINT = 1024

REPARSE_FOLDER = (
    win32file.FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT)

SYMBOLIC_LINK = 'symbolic'
MOUNTPOINT = 'mountpoint'
GENERIC = 'generic'


def mklink(fpath, target):
    """
    Creates a symlink.

    :param fpath: symlinkfile path to create
    :type  fpath: basestring
    :param target: path to link to
    :type  target: basestring
    :return:
    """
    win32file.CreateSymbolicLink(
        SymlinkFileName=fpath,
        TargetFileName=target,
        Flags=(1 if os.path.isdir(target) else 0))


def islink(fpath):
    """
    Determines whether a file path points to a symlink.

    :param fpath: file path to evaluate
    :type  fpath: basestring
    :return: whether the path points to a symlink
    :rtype: bool
    """
    return bool(win32file.GetFileAttributes(fpath) & REPARSE_FOLDER)


def parse_reparse_buffer(original, reparse_type=SYMBOLIC_LINK):
    """
    Parses a buffer using magic.  Output mimics the structure below.

    typedef struct _REPARSE_DATA_BUFFER {
        ULONG  ReparseTag;
        USHORT ReparseDataLength;
        USHORT Reserved;
        union {
            struct {
                USHORT SubstituteNameOffset;
                USHORT SubstituteNameLength;
                USHORT PrintNameOffset;
                USHORT PrintNameLength;
                ULONG Flags;
                WCHAR PathBuffer[1];
            } SymbolicLinkReparseBuffer;
            struct {
                USHORT SubstituteNameOffset;
                USHORT SubstituteNameLength;
                USHORT PrintNameOffset;
                USHORT PrintNameLength;
                WCHAR PathBuffer[1];
            } MountPointReparseBuffer;
            struct {
                UCHAR  DataBuffer[1];
            } GenericReparseBuffer;
        } DUMMYUNIONNAME;
    } REPARSE_DATA_BUFFER, *PREPARSE_DATA_BUFFER;
    """
    # size of our data types
    SZULONG = 4  # sizeof(ULONG)
    SZUSHORT = 2  # sizeof(USHORT)

    # our structure
    _buffer = {
        'tag': original[:SZULONG],
        'data_length': original[SZULONG:SZUSHORT],
        'reserved': original[SZULONG+SZUSHORT:SZUSHORT],
        SYMBOLIC_LINK: {
            'substitute_name_offset': SZUSHORT,
            'substitute_name_length': SZUSHORT,
            'print_name_offset': SZUSHORT,
            'print_name_length': SZUSHORT,
            'flags': SZULONG,
            'buffer': u'',
            'pkeys': [
                'substitute_name_offset',
                'substitute_name_length',
                'print_name_offset',
                'print_name_length',
                'flags',
            ]
        },
        MOUNTPOINT: {
            'substitute_name_offset': SZUSHORT,
            'substitute_name_length': SZUSHORT,
            'print_name_offset': SZUSHORT,
            'print_name_length': SZUSHORT,
            'buffer': u'',
            'pkeys': [
                'substitute_name_offset',
                'substitute_name_length',
                'print_name_offset',
                'print_name_length',
            ]
        },
        GENERIC: {
            'pkeys': [],
            'buffer': ''
        }
    }

    original = original[8:]

    # parsing
    k = reparse_type
    for c in _buffer[k]['pkeys']:
        if type(_buffer[k][c]) != int:
            continue

        sz = _buffer[k][c]
        _bytes = original[:sz]
        _buffer[k][c] = 0
        for b in _bytes:
            n = ord(b)
            if n:
                _buffer[k][c] += n

        original = original[sz:]

    # using the offset and lengths grabbed, we'll set the buffer
    _buffer[k]['buffer'] = original
    return _buffer


def readlink(fpath):
    """
    Parses a symlink to get the target path.

    :param fpath: path to the symlink
    :type  fpath: basestring
    :return: target path
    :rtype: basestring
    """
    if not islink(fpath):
        return None

    # open the file
    handle = win32file.CreateFileW(
        fpath,
        win32file.GENERIC_READ,
        0,
        None,
        win32file.OPEN_EXISTING,
        win32file.FILE_FLAG_OPEN_REPARSE_POINT,
        0)

    # MAXIMUM_REPARSE_DATA_BUFFER_SIZE = 16384 = (16*1024)
    _buffer = win32file.DeviceIoControl(
        handle,
        FSCTL_GET_REPARSE_POINT,
        None,
        16*1024)

    # above will return an ugly string (byte array), so we'll need to parse it
    win32file.CloseHandle(handle)

    # minimum possible length
    # (assuming that the length of the target is bigger than 0)
    if len(_buffer) < 9:
        return None

    # parse and return our result
    result = parse_reparse_buffer(_buffer)
    offset = result[SYMBOLIC_LINK]['substitute_name_offset']
    ending = offset + result[SYMBOLIC_LINK]['substitute_name_length']
    rpath = result[SYMBOLIC_LINK]['buffer'][offset:ending].replace('\x00', '')
    if len(rpath) > 4 and rpath[0:4] == '\\??\\':
        rpath = rpath[4:]

    return rpath


def realpath(fpath):
    """
    Evaluates a path completely, expanding all symlinks.

    :param fpath: path to expand
    :type  fpath: basestring
    :return: expanded path
    :rtype: basestring
    """
    while islink(fpath):
        rpath = readlink(fpath)
        if not os.path.isabs(rpath):
            rpath = os.path.abspath(os.path.join(os.path.dirname(fpath), rpath))

        fpath = rpath

    return fpath
