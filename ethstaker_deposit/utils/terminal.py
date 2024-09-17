import subprocess
import os
import sys
import shutil
import click


def clear_terminal() -> None:
    if sys.platform == 'win32':
        # Special-case for asyncio pytest on Windows
        if os.getenv("IS_ASYNC_TEST") == "1":
            click.clear()
        elif shutil.which('clear'):
            subprocess.call(['clear'])
        else:
            subprocess.call('cls', shell=True)
    elif sys.platform == 'linux' or sys.platform == 'darwin':
        if shutil.which('tput'):
            subprocess.call(['tput', 'reset'])
        elif shutil.which('reset'):
            subprocess.call(['reset'])
        elif shutil.which('clear'):
            subprocess.call(['clear'])
        else:
            click.clear()
    else:
        click.clear()
