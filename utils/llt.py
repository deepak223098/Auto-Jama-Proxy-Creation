"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Utilities for interacting with low level test files
"""
import files
import svn
from cache import LOGFILE_RE


__version__ = '$Rev: 251221 $'


class LLTFilesCacheException(Exception):
    """Exception to raise when there is an issue caching LLT files"""
    pass


class LLTFiles(object):
    """Container for low level test files"""
    def __init__(self, test_dir, tc, tp, env, logs, cached=False):
        """
        Constructor called in instantiation.  Creates a container for LLT files.
        
        :param test_dir: URL for the test directory
        :type  test_dir: basestring
        :param tc: URL for the test case (.xlsm) file
        :type  tc: basestring
        :param tp: URL for the test procedure (.tst) file
        :type  tp: basestring
        :param env: URL for the environment (.env) file
        :type  env: basestring
        :param logs: URLs for the log (.html) files
        :type  logs: list[basestring]
        :param cached: flag to denote that the paths are local, not URLs
        :type  cached: bool
        """
        self.dir = test_dir
        self.tc = tc
        self.tp = tp
        self.env = env
        self.logs = logs
        self.cached = cached

    def cache(self, local_test_dir, checkout=False):
        """
        Exports the LLT files into a local directory and changes the URLs to
        the new local paths.
        
        :param local_test_dir: directory to export the test directory to
        :type  local_test_dir: basestring
        :param checkout: checkout the files instead of exporting them
        :type  checkout: bool
        """
        if self.cached:
            raise LLTFilesCacheException(
                'LLT files already cached at "{}"'.format(self.dir))

        if checkout:
            svn.checkout(self.dir, local_test_dir)

        else:
            svn.export(self.dir, local_test_dir)

        self.map_cache(local_test_dir)

    def map_cache(self, local_test_dir):
        """
        Changes the URLs to the new local paths.

        :param local_test_dir: directory to map files to
        :type  local_test_dir: basestring
        """
        if self.cached:
            raise LLTFilesCacheException(
                'LLT files already cached at "{}"'.format(self.dir))

        new_dir = None
        new_tc = None
        new_tp = None
        new_env = None
        new_logs = []
        for path, info in svn.walk(local_test_dir):
            url = info['URL']
            if new_dir is None and url == self.dir:
                new_dir = path
                continue

            if new_tc is None and url == self.tc:
                new_tc = path
                continue

            if new_tp is None and url == self.tp:
                new_tp = path
                continue

            if new_env is None and url == self.env:
                new_env = path
                continue

            for log in self.logs:
                if url == log:
                    new_logs.append(path)
                    break

        if (not all([new_dir, new_tc, new_tp, new_env]) or
                len(new_logs) != len(self.logs)):
            raise LLTFilesCacheException(
                'Some LLT files failed to cache at "{}"'.format(local_test_dir))

        self.dir = new_dir
        self.tc = new_tc
        self.tp = new_tp
        self.env = new_env
        self.logs = new_logs
        self.cached = True


def associated_test_files(test_file):
    """
    Gets all test files associated with the given test file.

    :param test_file: test file for which to find associated test files
    :type  test_file: basestring
    :return: test files associated with the given test file
    :rtype: LLTFiles
    """
    test_dir = svn.test_root(test_file)
    test_filename = test_file.rsplit('/')[-1]
    match = LOGFILE_RE.search(test_filename)
    if match is not None:
        fname = test_filename[:-len(match.group(0))].lower()

    else:
        fname = test_filename.rsplit('.', 1)[0].lower()

    tc = None
    tp = None
    env = None
    logs = []
    for url in svn.listdir(test_dir):
        url_fname = files.filename(url, url=True).lower()
        if (url.endswith('.html') and
                url_fname.startswith(fname) and
                LOGFILE_RE.match(
                    '{}.html'.format(url_fname[len(fname):]))):
            logs.append(url)
            continue

        if not url_fname == fname:
            continue

        if tc is None and url.endswith('.xlsm'):
            tc = url
            continue

        if tp is None and url.endswith('.tst'):
            tp = url
            continue

        if env is None and url.endswith('.env'):
            env = url
            continue

    return LLTFiles(
        test_dir=test_dir, tc=tc, tp=tp, env=env, logs=logs)
