"""
Tests unitaris per a preset_actions.py
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Afegir el directori pare al path per poder importar els mòduls
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from preset_actions import (
    actions_dict, sounds_dict,
    wave_hands, resist, act_cute, rub_hands, think, keep_think,
    shake_head, nod, depressed, twist_body, celebrate,
    honking, start_engine, advance_20cm
)


class TestPresetActions(unittest.TestCase):
    """Tests per a les accions predefinides"""
    
    def setUp(self):
        """Configuració inicial per a cada test"""
        self.mock_car = Mock()
        self.mock_music = Mock()
    
    def test_actions_are_callable(self):
        """Test que totes les accions són callable"""
        for action_name, action_func in actions_dict.items():
            self.assertTrue(callable(action_func), f"Action '{action_name}' no és callable")
    
    def test_sounds_are_callable(self):
        """Test que tots els sons són callable"""
        for sound_name, sound_func in sounds_dict.items():
            self.assertTrue(callable(sound_func), f"Sound '{sound_name}' no és callable")


if __name__ == '__main__':
    unittest.main()
