"""Colored console, plain private rotating file; no model output logging."""
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel


class PlainFormatter(logging.Formatter):
    def format(self, record):
        line = super().format(record)
        line = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', line)
        return ''.join(c for c in line if c in '\n\t' or ord(c) >= 32)


def configure(root=None, console=None):
    root = Path(root or os.getenv('CAPTION_LOG_DIR', 'runtime/logs'))
    root.mkdir(parents=True, exist_ok=True)
    if os.name == 'posix':root.chmod(0o700)
    path = root/'caption.log'
    file = RotatingFileHandler(path, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    if os.name == 'posix':path.chmod(0o600)
    file.setFormatter(PlainFormatter('%(asctime)s | %(levelname)-7s | %(name)s | %(message)s', '%Y-%m-%d %H:%M:%S'))
    console = console or Console(stderr=True)
    colored = RichHandler(console=console, show_path=False, rich_tracebacks=False, markup=False, log_time_format='%H:%M:%S')
    colored.setFormatter(logging.Formatter('%(message)s'))
    logger=logging.getLogger();logger.setLevel(logging.INFO)
    for handler in list(logger.handlers):logger.removeHandler(handler);handler.close()
    logger.addHandler(colored);logger.addHandler(file)
    for name in ('httpx','httpcore'):logging.getLogger(name).setLevel(logging.WARNING)
    console.print(Panel('SNUWCANVAS  /  CAPTION API',border_style='cyan',expand=False))
