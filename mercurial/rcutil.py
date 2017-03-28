# rcutil.py - utilities about config paths, special config sections etc.
#
#  Copyright Mercurial Contributors
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import os

from . import (
    encoding,
    osutil,
    pycompat,
    util,
)

if pycompat.osname == 'nt':
    from . import scmwindows as scmplatform
else:
    from . import scmposix as scmplatform

systemrcpath = scmplatform.systemrcpath
userrcpath = scmplatform.userrcpath

def _expandrcpath(path):
    '''path could be a file or a directory. return a list of file paths'''
    p = util.expandpath(path)
    if os.path.isdir(p):
        join = os.path.join
        return [join(p, f) for f, k in osutil.listdir(p) if f.endswith('.rc')]
    return [p]

def envrcitems(env=None):
    '''Return [(section, name, value, source)] config items.

    The config items are extracted from environment variables specified by env,
    used to override systemrc, but not userrc.

    If env is not provided, encoding.environ will be used.
    '''
    if env is None:
        env = encoding.environ
    checklist = [
        ('EDITOR', 'ui', 'editor'),
        ('VISUAL', 'ui', 'editor'),
        ('PAGER', 'pager', 'pager'),
    ]
    result = []
    for envname, section, configname in checklist:
        if envname not in env:
            continue
        result.append((section, configname, env[envname], '$%s' % envname))
    return result

def defaultrcpath():
    '''return rc paths in default.d'''
    path = []
    defaultpath = os.path.join(util.datapath, 'default.d')
    if os.path.isdir(defaultpath):
        path = _expandrcpath(defaultpath)
    return path

def rccomponents():
    '''return an ordered [(type, obj)] about where to load configs.

    respect $HGRCPATH. if $HGRCPATH is empty, only .hg/hgrc of current repo is
    used. if $HGRCPATH is not set, the platform default will be used.

    if a directory is provided, *.rc files under it will be used.

    type could be either 'path' or 'items', if type is 'path', obj is a string,
    and is the config file path. if type is 'items', obj is a list of (section,
    name, value, source) that should fill the config directly.
    '''
    envrc = ('items', envrcitems())

    if 'HGRCPATH' in encoding.environ:
        # assume HGRCPATH is all about user configs so environments can be
        # overridden.
        _rccomponents = [envrc]
        for p in encoding.environ['HGRCPATH'].split(pycompat.ospathsep):
            if not p:
                continue
            _rccomponents.extend(('path', p) for p in _expandrcpath(p))
    else:
        paths = defaultrcpath() + systemrcpath()
        _rccomponents = [('path', os.path.normpath(p)) for p in paths]
        _rccomponents.append(envrc)
        paths = userrcpath()
        _rccomponents.extend(('path', os.path.normpath(p)) for p in paths)
    return _rccomponents
