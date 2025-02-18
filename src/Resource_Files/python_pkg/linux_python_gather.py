#!/usr/bin/env python3
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

import sys, os, inspect, shutil, platform, textwrap, py_compile, site
from python_paths import py_ver, py_lib, py_exe, py_inc, py_dest, tmp_prefix

# Python standard modules location
srcdir = os.path.dirname(inspect.getfile(os))

# Where we're going to copy stuff
py_dir = os.path.join(py_dest, 'lib', os.path.basename(srcdir))
print ('py_dir', py_dir)
app_dir = os.path.dirname(py_dest)
print ('app_dir', app_dir)

pyhome_dir = os.path.join(app_dir.replace(tmp_prefix, ''), os.path.basename(py_dest))
print ('pyhome_dir', pyhome_dir)
site_dest = os.path.join(py_dir, 'site-packages')

# Cherry-picked additional and/or modified modules
site_packages = [ ('lxml', 'd'), 
                  ('six.py', 'f'), 
                  ('bs4', 'd'), 
                  ('html5lib','d'), 
                  ('PIL', 'd'), 
                  ('regex.py','f'),
                  ('_regex.cpython-34m.so','f'),
                  ('_regex_core.py','f'),
                  ('test_regex.py', 'f')]


def copy_site_packages(packages, dest):
    #if not os.path.exists(dest):
    #    os.mkdir(dest)
    for pkg, typ in packages:
        found = False
        for path in site.getsitepackages():
            if not found:
                for entry in os.listdir(path):
                    if entry == pkg:
                        if typ == 'd' and os.path.isdir(os.path.join(path, entry)):
                            shutil.copytree(os.path.join(path, entry), os.path.join(site_dest, entry), ignore=ignore_in_dirs)
                            found = True
                            break
                        else:
                            if os.path.isfile(os.path.join(path, entry)):
                                shutil.copy2(os.path.join(path, entry), os.path.join(site_dest, entry))
                                found = True
                                break
            else:
                break

def ignore_in_dirs(base, items, ignored_dirs=None):
    ans = []
    if ignored_dirs is None:
        ignored_dirs = {'.svn', '.bzr', '.git', 'test', 'tests', 'testing', '__pycache__'}
    for name in items:
        path = os.path.join(base, name)
        if os.path.isdir(path):
            if name in ignored_dirs or not os.path.exists(os.path.join(path, '__init__.py')):
                ans.append(name)
        else:
            if name.rpartition('.')[-1] not in ('so', 'py'):
                ans.append(name)
    return ans

def copy_pylib():
    shutil.copy2(py_lib, app_dir)
    shutil.copy2(py_exe, os.path.join(py_dest, 'bin', "sigil-python3"))


def copy_python():
    
    if not os.path.exists(py_dir):
        os.mkdir(py_dir)

    for x in os.listdir(srcdir):
        y = os.path.join(srcdir, x)
        ext = os.path.splitext(x)[1]
        if os.path.isdir(y) and x not in ('test', 'hotshot', 'distutils',
                'site-packages', 'idlelib', 'lib2to3', 'dist-packages', '__pycache__'):
            shutil.copytree(y, os.path.join(py_dir, x),
                    ignore=ignore_in_dirs)
        if os.path.isfile(y) and ext in ('.py', '.so'):
            shutil.copy2(y, py_dir)

    #site_dest = os.path.join(py_dir, 'site-packages')
    copy_site_packages(site_packages, site_dest)
    create_site_py()
    create_pyvenv()

    for x in os.walk(py_dir):
        for f in x[-1]:
            if f.endswith('.py'):
                y = os.path.join(x[0], f)
                rel = os.path.relpath(y, py_dir)
                try:
                    py_compile.compile(y, cfile=y+'o',dfile=rel, doraise=True, optimize=2)
                    os.remove(y)
                    z = y+'c'
                    if os.path.exists(z):
                        os.remove(z)
                except:
                    print ('Failed to byte-compile', y)

def create_site_py():
    with open(os.path.join(py_dir, 'site.py'), 'wb') as f:
        f.write(bytes(textwrap.dedent('''\
        import sys
        import builtins
        import os
        import _sitebuiltins

        def set_helper():
            builtins.help = _sitebuiltins._Helper()

        def fix_sys_path():
            if os.sep == '/':
                sys.path.append(os.path.join(sys.prefix, "lib",
                                "python" + sys.version[:3],
                                "site-packages"))
            else:
                for path in sys.path:
                    py_ver = "".join(map(str, sys.version_info[:2]))
                    if os.path.basename(path) == "python" + py_ver + ".zip":
                        sys.path.remove(path)
                sys.path.append(os.path.join(sys.prefix, "lib", "site-packages"))

        def main():
            try:
                fix_sys_path()
                set_helper()
            except SystemExit as err:
                if err.code is None:
                    return 0
                if isinstance(err.code, int):
                    return err.code
                print (err.code)
                return 1
            except:
                import traceback
                traceback.print_exc()
            return 1

        if not sys.flags.no_site:
            main()
            '''), 'UTF-8'))

def create_pyvenv():
    with open(os.path.join(py_dest, 'pyvenv.cfg'), 'wb') as f:
        f.write(bytes(textwrap.dedent('''\
        home = %s
        include-system-site-packages = false
        version = 3.4.0
        ''') % pyhome_dir, 'UTF-8'))


if __name__ == '__main__':
    copy_pylib()
    copy_python()
