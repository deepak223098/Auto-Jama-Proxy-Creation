"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Utility functions for caching SVN files to be used in verification.
"""
import logging
import os
import re
import urlparse
from collections import namedtuple

import pysvn
import uuid
import xlrd
from enum import Enum

import execute
import files
import svn
from constants import TEMP_DIR


__version__ = '$Rev: 243452 $'

# matches a test directory in a URL
TESTDIR_RE = re.compile(r'/tests?/', re.IGNORECASE)

# matches a file extension for a disposition file
DISPOSITION_RE = re.compile(
    r'\.(?:xml|xls|xlsx|xlsm|csv|txt)$', re.IGNORECASE)

# matches the last part of a log file name
# platform - which platform the log was executed against
# negative - a qualifier for the coverage level
# positive - a qualifier for the coverage level
# coverage - the coverage level
LOGFILE_RE = re.compile(
    r'(?:[-_](?P<platform>host|target))?'
    r'(?:[-_](?:(?P<negative>without)|(?P<positive>with)))?'
    r'(?:[-_](?P<coverage>cover(?:age)?))?'
    r'(?:\.(?P<platform2>h|t))?'
    r'(?:-(?P<platform3>host|targ|target))?'
    r'\.(?:log|xml|html)$', re.IGNORECASE)

# container for organizing cached reference files
References = namedtuple('References', ['logs', 'dispositions'])


class Platform(Enum):
    """Environments in which tests can be executed"""
    Host = 'host'
    Target = 'target'


class SvnFileDoesNotExist(Exception):
    """Exception for when an SVN file doesn't exist at the expected URL"""
    pass


class CacheDirNotSet(Exception):
    """Exception for when the cache directory has not been set"""
    pass


class FileCache(object):
    """Interface for cached SVN files"""
    def __init__(self, name, url, revision, path):
        """
        Constructor called in instantiation.  Creates a cached file interface.

        :param name: name of the cached file
        :type  name: basestring
        :param url: SVN URL of the cached file
        :type  url: basestring
        :param revision: SVN revision of the cached file
        :type  revision: int
        :param path: local path to the cached file
        :type  path: basestring
        """
        object.__init__(self)
        self._name = name
        self._url = url
        self._revision = revision
        self._path = path

    def read(self):
        """
        Gets the contents of the cached file.

        :return: contents of the cached file
        :rtype: basestring
        """
        with open(self._path, 'r') as f:
            return f.read()

    def readlines(self):
        """
        Gets the contents of the cached as a list of lines.

        :return: contents of the cached file
        :rtype: list of basestrings
        """
        with open(self._path, 'r') as f:
            return f.readlines()

    def read_workbook(self):
        """
        Gets the contents of the cached as an Excel workbook.

        :return: contents of the cached file
        :rtype: xlrd.Book
        """
        return xlrd.open_workbook(self._path)

    @property
    def name(self):
        """
        Gets the name of the cached file.

        :return: name of the cached file
        :rtype: basestring
        """
        return self._name

    @property
    def url(self):
        """
        Gets the SVN URL of the cached file.

        :return: SVN URL of the cached file
        :rtype: basestring
        """
        return self._url

    @property
    def revision(self):
        """
        Gets the SVN revision of the cached file.

        :return: SVN revision of the cached file
        :rtype: basestring
        """
        return self._revision

    @property
    def path(self):
        """
        Gets the local path of the cached file.

        :return: local path of the cached file
        :rtype: basestring
        """
        return self._path


