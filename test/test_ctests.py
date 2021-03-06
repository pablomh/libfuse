#!/usr/bin/env python3

if __name__ == '__main__':
    import pytest
    import sys
    sys.exit(pytest.main([__file__] + sys.argv[1:]))

import subprocess
import pytest
import platform
from distutils.version import LooseVersion
from util import (wait_for_mount, umount, cleanup, base_cmdline,
                  safe_sleep, basename, fuse_test_marker)
from os.path import join as pjoin

pytestmark = fuse_test_marker()

@pytest.mark.parametrize("writeback", (False, True))
def test_write_cache(tmpdir, writeback):
    if writeback and LooseVersion(platform.release()) < '3.14':
        pytest.skip('Requires kernel 3.14 or newer')
    # This test hangs under Valgrind when running close(fd)
    # test_write_cache.c:test_fs(). Most likely this is because of an internal
    # deadlock in valgrind, it probably assumes that until close() returns,
    # control does not come to the program.
    mnt_dir = str(tmpdir)
    cmdline = [ pjoin(basename, 'test', 'test_write_cache'),
                mnt_dir ]
    if writeback:
        cmdline.append('-owriteback_cache')
    subprocess.check_call(cmdline)


@pytest.mark.parametrize("name",
                         ('notify_inval_inode',
                          'notify_store_retrieve'))
@pytest.mark.parametrize("notify", (True, False))
def test_notify1(tmpdir, name, notify):
    mnt_dir = str(tmpdir)
    cmdline = base_cmdline + \
              [ pjoin(basename, 'example', name),
                '-f', '--update-interval=1', mnt_dir ]
    if not notify:
        cmdline.append('--no-notify')
    mount_process = subprocess.Popen(cmdline)
    try:
        wait_for_mount(mount_process, mnt_dir)
        filename = pjoin(mnt_dir, 'current_time')
        with open(filename, 'r') as fh:
            read1 = fh.read()
        safe_sleep(2)
        with open(filename, 'r') as fh:
            read2 = fh.read()
        if notify:
            assert read1 != read2
        else:
            assert read1 == read2
    except:
        cleanup(mnt_dir)
        raise
    else:
        umount(mount_process, mnt_dir)

    
