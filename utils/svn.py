"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Utilities for interfacing with SVN
"""
import pysvn

from constants import TEST_SUBDIRS
from strings import plainstr


__version__ = '$Rev: 252047 $'

TEST_SUBDIRS = tuple(s.lower() for s in TEST_SUBDIRS)


def _is_invalid_url_exception(exc):
    """
    Determines if an exception is for an invalid SVN URL.

    :param exc: exception under scrutiny
    :type  exc: Exception
    :return: whether the exception is for an invalid SVN URL
    :rtype: bool
    """
    exc = str(exc)
    invalid_url_str = [
        'non-existent',
        'doesn\'t exist',
        'path not found',
        'No such host is known',
        'was not found.'
    ]

    return any([s in exc for s in invalid_url_str])


def export(url, path, revision=None):
    """
    Exports an SVN path to a local destination, removing SVN information.

    :param url: SVN path to export
    :type  url: basestring
    :param path: local path to export to
    :type  path: basestring
    :param revision: revision of the SVN path to export
    :type  revision: int
    :return: whether the export was successful
    :rtype: bool
    """
    if revision is None:
        # use HEAD as revision
        svn_rev = pysvn.Revision(pysvn.opt_revision_kind.head)

    else:
        svn_rev = pysvn.Revision(
            pysvn.opt_revision_kind.number, str(revision))

    try:
        pysvn.Client().export(
            src_url_or_path=url,
            dest_path=path,
            revision=svn_rev,
            recurse=True,
            peg_revision=pysvn.Revision(pysvn.opt_revision_kind.unspecified))

        return True

    except pysvn.ClientError as e:
        if _is_invalid_url_exception(e):
            return False

        raise


def listdir(url, depth=pysvn.depth.infinity):
    """
    Lists all artifacts under an SVN directory.

    :param url: SVN directory to search
    :type  url: basestring
    :param depth: search depth
    :type  depth: pysvn.depth
    :return: SVN paths to all artifacts under the search directory
    :rtype: list[basestring]
    """
    return [plainstr(l[0]['path']) for l in pysvn.Client().list(
        url, depth=depth)]


def exists(url, revision=None, kind=None):
    """
    Checks whether an artifact exists at a given URL and SVN revision.

    :param url: SVN artifact to check for
    :type  url: basestring
    :param revision: revision of the artifact to check for
    :type  revision: int
    :param kind: kind of artifact to check for (file or dir)
    :type  kind: pysvn.node_kind
    :return: whether the artifact exists
    :rtype: bool
    """
    if revision is None:
        # use HEAD as revision
        svn_rev = pysvn.Revision(pysvn.opt_revision_kind.head)

    else:
        svn_rev = pysvn.Revision(pysvn.opt_revision_kind.number, str(revision))

    try:
        info = pysvn.Client().info2(url, revision=svn_rev)

    except:
        return False

    if len(info) < 0:
        return False

    if info[0][1]['rev'].number == -1:
        return False

    if kind is None:
        return True

    return info[0][1].kind == kind


def file_exists(url, revision=None):
    """
    Checks whether a file exists at a given URL and SVN revision.

    :param url: SVN file to check for
    :type  url: basestring
    :param revision: revision of the file to check for
    :type  revision: int
    :return: whether the file exists
    :rtype: bool
    """
    return exists(url, revision=revision, kind=pysvn.node_kind.file)


def dir_exists(url, revision=None):
    """
    Checks whether a directory exists at a given URL and SVN revision.

    :param url: SVN directory to check for
    :type  url: basestring
    :param revision: revision of the directory to check for
    :type  revision: int
    :return: whether the directory exists
    :rtype: bool
    """
    return exists(url, revision=revision, kind=pysvn.node_kind.file)


def info(url):
    """
    Gets information about an SVN artifact.

    :param url: SVN artifact to get info on
    :type  url: basestring
    :return: information about the SVN artifact
    :rtype: PysvnInfo
    """
    try:
        return pysvn.Client().info2(url)[0][1]

    except pysvn.ClientError as e:
        if _is_invalid_url_exception(e):
            return None

        raise


def walk(url):
    """
    Gets information about an SVN artifact and its children.

    :param url: SVN artifact to get info on
    :type  url: basestring
    :return: local path and information about the SVN artifacts
    :rtype: [basestring, PysvnInfo]
    """
    try:
        return pysvn.Client().info2(url)

    except pysvn.ClientError as e:
        if _is_invalid_url_exception(e):
            return None

        raise


def log(url, limit=0):
    """
    Gets the commit log for an SVN artifact.

    :param url: SVN file or directory to get the log for
    :type  url: basestring
    :param limit: number of log entries to return (returns all by default)
    :type  limit: int
    :return: commit log for the SVN artifact
    :rtype: PysvnLog
    """
    return pysvn.Client().log(url, limit=limit)


def test_root(file_url):
    """
    Gets the SVN URL of the root test directory for a test file.

    :param file_url: SVN test file to find the root directory for
    :type  file_url: basestring
    :return: root test directory
    :rtype: basestring
    """
    url = file_url.rsplit('/', 1)[0]
    while url.lower().endswith(TEST_SUBDIRS):
        url = url.rsplit('/', 1)[0]

    return url


def latest_revisions(url):
    """
    Gets the latest SVN revisions for an artifact.

    :param url: URL of the artifact
    :type  url: basestring
    :return: latest revisions
    :rtype: set(int)
    """
    if not exists(url):
        return None

    revisions = set()
    last_changed = i['last_changed_rev'].number
    if last_changed is not None:
        revisions.add(int(last_changed))

    latest = latest_revision(url)
    if latest is not None:
        revisions.add(int(latest))

    return revisions


def latest_revision(url):
    """
    Gets the latest SVN revision for an artifact.

    :param url: URL of the artifact
    :type  url: basestring
    :return: latest revision
    :rtype: int
    """
    if not exists(url):
        return None

    return log(url, limit=1)[0]['revision'].number


def checkout(url, path, revision=None):
    """
    Checks out an SVN path to a local destination, including SVN information.

    :param url: SVN path to checkout
    :type  url: basestring
    :param path: local path to checkout to
    :type  path: basestring
    :param revision: revision of the SVN path to checkout
    :type  revision: int
    :return: whether the checkout was successful
    :rtype: bool
    """
    if revision is None:
        # use HEAD as revision
        svn_rev = pysvn.Revision(pysvn.opt_revision_kind.head)

    else:
        svn_rev = pysvn.Revision(pysvn.opt_revision_kind.number, str(revision))

    try:
        pysvn.Client().checkout(
            url=url,
            path=path,
            revision=svn_rev,
            recurse=True,
            peg_revision=pysvn.Revision(pysvn.opt_revision_kind.unspecified))

        return True

    except pysvn.ClientError as e:
        if _is_invalid_url_exception(e):
            return False

        raise


def commit(paths, message, depth=pysvn.depth.infinity):
    """
    Commits an artifact to SVN.

    :param paths: local path(s) to the artifact(s) to commit
    :type  paths: basestring or list
    :param message: message to commit with
    :type  message: basestring
    :param depth: commit depth
    :type  depth: pysvn.depth
    """
    if not isinstance(paths, list):
        paths = [paths]

    svn = pysvn.Client()
    for path in paths:
        status = svn.status(path)[0]
        if status.is_versioned != 1:
            svn.add(path)

    svn.checkin(
        path=paths,
        log_message=message,
        depth=depth)
