"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Utility functions for processing command line arguments
"""
__version__ = '$Rev: 235184 $'

FORMAT = '%(levelname)s: %(message)s'


def parse(parser, logging, args=None, logfile=None, logfile_level=None):
    """
    Adds flags for setting the logging level to the argument parser, then parses
    the command line arguments and sets the appropriate logging level.

    :param parser: command line argument parser
    :type  parser: ArgumentParser
    :param logging: logging module
    :type  logging: module
    :param args: arguments to provide to the parser
    :type  args: basestring or list[basestrings]
    :param logfile: path to an output file in which logs will be written
    :type  logfile: basestring
    :param logfile_level: level of logs to be recorded to the log file
    :type  logfile_level: int
    :return: namespace populated with the command line argument values.
    :rtype: namespace
    """

    # add default verbosity arguments
    volume = parser.add_mutually_exclusive_group()
    volume.add_argument(
        '-v', '--verbose', action='store_true', help='show debugging output')

    volume.add_argument(
        '-q', '--quiet', action='store_true',
        help='hide output except for warnings and errors')

    volume.add_argument(
        '-s', '--silent', action='store_true',
        help='hide output except for errors')

    # parse the arguments
    args = parser.parse_args(args=args)

    # determine the verbosity level
    if args.verbose:
        log_level = logging.DEBUG

    elif args.quiet:
        log_level = logging.WARNING

    elif args.silent:
        log_level = logging.ERROR

    else:
        log_level = logging.INFO

    # configure the logging module
    logging.basicConfig(
        format=FORMAT,
        level=log_level)

    if logfile is None:
        return args

    if logfile_level is None:
        logfile_level = log_level

    # add a file stream handler
    file_handler = logging.FileHandler(logfile)
    file_handler.setLevel(logfile_level)
    file_handler.setFormatter(logging.Formatter(FORMAT))
    logging.getLogger('').addHandler(file_handler)
    return args
