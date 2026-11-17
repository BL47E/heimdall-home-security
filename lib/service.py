#!/usr/bin/env python3
"""Read and control only the fixed, identity-checked system monitor unit.

No privilege escalation: systemctl is always noninteractive. Missing systemd
keeps the standalone CLI useful; an unreadable or mismatched unit fails closed.
"""
import pwd
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

UNIT = 'heimdall-monitor.service'
PROPERTIES = ('LoadState', 'ActiveState', 'SubState', 'MainPID',
              'WorkingDirectory', 'Environment', 'ExecStart', 'User')


def call(*args, timeout=1):
    return subprocess.run(['systemctl', '--system', '--no-ask-password', *args],
                          capture_output=True, text=True, timeout=timeout)


def service_owned_pid(data):
    try:
        pid = json.loads((data / 'state.json').read_text()).get('monitor', {}).get('pid')
        if not isinstance(pid, int) or pid <= 0:
            return False
        return any(line.rstrip().endswith('/' + UNIT) for line in Path(f'/proc/{pid}/cgroup').read_text().splitlines())
    except (OSError, ValueError, TypeError):
        return False


def in_monitor_service():
    """The helper inherits the foreground shell's kernel-assigned cgroup."""
    try:
        return any(line.rstrip().endswith('/' + UNIT)
                   for line in Path('/proc/self/cgroup').read_text().splitlines())
    except OSError:
        return False


def inspect(root, data):
    selection = os.environ.get('HEIMDALL_MONITOR_MANAGER', 'auto')
    if selection not in ('auto', 'standalone', 'systemd'):
        return {'manager': 'unavailable', 'error': 'HEIMDALL_MONITOR_MANAGER must be auto, standalone or systemd'}
    missing = not shutil.which('systemctl')
    if not missing:
        try:
            result = call('show', '--no-pager', '--property=' + ','.join(PROPERTIES), UNIT)
        except (OSError, subprocess.TimeoutExpired):
            return {'manager': 'unavailable', 'unit': UNIT, 'error': 'Cannot inspect monitor service; check systemctl access'}
        pairs = [line.split('=', 1) for line in result.stdout.splitlines() if '=' in line]
        props = dict(pairs)
        if len(props) != len(pairs):
            return {'manager': 'unavailable', 'unit': UNIT, 'error': 'Ambiguous monitor service properties; refusing control'}
        missing = props.get('LoadState') == 'not-found'
        if result.returncode and not missing:
            # A systemctl executable alone does not mean this host runs systemd.
            missing = ('System has not been booted with systemd' in result.stderr or
                       'Failed to connect to bus: No such file or directory' in result.stderr)
            if not missing:
                return {'manager': 'unavailable', 'unit': UNIT, 'error': 'Cannot inspect monitor service; check systemctl access'}
    if missing:
        if service_owned_pid(data) or in_monitor_service():
            return {'manager': 'unavailable', 'unit': UNIT, 'error': 'Monitor process belongs to systemd but service inspection is unavailable'}
        if selection == 'systemd':
            return {'manager': 'unavailable', 'unit': UNIT, 'error': 'Requested systemd monitor service is unavailable'}
        return {'manager': 'standalone'}
    info = {'manager': 'systemd', 'unit': UNIT,
            'active_state': props.get('ActiveState', 'unknown'),
            'sub_state': props.get('SubState', 'unknown'),
            'main_pid': int(props.get('MainPID', '0')) if props.get('MainPID', '0').isdigit() else 0}
    try:
        env_items = shlex.split(props.get('Environment', ''))
        if any(not re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', item) for item in env_items):
            raise ValueError('Malformed service environment')
        env_pairs = [item.split('=', 1) for item in env_items]
        environment = dict(env_pairs)
        if len(environment) != len(env_pairs):
            raise ValueError('Ambiguous service environment')
        # systemctl show renders ExecStart as a structured, escaped property.
        # Accept only our single fixed invocation; unfamiliar escaping fails safe.
        executable = str(root / 'bin/heimdall')
        command = props.get('ExecStart', '')
        path_match = re.search(r'(?:^|[ {;])path=([^;]+?)\s*;', command)
        argv_match = re.search(r'(?:^|[ {;])argv\[\]=([^;]+?)\s*;', command)
        identity = (props.get('LoadState') == 'loaded' and
                    Path(props.get('WorkingDirectory', '')).resolve() == root and
                    Path(environment.get('HEIMDALL_DATA_DIR', '')).resolve() == data and
                    'HEIMDALL_DATA_DIR' in environment and
                    props.get('User') == pwd.getpwuid(os.geteuid()).pw_name and
                    path_match is not None and path_match.group(1) == executable and
                    argv_match is not None and shlex.split(argv_match.group(1)) == [executable, 'monitor', 'run'] and
                    command.count('argv[]=') == 1 and
                    len(re.findall(r'(?:^|[ {;])path=', command)) == 1)
    except (ValueError, OSError):
        identity = False
    if not identity:
        info.update(manager='unavailable', error='Monitor service identity does not match this release, data directory and owner; inspect the installed unit before controlling it')
    elif selection == 'standalone':
        info.update(manager='unavailable', error='Installed monitor service owns this source; use auto or systemd instead of standalone')
    return info


def main():
    root, data = (Path(value).resolve() for value in sys.argv[1:3])
    action = sys.argv[3]
    info = inspect(root, data)
    if action == 'check-run':
        # A service can be starting before MainPID appears in systemctl show.
        # Validate its identity and actual cgroup, never an inherited env marker.
        if info['manager'] == 'unavailable' or (info['manager'] == 'systemd' and not in_monitor_service()):
            print('HEIMDALL_SERVICE_CONTROL: ' + info.get('error',
                  f'Installed monitor service owns this source; run sudo systemctl start {UNIT} instead of monitor run'), file=sys.stderr)
            return 77
    elif action in ('start', 'stop'):
        if info['manager'] != 'systemd':
            print('HEIMDALL_SERVICE_CONTROL: ' + info.get('error', 'Service control requires the systemd manager'), file=sys.stderr)
            return 77
        try:
            result = call(action, UNIT, timeout=4)
        except (OSError, subprocess.TimeoutExpired):
            result = None
        if result is None or result.returncode:
            print(f'HEIMDALL_SERVICE_CONTROL: Cannot complete {action} for {UNIT}; the request failed or timed out. Administrator inspection may be required. In the VM console, run: sudo systemctl {action} {UNIT}. Then refresh status. No process fallback was attempted.', file=sys.stderr)
            return 77
        info = inspect(root, data)
        expected = 'active' if action == 'start' else 'inactive'
        if info['manager'] != 'systemd' or info.get('active_state') != expected:
            print(f'HEIMDALL_SERVICE_CONTROL: Service {action} did not reach {expected}; inspect sudo systemctl status {UNIT} and refresh status.', file=sys.stderr)
            return 77
    elif action != 'inspect':
        print('Unknown service operation', file=sys.stderr)
        return 1
    print(json.dumps(info))
    return 0


if __name__ == '__main__':
    sys.exit(main())
