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
    
    def test_actions_dict_exists(self):
        """Test que actions_dict existeix i no està buit"""
        self.assertIsNotNone(actions_dict)
        self.assertIsInstance(actions_dict, dict)
        self.assertGreater(len(actions_dict), 0)
    
    def test_sounds_dict_exists(self):
        """Test que sounds_dict existeix i no està buit"""
        self.assertIsNotNone(sounds_dict)
        self.assertIsInstance(sounds_dict, dict)
        self.assertGreater(len(sounds_dict), 0)
    
    @patch('preset_actions.sleep')
    def test_wave_hands(self, mock_sleep):
        """Test de wave_hands"""
        wave_hands(self.mock_car)
        self.mock_car.reset.assert_called()
        self.mock_car.set_cam_tilt_angle.assert_called()
        self.mock_car.set_dir_servo_angle.assert_called()
    
    @patch('preset_actions.sleep')
    def test_resist(self, mock_sleep):
        """Test de resist"""
        resist(self.mock_car)
        self.mock_car.reset.assert_called()
        self.mock_car.set_cam_tilt_angle.assert_called()
        self.mock_car.set_cam_pan_angle.assert_called()
        self.mock_car.set_dir_servo_angle.assert_called()
        self.mock_car.stop.assert_called()
    
    @patch('preset_actions.sleep')
    def test_act_cute(self, mock_sleep):
        """Test de act_cute"""
        act_cute(self.mock_car)
        self.mock_car.reset.assert_called()
        self.mock_car.set_cam_tilt_angle.assert_called()
        self.mock_car.forward.assert_called()
        self.mock_car.backward.assert_called()
        self.mock_car.stop.assert_called()
    
    @patch('preset_actions.sleep')
    def test_rub_hands(self, mock_sleep):
        """Test de rub_hands"""
        rub_hands(self.mock_car)
        self.mock_car.reset.assert_called()
        self.mock_car.set_dir_servo_angle.assert_called()
    
    @patch('preset_actions.sleep')
    def test_think(self, mock_sleep):
        """Test de think"""
        think(self.mock_car)
        self.mock_car.reset.assert_called()
        self.mock_car.set_cam_pan_angle.assert_called()
        self.mock_car.set_cam_tilt_angle.assert_called()
        self.mock_car.set_dir_servo_angle.assert_called()
    
    @patch('preset_actions.sleep')
    def test_keep_think(self, mock_sleep):
        """Test de keep_think"""
        keep_think(self.mock_car)
        self.mock_car.reset.assert_called()
        self.mock_car.set_cam_pan_angle.assert_called()
        self.mock_car.set_cam_tilt_angle.assert_called()
        self.mock_car.set_dir_servo_angle.assert_called()
    
    @patch('preset_actions.sleep')
    def test_shake_head(self, mock_sleep):
        """Test de shake_head"""
        shake_head(self.mock_car)
        self.mock_car.stop.assert_called()
        self.mock_car.set_cam_pan_angle.assert_called()
    
    @patch('preset_actions.sleep')
    def test_nod(self, mock_sleep):
        """Test de nod"""
        nod(self.mock_car)
        self.mock_car.reset.assert_called()
        self.mock_car.set_cam_tilt_angle.assert_called()
    
    @patch('preset_actions.sleep')
    def test_depressed(self, mock_sleep):
        """Test de depressed"""
        depressed(self.mock_car)
        self.mock_car.reset.assert_called()
        self.mock_car.set_cam_tilt_angle.assert_called()
    
    @patch('preset_actions.sleep')
    def test_twist_body(self, mock_sleep):
        """Test de twist_body"""
        twist_body(self.mock_car)
        self.mock_car.reset.assert_called()
        self.mock_car.set_motor_speed.assert_called()
        self.mock_car.set_cam_pan_angle.assert_called()
        self.mock_car.set_dir_servo_angle.assert_called()
    
    @patch('preset_actions.sleep')
    def test_celebrate(self, mock_sleep):
        """Test de celebrate"""
        celebrate(self.mock_car)
        self.mock_car.reset.assert_called()
        self.mock_car.set_cam_tilt_angle.assert_called()
        self.mock_car.set_dir_servo_angle.assert_called()
        self.mock_car.set_cam_pan_angle.assert_called()
    
    @patch('preset_actions.sleep')
    def test_advance_20cm(self, mock_sleep):
        """Test de advance_20cm"""
        advance_20cm(self.mock_car)
        self.mock_car.reset.assert_called()
        self.mock_car.set_dir_servo_angle.assert_called_with(0)
        self.mock_car.forward.assert_called_with(30)
        self.mock_car.stop.assert_called()
    
    def test_honking(self):
        """Test de honking"""
        honking(self.mock_music)
        self.mock_music.sound_play_threading.assert_called_once()
    
    def test_start_engine(self):
        """Test de start_engine"""
        start_engine(self.mock_music)
        self.mock_music.sound_play_threading.assert_called_once()
    
    def test_actions_are_callable(self):
        """Test que totes les accions són callable"""
        for action_name, action_func in actions_dict.items():
            self.assertTrue(callable(action_func), f"Action '{action_name}' no és callable")
    
    def test_sounds_are_callable(self):
        """Test que tots els sons són callable"""
        for sound_name, sound_func in sounds_dict.items():
            self.assertTrue(callable(sound_func), f"Sound '{sound_name}' no és callable")
    
    def test_actions_dict_keys(self):
        """Test que actions_dict conté les claus esperades"""
        expected_keys = ["shake head", "nod", "wave hands", "resist", "act cute", 
                        "rub hands", "think", "twist body", "celebrate", 
                        "depressed", "advance", "avanci", "forward 20cm"]
        for key in expected_keys:
            self.assertIn(key, actions_dict, f"Key '{key}' no està a actions_dict")
    
    def test_sounds_dict_keys(self):
        """Test que sounds_dict conté les claus esperades"""
        expected_keys = ["honking", "start engine"]
        for key in expected_keys:
            self.assertIn(key, sounds_dict, f"Key '{key}' no està a sounds_dict")


if __name__ == '__main__':
    unittest.main()

