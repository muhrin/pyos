import re
from typing import List, Iterator

from pyos import config
from pyos import db
from pyos import os

EXCLUDE_HIDDEN = '(?!\\.)'  # Exclude names starting with dot
MAGIC_CHECK = re.compile('([*?[])')
GLOBSTAR_CHECK = re.compile(r'((?:^|/)\*+(?:$|/))')
PATH_SEGMENT = r'([^/]*)'


def glob(pathname: str, *, recursive=False) -> List[str]:
    return list(iglob(pathname, recursive=recursive))


def iglob(pathname: str, *, recursive=False) -> Iterator[str]:
    hist = db.get_historian()

    if not has_magic(pathname):
        if os.path.exists(pathname):
            yield pathname
        return

    dirname, basename = os.path.split(pathname)

    # Make sure we have an absolute directory (this will also get the cwd if needed)
    dirname = os.path.abspath(dirname)

    if not pathname.endswith(os.sep):
        startdir = _get_startdir(pathname)

        match = GLOBSTAR_CHECK.search(pathname)
        if recursive and match and match.end(0) == len(pathname):
            # Ends in globstar so looking for files AND directories
            found_dirs = set()

            regex = get_dir_regex(os.path.abspath(pathname), recursive=True, complete_match=False)
            regobj = re.compile(regex + r'$')
            query = q_regex(config.DIR_KEY, regex)
            for oid, meta in hist.meta.find(query):
                path = db.get_abspath(oid, meta)

                dirname = os.path.dirname(path)
                yield from get_new_matching_dirs(dirname,
                                                 regobj,
                                                 anchor=startdir,
                                                 existing=found_dirs)

                # Yield the filename
                yield os.path.join(startdir, os.path.relpath(path, startdir))

        else:
            query = {
                **q_regex(config.NAME_KEY, filename_pattern(basename)),
                **q_regex(config.DIR_KEY,
                          get_dir_regex(dirname, recursive=recursive, complete_match=True))
            }

            for oid, meta in hist.meta.find(query):
                path = db.get_abspath(oid, meta)
                yield os.path.join(startdir, os.path.relpath(path, startdir))

            # Check if the pathname ends with magic
            # match = MAGIC_CHECK.search(pathname)
            # if match and match.end(0) == len(pathname):
            # Look for matching directories
            yield from _glob_dirs(pathname, recursive=recursive)
    else:
        # Looking for directories _only_
        yield from _glob_dirs(pathname, recursive=recursive)


def _glob_dirs(dirname: str, *, recursive=False) -> Iterator[str]:
    startdir = _get_startdir(dirname)

    pattern = '^' + get_dir_regex(dirname, recursive=recursive, complete_match=False)

    # Look for objects that are in the given directory or anywhere below
    query = q_regex(config.DIR_KEY, pattern)

    # For each match we have to check that it meets the given criterion as it may be a subdirectory
    regobj = re.compile(pattern + r'$')
    hist = db.get_historian()
    found = set()
    for dname in hist.meta.distinct(config.DIR_KEY, query):
        new = get_new_matching_dirs(dname, regobj, anchor=startdir, existing=found)
        yield from new


def _get_startdir(pathname: str) -> str:
    """Get the starting directory for a pathname search.  This will be the first directory that
    doesn't contain any magic characters"""
    match = MAGIC_CHECK.search(pathname)
    if not match:
        return pathname
    try:
        idx = pathname.rindex(os.sep, 0, match.start(0))
    except ValueError:
        return ''
    else:
        return pathname[:idx + 1]


def q_regex(field: str, pattern: str) -> dict:
    if has_magic(pattern):
        return {field: {'$regex': pattern}}

    return {field: pattern}


def get_dir_regex(pattern: str, *, recursive=False, complete_match=True):
    if not pattern.endswith(os.sep):
        pattern += os.sep
    pattern = os.path.abspath(pattern)

    if not has_magic(pattern):
        return pattern

    regex = get_regex(pattern, recursive=recursive)
    if complete_match:
        return '^' + regex + '$'

    return regex


def filename_pattern(filename: str, complete_match=True) -> str:
    if not filename or not has_magic(filename):
        return filename

    regex = get_regex(filename, recursive=False)
    if complete_match:
        regex = '^' + regex + '$'

    return regex


def get_new_matching_dirs(path: str, regobj, anchor='/', existing: set = None) -> set:
    new = set()
    existing = existing if existing is not None else set()

    relative = os.path.relpath(path, os.path.abspath(anchor))
    if relative == os.curdir:
        partial = anchor
        abspath = os.path.abspath(partial)
        if partial and abspath not in existing and regobj.match(abspath):
            new.add(partial)
            existing.add(abspath)
        return new

    split = relative
    while split and split != os.sep:
        partial = os.path.join(anchor, split)
        abspath = os.path.abspath(partial)
        if abspath not in existing and regobj.match(abspath):
            new.add(partial)
            existing.add(abspath)
        split = os.path.split(split)[0]

    return new


def has_magic(string: str) -> bool:
    return MAGIC_CHECK.search(string) is not None


def escape(pathname: str) -> str:
    """Escape all special characters."""
    return MAGIC_CHECK.sub(r'[\1]', pathname)


def get_regex(pattern: str, recursive=False):
    if not pattern or not has_magic(pattern):
        return pattern

    globstar = recursive

    re_str = ''
    idx = 0
    while idx < len(pattern):
        char = pattern[idx]

        if char in '*?' and _prv(pattern, idx) in [os.sep, None]:
            # We are following from a separator so exclude hidden paths
            re_str += EXCLUDE_HIDDEN

        if char in '/$^+.()=!|':
            re_str += '\\' + char

        elif char == "?":
            re_str += '[^/]'

        elif char == '*':

            # Move over all consecutive "*"'s.
            # Also store the previous and next characters
            pre_char = _prv(pattern, idx)
            star_count = 1

            while _nxt(pattern, idx) == '*':
                star_count += 1
                idx += 1

            next_char = _nxt(pattern, idx)

            if not globstar:
                # globstar is disabled, so treat any number of "*" as one
                re_str += PATH_SEGMENT
            else:
                # globstar is enabled, so determine if this is a globstar segment

                # multiple "*"'s
                # from the start of the segment
                # to the end of the segment

                is_globstar = star_count > 1 \
                              and pre_char in [os.sep, None] \
                              and next_char in [os.sep, None]

                if is_globstar:
                    # it's a globstar, so match zero or more path segments
                    re_str += r'((?:[^/]*(?:\/|$))*)'
                    idx += 1  # move over the "/"
                else:
                    # it's not a globstar, so only match one path segment
                    re_str += PATH_SEGMENT

        else:
            # Default
            re_str += char

        idx += 1

    return re_str


def _nxt(string, idx):
    if idx + 1 >= len(string):
        return None

    return string[idx + 1]


def _prv(string, idx):
    if idx == 0:
        return None
    return string[idx - 1]
