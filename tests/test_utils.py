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
    
    @patch('builtins.print')
    def test_print_color(self, mock_print):
        """Test de print_color"""
        print_color("test", color='1;30')
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        self.assertIn('\033[1;30m', call_args)
        self.assertIn('test', call_args)
        self.assertIn('\033[0m', call_args)
    
    @patch('builtins.print')
    def test_gray_print(self, mock_print):
        """Test de gray_print"""
        gray_print("test message")
        mock_print.assert_called_once()
    
    @patch('builtins.print')
    def test_warn(self, mock_print):
        """Test de warn"""
        warn("warning message")
        mock_print.assert_called_once()
    
    @patch('builtins.print')
    def test_error(self, mock_print):
        """Test de error"""
        error("error message")
        mock_print.assert_called_once()


class TestRedirectError(unittest.TestCase):
    """Tests per a les funcions de redirecció d'errors"""
    
    @patch('utils.os.open')
    @patch('utils.os.dup')
    @patch('utils.os.dup2')
    @patch('utils.os.close')
    @patch('utils.sys.stderr')
    def test_redirect_error_2_null(self, mock_stderr, mock_close, mock_dup2, mock_dup, mock_open):
        """Test de redirect_error_2_null"""
        mock_open.return_value = 999
        mock_dup.return_value = 888
        
        result = redirect_error_2_null()
        
        self.assertEqual(result, 888)
        mock_open.assert_called_once()
        mock_dup.assert_called_once_with(2)
        mock_dup2.assert_called_once()
    
    @patch('utils.os.dup2')
    @patch('utils.os.close')
    def test_cancel_redirect_error(self, mock_close, mock_dup2):
        """Test de cancel_redirect_error"""
        old_stderr = 888
        cancel_redirect_error(old_stderr)
        
        mock_dup2.assert_called_once_with(old_stderr, 2)
        mock_close.assert_called_once_with(old_stderr)


class TestRunCommand(unittest.TestCase):
    """Tests per a run_command"""
    
    @patch('subprocess.Popen')
    def test_run_command_success(self, mock_popen):
        """Test de run_command amb èxit"""
        mock_process = Mock()
        mock_process.poll.return_value = 0
        mock_process.stdout.read.return_value = b"test output"
        mock_popen.return_value = mock_process
        
        status, result = run_command("echo test")
        
        self.assertEqual(status, 0)
        self.assertEqual(result, "test output")
        mock_popen.assert_called_once()
    
    @patch('subprocess.Popen')
    def test_run_command_failure(self, mock_popen):
        """Test de run_command amb fallo"""
        mock_process = Mock()
        mock_process.poll.return_value = 1
        mock_process.stdout.read.return_value = b"error output"
        mock_popen.return_value = mock_process
        
        status, result = run_command("invalid command")
        
        self.assertEqual(status, 1)
        self.assertEqual(result, "error output")


class TestSoxVolume(unittest.TestCase):
    """Tests per a sox_volume"""
    
    @patch.dict('sys.modules', {'sox': MagicMock()})
    def test_sox_volume_success(self):
        """Test de sox_volume amb èxit"""
        # Mock del mòdul sox
        mock_sox_module = sys.modules['sox']
        mock_transformer = Mock()
        mock_sox_module.Transformer.return_value = mock_transformer
        
        result = sox_volume("input.mp3", "output.mp3", 5)
        
        self.assertTrue(result)
        mock_transformer.vol.assert_called_once_with(5)
        mock_transformer.build.assert_called_once_with("input.mp3", "output.mp3")
    
    @patch.dict('sys.modules', {'sox': MagicMock()})
    def test_sox_volume_failure(self):
        """Test de sox_volume amb fallo"""
        # Mock del mòdul sox
        mock_sox_module = sys.modules['sox']
        mock_transformer = Mock()
        mock_transformer.build.side_effect = Exception("Sox error")
        mock_sox_module.Transformer.return_value = mock_transformer
        
        result = sox_volume("input.mp3", "output.mp3", 5)
        
        self.assertFalse(result)


class TestSpeakBlock(unittest.TestCase):
    """Tests per a speak_block"""
    
    @patch('os.geteuid', create=True)
    @patch('utils.run_command')
    @patch('os.path.isfile')
    def test_speak_block_success(self, mock_isfile, mock_run_command, mock_geteuid):
        """Test de speak_block amb èxit"""
        mock_geteuid.return_value = 0  # root
        mock_isfile.return_value = True
        mock_run_command.return_value = (0, "output")  # Retornar (status, result)
        mock_music = Mock()
        
        result = speak_block(mock_music, "test.mp3", 80)
        
        mock_music.sound_play.assert_called_once_with("test.mp3", 80)
        self.assertIsNone(result)  # speak_block no retorna res quan té èxit
    
    @patch('os.geteuid', create=True)
    @patch('utils.run_command')
    @patch('os.path.isfile')
    def test_speak_block_file_not_found(self, mock_isfile, mock_run_command, mock_geteuid):
        """Test de speak_block quan el fitxer no existeix"""
        mock_geteuid.return_value = 0
        mock_isfile.return_value = False
        mock_run_command.return_value = (0, "output")  # Retornar (status, result)
        mock_music = Mock()
        
        result = speak_block(mock_music, "nonexistent.mp3", 80)
        
        self.assertFalse(result)
        mock_music.sound_play.assert_not_called()
    
    @patch('os.geteuid', create=True)
    @patch('utils.run_command')
    @patch('os.path.isfile')
    @patch('utils.warn')
    def test_speak_block_non_root_warning(self, mock_warn, mock_isfile, mock_run_command, mock_geteuid):
        """Test de speak_block quan no s'executa com root"""
        mock_geteuid.return_value = 1000  # No root
        mock_isfile.return_value = True
        mock_run_command.return_value = (0, "output")  # Retornar (status, result)
        mock_music = Mock()
        
        # Resetear speak_first per forçar el warning
        import utils
        utils.speak_first = False
        
        speak_block(mock_music, "test.mp3", 80)
        
        # Hauria de mostrar warning
        mock_warn.assert_called()
        mock_music.sound_play.assert_called_once_with("test.mp3", 80)


class TestPrintColorVariations(unittest.TestCase):
    """Tests addicionals per a print_color amb diferents paràmetres"""
    
    @patch('builtins.print')
    def test_print_color_with_custom_end(self, mock_print):
        """Test de print_color amb end personalitzat"""
        print_color("test", end='', color='1;30')
        mock_print.assert_called_once()
        call_kwargs = mock_print.call_args[1]
        self.assertEqual(call_kwargs['end'], '')
    
    @patch('builtins.print')
    def test_print_color_with_flush(self, mock_print):
        """Test de print_color amb flush"""
        print_color("test", flush=True, color='1;30')
        mock_print.assert_called_once()
        call_kwargs = mock_print.call_args[1]
        self.assertTrue(call_kwargs['flush'])
    
    @patch('builtins.print')
    def test_print_color_empty_color(self, mock_print):
        """Test de print_color sense color"""
        print_color("test", color='')
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        # Hauria de tenir només el text i el reset
        self.assertIn('test', call_args)


if __name__ == '__main__':
    unittest.main()

