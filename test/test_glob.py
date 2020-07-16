import functools
from typing import List

import pytest

from pyos import glob
from pyos import os
from pyos import psh
from . import support


def norm(tempdir, *parts) -> str:
    return os.path.normpath(os.path.join(tempdir, *parts))


def joins(tempdir, *tuples) -> List[str]:
    return [os.path.join(tempdir, *parts) for parts in tuples]


def mktemp(tempdir, *parts):
    filename = norm(tempdir, *parts)
    support.create_empty_file(filename)


change_cwd = support.change_cwd


@pytest.fixture
def test_dir():
    tempdir = "globtest_dir"
    mktemp(tempdir, 'a', 'D')
    mktemp(tempdir, 'aab', 'F')
    mktemp(tempdir, '.aa', 'G')
    mktemp(tempdir, '.bb', 'H')
    mktemp(tempdir, 'aaa', 'zzzF')
    mktemp(tempdir, 'ZZZ')
    mktemp(tempdir, 'EF')
    mktemp(tempdir, 'a', 'bcd', 'EF')
    mktemp(tempdir, 'a', 'bcd', 'efg', 'ha')

    yield tempdir
    # TODO: Remove directory
    psh.rm - psh.r(tempdir)


def check_glob(tempdir, *parts, **kwargs):
    if len(parts) == 1:
        pattern = parts[0]
    else:
        pattern = os.path.join(*parts)
    p = os.path.join(tempdir, pattern)
    res = glob.glob(p, **kwargs)
    assert len(list(glob.iglob(p, **kwargs))) == len(res)
    return res


def assertSequencesEqual_noorder(l1, l2):
    l1 = list(l1)
    l2 = list(l2)
    assert set(l1) == set(l2)
    assert sorted(l1) == sorted(l2)


def test_glob_literal(test_dir):
    eq = assertSequencesEqual_noorder
    do_check = functools.partial(check_glob, test_dir)
    do_norm = functools.partial(norm, test_dir)

    # orig: eq(do_check(test_dir, 'a'), [norm(test_dir, 'a')])
    eq(do_check('a/'), [do_norm('a/')])

    eq(do_check('a', 'D'), [do_norm('a', 'D')])

    # orig: eq(do_check(test_dir, 'aab'), [norm(test_dir, 'aab')])
    eq(do_check('aab/'), [do_norm('aab/')])

    eq(do_check('zymurgy'), [])

    res = check_glob(test_dir, '*')
    assert {type(r) for r in res} == {str}
    res = glob.glob(os.path.join(test_dir, '*'))
    assert {type(r) for r in res} == {str}


def test_glob_one_directory(test_dir):
    eq = assertSequencesEqual_noorder
    do_norm = functools.partial(norm, test_dir)
    do_check = functools.partial(check_glob, test_dir)

    # originals had aaa and aab etc (without '/') as posix doesn't enforce trailing '/' for directories
    eq(do_check('a*'), map(do_norm, ['a/', 'aab/', 'aaa/']))
    eq(do_check('*a'), map(do_norm, ['a/', 'aaa/']))
    eq(do_check('.*'), map(do_norm, ['.aa/', '.bb/']))
    eq(do_check('?aa'), map(do_norm, ['aaa/']))
    eq(do_check('aa?'), map(do_norm, ['aaa/', 'aab/']))
    eq(do_check('aa[ab]'), map(do_norm, ['aaa/', 'aab/']))
    eq(do_check('*q'), [])


def test_glob_nested_directory(test_dir):
    eq = assertSequencesEqual_noorder
    do_norm = functools.partial(norm, test_dir)
    do_check = functools.partial(check_glob, test_dir)

    eq(do_check('a', 'bcd', 'E*'), [do_norm('a/', 'bcd/', 'EF')])
    eq(do_check('a', 'bcd', '*g'), [do_norm('a/', 'bcd/', 'efg/')])


def test_glob_directory_names(test_dir):
    eq = assertSequencesEqual_noorder
    do_norm = functools.partial(norm, test_dir)
    do_check = functools.partial(check_glob, test_dir)

    eq(do_check('*', 'D'), [do_norm('a', 'D')])
    eq(do_check('*', '*a'), [])
    eq(do_check('a', '*', '*', '*a'), [do_norm('a', 'bcd', 'efg', 'ha')])
    eq(do_check('?a?', '*F'), [do_norm('aaa', 'zzzF'), do_norm('aab', 'F')])