class LogFileCache(FileCache):
    """Interface for cached log files"""
    def __init__(self, name, url, revision, path, platform, coverage):
        """
        Constructor called in instantiation.  Creates a cached log file
        interface.

        :param name: name of the cached file
        :type  name: basestring
        :param url: SVN URL of the cached file
        :type  url: basestring
        :param revision: SVN revision of the cached file
        :type  revision: int
        :param path: local path to the cached file
        :type  path: basestring
        :param platform: platform the log was executed against
        :type  platform: Platform
        :param coverage: whether or not coverage was enabled in the log
        :type  coverage: bool
        """
        FileCache.__init__(self, name, url, revision, path)
        self._platform = platform
        self._coverage = coverage

    @classmethod
    def from_file_cache(cls, cache, platform, coverage):
        """
        Creates a log file cache from a normal file cache.

        :param cache: normal file cache
        :type  cache: FileCache
        :param platform: platform the log was executed against
        :type  platform: Platform
        :param coverage: whether or not coverage was enabled in the log
        :type  coverage: bool
        """
        return cls(
            name=cache._name,
            url=cache._url,
            revision=cache._revision,
            path=cache._path,
            platform=platform,
            coverage=coverage)

    @property
    def platform(self):
        """
        Gets the platform the cached log file was executed against.

        :return: platform the cached log file was executed against
        :rtype: Platform
        """
        return self._platform

    @property
    def coverage(self):
        """
        Gets whether coverage metrics were included in the cached log file.

        :return: whether coverage metrics were included in the cached log file
        :rtype: bool
        """
        return self._coverage


class CacheFileThread(execute.ExceptionThread):
    """Thread for caching a file"""
    def __init__(self, url, revision=None):
        """
        Constructor called in instantiation.  Creates a thread to cache an SVN
        file asynchronously.

        :param url: SVN URL of the file
        :type  url: basestring
        :param revision: SVN revision of the file
        :type  revision: int
        """
        execute.ExceptionThread.__init__(self)
        self.url = url
        self.revision = revision
        self.file_cache = None

    def run(self, *args, **kwargs):
        """
        Executes the thread.
        """
        execute.ExceptionThread.run(self)
        self.file_cache = SVNCache.cache_file(
            url=self.url,
            revision=self.revision)


class CacheLogFileThread(CacheFileThread):
    """Thread for caching a log file"""
    def __init__(self, url, platform, coverage, revision=None):
        """
        Constructor called in instantiation.  Creates a thread to cache an SVN
        log file asynchronously.

        :param url: SVN URL of the file
        :type  url: basestring
        :param platform: platform the log was executed against
        :type  platform: Platform
        :param coverage: whether or not coverage was enabled in the log
        :type  coverage: bool
        :param revision: SVN revision of the file
        :type  revision: int
        """
        CacheFileThread.__init__(self, url, revision=revision)
        self.platform = platform
        self.coverage = coverage

    def run(self, *args, **kwargs):
        """
        Executes the thread.
        """
        self.file_cache = LogFileCache.from_file_cache(
            cache=SVNCache.cache_file(
                url=self.url,
                revision=self.revision),
            platform=self.platform,
            coverage=self.coverage)


