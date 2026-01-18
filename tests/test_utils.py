"""
Tests unitaris per a utils.py
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tempfile

# Afegir el directori pare al path per poder importar els mòduls
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    print_color, gray_print, warn, error,
    redirect_error_2_null, cancel_redirect_error,
    run_command, sox_volume, speak_block
)


class TestPrintFunctions(unittest.TestCase):
    """Tests per a les funcions de print"""
    pass


class TestRedirectError(unittest.TestCase):
    """Tests per a les funcions de redirecció d'errors"""
    pass


class TestRunCommand(unittest.TestCase):
    """Tests per a run_command"""
    pass


class TestSoxVolume(unittest.TestCase):
    """Tests per a sox_volume"""
    pass


class TestSpeakBlock(unittest.TestCase):
    """Tests per a speak_block"""
    pass


class TestPrintColorVariations(unittest.TestCase):
    """Tests addicionals per a print_color amb diferents paràmetres"""
    pass


if __name__ == '__main__':
    unittest.main()
