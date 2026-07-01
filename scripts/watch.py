# -*- coding: utf-8 -*-
"""Watch portfolio.html and rebuild the status dashboard on change."""
import argparse
import atexit
import ctypes
import os
import subprocess
import sys
import time
from datetime import datetime

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
PORTFOLIO_DIR = os.path.join(os.path.expanduser('~'), 'Desktop', 'פרויקטים', 'תיק עבודות')
PORTFOLIO = os.path.join(PORTFOLIO_DIR, 'portfolio.html')
BUILD_SCRIPT = os.path.join(SCRIPTS_DIR, 'build.py')
NETLIFY_DIR = os.path.join(PORTFOLIO_DIR, 'portfolio-git-temp')
NETLIFY_URL = 'https://storied-alfajores-6f10d2.netlify.app/status-dashboard.html'
NETLIFY_SITE = '3276a480-932a-403f-8abe-07f7c9bfb3b0'
PID_FILE = os.path.join(PROJECT_DIR, '.watch.pid')
DEFAULT_LOG = os.path.join(PROJECT_DIR, 'סנכרון.log')

DEFAULT_DEBOUNCE = 2.0
DEFAULT_POLL = 1.0

_LOG_PATH = None


def log(msg):
    line = f'[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}'
    if _LOG_PATH:
        with open(_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    else:
        print(line, flush=True)


def _pid_alive(pid):
    if sys.platform != 'win32':
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
    if handle:
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    return False


def acquire_lock():
    if os.path.isfile(PID_FILE):
        try:
            old = int(open(PID_FILE, encoding='utf-8').read().strip())
            if old != os.getpid() and _pid_alive(old):
                return False
        except (ValueError, OSError):
            pass
    with open(PID_FILE, 'w', encoding='utf-8') as f:
        f.write(str(os.getpid()))
    return True


def release_lock():
    if not os.path.isfile(PID_FILE):
        return
    try:
        if int(open(PID_FILE, encoding='utf-8').read().strip()) == os.getpid():
            os.remove(PID_FILE)
    except (ValueError, OSError):
        pass


def run_build():
    log('portfolio.html changed — building...')
    result = subprocess.run([sys.executable, BUILD_SCRIPT], cwd=PROJECT_DIR,
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.stdout:
        for line in result.stdout.strip().splitlines():
            log(line)
    if result.returncode != 0:
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                log('ERR ' + line)
        log(f'build failed (exit {result.returncode})')
        return False
    log('build OK')
    return True


def run_deploy():
    if not os.path.isdir(NETLIFY_DIR):
        log(f'missing netlify dir: {NETLIFY_DIR}')
        return False
    status = subprocess.run(['git', 'status', '--porcelain', 'status-dashboard.html'],
                            cwd=NETLIFY_DIR, capture_output=True, text=True)
    if not status.stdout.strip():
        log('no netlify changes — skip deploy')
        return True
    for cmd in (
        ['git', 'add', 'status-dashboard.html'],
        ['git', 'commit', '-m', 'auto: status dashboard sync'],
        ['git', 'push', 'origin', 'main'],
        ['netlify', 'deploy', '--prod', '--dir', '.', '--site', NETLIFY_SITE],
    ):
        result = subprocess.run(cmd, cwd=NETLIFY_DIR)
        if result.returncode != 0:
            log(f'deploy step failed: {" ".join(cmd)}')
            return False
    log(f'published: {NETLIFY_URL}')
    return True


def watch_loop(debounce, poll, deploy):
    if not os.path.isfile(PORTFOLIO):
        log(f'missing portfolio: {PORTFOLIO}')
        return 1

    log(f'watching: {PORTFOLIO}')
    log(f'debounce {debounce}s · poll {poll}s · deploy={"on" if deploy else "off"}')

    last_mtime = os.path.getmtime(PORTFOLIO)
    changed_at = 0.0

    try:
        while True:
            time.sleep(poll)
            try:
                mtime = os.path.getmtime(PORTFOLIO)
            except OSError:
                continue

            if mtime != last_mtime:
                last_mtime = mtime
                changed_at = time.time()
            elif changed_at and (time.time() - changed_at) >= debounce:
                changed_at = 0.0
                if run_build() and deploy:
                    run_deploy()
    except KeyboardInterrupt:
        log('stopped')
        return 0


def main():
    global _LOG_PATH

    parser = argparse.ArgumentParser(description='Auto-rebuild status dashboard when portfolio.html changes')
    parser.add_argument('--initial', action='store_true', help='build once before watching')
    parser.add_argument('--deploy', action='store_true', help='git push + netlify deploy after each build')
    parser.add_argument('--debounce', type=float, default=DEFAULT_DEBOUNCE, help='seconds to wait after last change')
    parser.add_argument('--poll', type=float, default=DEFAULT_POLL, help='poll interval in seconds')
    parser.add_argument('--log', nargs='?', const=DEFAULT_LOG, default=None,
                        help='append log to file (default: סנכרון.log)')
    parser.add_argument('--allow-multiple', action='store_true', help='skip single-instance lock')
    args = parser.parse_args()

    _LOG_PATH = args.log
    if _LOG_PATH:
        os.makedirs(os.path.dirname(_LOG_PATH) or '.', exist_ok=True)

    if not args.allow_multiple:
        if not acquire_lock():
            log('watch already running — exit')
            return 0
        atexit.register(release_lock)

    if args.initial:
        if not run_build():
            return 1
        if args.deploy:
            run_deploy()

    return watch_loop(args.debounce, args.poll, args.deploy)


if __name__ == '__main__':
    raise SystemExit(main())