class SVNCache(object):
    """Simple cache for keeping track of cached files (NOT THREADSAFE!)"""
    _cached_files = []
    _cache_dir = None

    @classmethod
    def add_cached_file(cls, file_cache):
        """
        Adds a file to the cache.

        :param file_cache: file to add to the cache
        :type  file_cache: FileCache
        """
        cls._cached_files.append(file_cache)

    @classmethod
    def get_cached_file(cls, url, revision=None):
        """
        Gets a file from the cache if it has already been cached.

        :param url: SVN URL of the file to get
        :type  url: basestring
        :param revision: SVN revision of the file to get
        :type  revision: int
        :return: cached file if it exists, else None
        :rtype: FileCache
        """
        for f in cls._cached_files:
            if f.url == url and f.revision == revision:
                return f

        return None

    @classmethod
    def set_cache_dir(cls, cache_dir):
        """
        Sets the cache directory

        :param cache_dir: local directory to cache files to
        :type  cache_dir: basestring
        """
        cls._cache_dir = cache_dir

    @classmethod
    def cache_file(cls, url, revision=None):
        """
        Caches an SVN file locally for verification.
    
        :param url: SVN URL of the file
        :type  url: basestring
        :param revision: SVN revision of the file
        :type  revision: int
        :return: the cached file
        :rtype: FileCache
        """
        if cls._cache_dir is None:
            raise CacheDirNotSet('The cache directory has not been set')

        with execute.KeyLocker.lock(
                'cache-file-{url}-{rev}'.format(url=url, rev=revision)):
            existing_cache = SVNCache.get_cached_file(url, revision=revision)
            if existing_cache is not None:
                return existing_cache

            files.mkdir(cls._cache_dir)

            # generate cache path
            filename = os.path.basename(urlparse.urlparse(url).path)
            cache_path = os.path.join(cls._cache_dir, '{uuid}_{fname}'.format(
                uuid=uuid.uuid4(), fname=filename))

            # export file
            logging.debug('Caching "{url}" at "{path}"...'.format(
                url=url, path=cache_path))

            url_exists = svn.export(url=url, path=cache_path, revision=revision)
            if not url_exists:
                raise SvnFileDoesNotExist('File does not exist at "{}"'.format(url))

            file_cache = FileCache(
                name=filename,
                url=url,
                revision=revision,
                path=cache_path)

            SVNCache.add_cached_file(file_cache)
            return file_cache

    @classmethod
    def cache_references(cls, cached_files):
        """
        Finds and caches reference files associated with the given cached files.
    
        :param cached_files: cached files to find associated reference files for
        :type  cached_files: list[FileCaches]
        :return: cached reference files
        :rtype: References
        """
        if cls._cache_dir is None:
            raise CacheDirNotSet('The cache directory has not been set')

        logging.debug('Caching reference files...')

        # gather test directory URLs associated with the files
        test_dirs = set()
        for f in cached_files:
            if TESTDIR_RE.search(f.url) is not None:
                test_dirs.add(svn.test_root(f.url))

        logging.debug('Searching test directories for reference files:{}'.format(
            ''.join(['\n - {}'.format(k) for k in test_dirs])))

        log_threads = []
        disposition_threads = []
        for test_dir in test_dirs:
            # get list of paths in the test dir
            suburls = svn.listdir(test_dir)

            # find and cache reference files
            for url in suburls:
                fname = url.rsplit('/', 1)[-1].lower()
                if ('disposition' in url and
                        DISPOSITION_RE.search(fname) is not None):
                    # start cache thread
                    t = CacheFileThread(url=url)
                    t.start()
                    disposition_threads.append(t)
                    continue

                match = LOGFILE_RE.search(fname)
                if match is None:
                    # path is not log or disposition
                    continue

                # determine log information
                platform = Platform.Host
                if any((match.group(v) or '').lower() in ['t', 'targ', 'target']
                       for v in ['platform', 'platform2', 'platform3']):
                    platform = Platform.Target

                coverage = bool(
                    match.group('coverage') and not match.group('negative'))

                # start cache thread
                t = CacheLogFileThread(
                    url=url,
                    platform=platform,
                    coverage=coverage)

                t.start()
                log_threads.append(t)

        # wait for cache to finish
        threads = log_threads[:]
        threads.extend(disposition_threads)
        for t in threads:
            try:
                t.join()

            except (SvnFileDoesNotExist, pysvn.ClientError) as e:
                logging.error(
                    'Failed to cache file "{url}" at revision "{rev}"'.format(
                        url=t.url, rev=t.revision))

                logging.error(str(e).strip())

        refs = References(
            logs=[
                t.file_cache for t in log_threads
                if t.file_cache is not None],
            dispositions=[
                t.file_cache for t in disposition_threads
                if t.file_cache is not None])

        logging.debug('Cached {} reference files'.format(
            len(refs.logs) + len(refs.dispositions)))

        return refs


def tempfile(name):
    """
    Creates a path to a temporary file.

    :param name: file name to convert to a temporary file
    :type  name: basestring
    :return: path to a new temporary file
    :rtype: basestring
    """
    return os.path.join(TEMP_DIR, '{uuid}_{name}'.format(
        uuid=uuid.uuid4(), name=name))