def test_glob_directory_with_trailing_slash(test_dir):
    do_norm = functools.partial(norm, test_dir)

    # Patterns ending with a slash shouldn't match non-dirs
    res = glob.glob(do_norm('Z*Z') + os.sep)
    assert res == []
    res = glob.glob(do_norm('ZZZ') + os.sep)
    assert res == []
    # When there is a wildcard pattern which ends with os.sep, glob()
    # doesn't blow up.
    res = glob.glob(do_norm('aa*') + os.sep)
    assert len(res) == 2
    # either of these results is reasonable
    assert set(res) in [
        {do_norm('aaa'), do_norm('aab')},
        {do_norm('aaa') + os.sep, do_norm('aab') + os.sep},
    ]


def check_escape(arg, expected):
    assert glob.escape(arg) == expected


def test_escape():
    check = check_escape
    check('abc', 'abc')
    check('[', '[[]')
    check('?', '[?]')
    check('*', '[*]')
    check('[[_/*?*/_]]', '[[][[]_/[*][?][*]/_]]')
    check('/[[_/*?*/_]]/', '/[[][[]_/[*][?][*]/_]]/')


def rglob(tempdir, *parts, **kwargs):
    return check_glob(tempdir, *parts, recursive=True, **kwargs)


def test_recursive_glob(test_dir):
    eq = assertSequencesEqual_noorder
    full = [
        ('EF',),
        ('ZZZ',),
        ('a/',),
        ('a', 'D'),

        # orig: ('a', 'bcd'),
        ('a', 'bcd/'),
        ('a', 'bcd', 'EF'),

        # orig: ('a', 'bcd', 'efg'),
        ('a', 'bcd', 'efg/'),
        ('a', 'bcd', 'efg', 'ha'),
        ('aaa/',),
        ('aaa', 'zzzF'),
        ('aab/',),
        ('aab', 'F'),
    ]
    eq(rglob(test_dir, '**'), joins(test_dir, ('',), *full))
    eq(rglob(test_dir, os.curdir, '**'),
       joins(test_dir, (os.curdir, ''), *((os.curdir,) + i for i in full)))
    dirs = [('a', ''), ('a', 'bcd', ''), ('a', 'bcd', 'efg', ''), ('aaa', ''), ('aab', '')]

    eq(rglob(test_dir, '**', ''), joins(test_dir, ('',), *dirs))

    eq(
        rglob(test_dir, 'a', '**'),
        joins(test_dir, ('a', ''), ('a', 'D'), ('a', 'bcd/'), ('a', 'bcd', 'EF'),
              ('a', 'bcd', 'efg/'), ('a', 'bcd', 'efg', 'ha')))
    eq(rglob(test_dir, 'a**/'), joins(test_dir, ('a/',), ('aaa/',), ('aab/',)))
    expect = [('a', 'bcd', 'EF'), ('EF',)]

    eq(rglob(test_dir, '**', 'EF'), joins(test_dir, *expect))
    expect = [('a', 'bcd', 'EF'), ('aaa', 'zzzF'), ('aab', 'F'), ('EF',)]

    eq(rglob(test_dir, '**', '*F'), joins(test_dir, *expect))
    eq(rglob(test_dir, '**', '*F', ''), [])
    eq(rglob(test_dir, '**', 'bcd', '*'), joins(test_dir, ('a', 'bcd', 'EF'), ('a', 'bcd', 'efg/')))
    eq(rglob(test_dir, 'a', '**', 'bcd'), joins(test_dir, ('a', 'bcd/')))

    with change_cwd(test_dir):
        join = os.path.join
        eq(glob.glob('**', recursive=True), [join(*i) for i in full])
        eq(glob.glob(join('**', ''), recursive=True), [join(*i) for i in dirs])
        eq(glob.glob(join('**', '*'), recursive=True), [join(*i) for i in full])
        eq(glob.glob(join(os.curdir, '**'), recursive=True),
           [join(os.curdir, '')] + [join(os.curdir, *i) for i in full])
        eq(glob.glob(join(os.curdir, '**', ''), recursive=True),
           [join(os.curdir, '')] + [join(os.curdir, *i) for i in dirs])
        eq(glob.glob(join(os.curdir, '**', '*'), recursive=True),
           [join(os.curdir, *i) for i in full])
        eq(glob.glob(join('**', 'zz*F'), recursive=True), [join('aaa', 'zzzF')])
        eq(glob.glob('**zz*F', recursive=True), [])
        expect = [join('a', 'bcd', 'EF'), 'EF']
        eq(glob.glob(join('**', 'EF'), recursive=True), expect)
