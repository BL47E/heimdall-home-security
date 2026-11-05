#!/usr/bin/env python3
"""Hold an OS advisory lock across exec; the OS releases it after a crash."""
import fcntl
import os
import sys
import time

path, marker, wait, *command = sys.argv[1:]
fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
os.fchmod(fd, 0o600)
deadline = time.monotonic() + float(wait)
while True:
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        break
    except BlockingIOError:
        if time.monotonic() >= deadline:
            sys.exit("Heimdall operation is already active; lock wait expired")
        time.sleep(0.05)
# A fixed descriptor lets the shell close this lock in an independent journal
# reader. Otherwise an orphaned child could keep a crashed monitor's lock alive.
if fd != 9:
    os.dup2(fd, 9)
    os.close(fd)
os.set_inheritable(9, True)
os.environ[marker] = str(os.getpid())
os.execv(command[0], command)
