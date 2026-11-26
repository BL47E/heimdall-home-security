#!/usr/bin/env python3
"""Keep the dashboard bound to the current Tailscale IPv4 address."""
import ipaddress
import select
import signal
import socket
import subprocess
import sys
import time


def dashboard_address():
    try:
        result = subprocess.run(['tailscale', 'ip', '-4'], capture_output=True,
                                text=True, timeout=2, check=True)
        address = ipaddress.IPv4Address(result.stdout.strip())
        if address in ipaddress.IPv4Network('100.64.0.0/10'):
            return str(address)
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return '127.0.0.1'


def address_events():
    # Linux sends notifications as soon as an interface or IPv4 address changes.
    try:
        listener = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, socket.NETLINK_ROUTE)
        listener.bind((0, 0x1 | 0x10))  # RTMGRP_LINK | RTMGRP_IPV4_IFADDR
        listener.setblocking(False)
        return listener
    except (AttributeError, OSError):
        return None


def stop_dashboard(process):
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main():
    running = True

    def stop(_signum, _frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    listener = address_events()
    process = None
    address = None
    try:
        while running:
            current = dashboard_address()
            if current != address:
                stop_dashboard(process)
                address = current
                print(f'Starting dashboard at http://{address}:8765', flush=True)
                process = subprocess.Popen([sys.argv[1], 'dashboard', '--host', address,
                                            '--port', '8765'])
            elif process is not None and process.poll() is not None:
                return process.returncode or 1
            # A short periodic check also catches Tailscale daemon state changes
            # that do not generate a kernel address notification.
            if listener:
                readable, _, _ = select.select([listener], [], [], 1)
                if readable:
                    try:
                        listener.recv(65536)
                    except BlockingIOError:
                        pass
            else:
                time.sleep(1)
    finally:
        stop_dashboard(process)
        if listener:
            listener.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
