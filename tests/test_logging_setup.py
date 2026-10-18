import io
import logging
from pathlib import Path
import tempfile
import unittest
from rich.console import Console
from snuwcaption.logging_setup import configure


class LoggingTests(unittest.TestCase):
    def test_console_color_plain_file(self):
        root=logging.getLogger();saved=list(root.handlers);level=root.level
        # Keep test-runner capture handlers alive while temporarily installing ours.
        root.handlers=[]
        try:
            with tempfile.TemporaryDirectory() as folder:
                output=io.StringIO();configure(folder,Console(file=output,force_terminal=True,legacy_windows=False,color_system="truecolor",width=100))
                logging.getLogger('snuwcaption').warning('request rejected | status=403')
                for handler in root.handlers:handler.flush()
                text=(Path(folder)/'caption.log').read_text(encoding='utf-8')
                self.assertNotIn('\x1b',text);self.assertIn('WARNING',text)
                self.assertIn('\x1b[',output.getvalue())
                for handler in root.handlers:handler.close()
        finally:root.handlers=saved;root.setLevel(level)
