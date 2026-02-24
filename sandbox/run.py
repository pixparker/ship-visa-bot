"""
One-command sandbox launcher.

By default runs in standalone mode (one process, no Telegram bot).
Use SANDBOX_WITH_BOT=1 to run server + bot process (two processes).

Usage (from the ship-visa-bot directory):
    python -m sandbox.run              # standalone
    SANDBOX_WITH_BOT=1 python -m sandbox.run   # with bot process
"""

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent  # ship-visa-bot/


def main() -> None:
    venv_python = ROOT / '.venv' / 'bin' / 'python'
    python = str(venv_python) if venv_python.exists() else sys.executable

    with_bot = os.getenv('SANDBOX_WITH_BOT', '').strip() in ('1', 'true', 'yes')

    # ── 1. Start sandbox server ──────────────────────────────────────────
    server_env = {**os.environ}
    if not with_bot:
        server_env['SANDBOX_STANDALONE'] = '1'
    print('▶ Starting sandbox server …' + (' (standalone)' if not with_bot else ''))
    server = subprocess.Popen(
        [python, '-m', 'sandbox.server'],
        cwd=str(ROOT),
        env=server_env,
    )

    time.sleep(1.2)

    if not with_bot:
        print()
        print('=' * 52)
        print('  🌐  Open:  http://localhost:8888')
        print(f'  Server PID: {server.pid}  (standalone — no bot process)')
        print('  Press Ctrl+C to stop.')
        print('=' * 52)
        print()
        try:
            server.wait()
        except KeyboardInterrupt:
            print('\n⏹ Shutting down …')
            server.terminate()
            server.wait()
            print('Done.')
        return

    # ── 2. Start bot in sandbox mode ─────────────────────────────────────
    bot_env = {**os.environ, 'SANDBOX_MODE': '1'}
    print('▶ Starting bot in sandbox mode …')
    bot = subprocess.Popen(
        [python, 'bot.py'],
        cwd=str(ROOT),
        env=bot_env,
    )

    print()
    print('=' * 52)
    print('  🌐  Open:  http://localhost:8888')
    print(f'  Server PID: {server.pid}   Bot PID: {bot.pid}')
    print('  Press Ctrl+C to stop both processes.')
    print('=' * 52)
    print()

    try:
        bot.wait()
    except KeyboardInterrupt:
        print('\n⏹ Shutting down …')
        bot.terminate()
        server.terminate()
        bot.wait()
        server.wait()
        print('Done.')


if __name__ == "__main__":
    main()
