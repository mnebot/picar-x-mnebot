"""
Tests unitaris per a preset_actions.py
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import importlib.util

# Afegir el directori pare al path per poder importar els mòduls
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _parent_dir)

# Si preset_actions ha estat mockejat per un altre test (ex. test_gpt_car_refactored_functions),
# carregar el mòdul real des del fitxer
_pa = sys.modules.get('preset_actions')
_pa_ok = getattr(_pa, 'actions_dict', None) and 'shake head' in getattr(_pa, 'actions_dict', {})
if not _pa_ok:
    _pa_spec = importlib.util.spec_from_file_location(
        'preset_actions',
        os.path.join(_parent_dir, 'preset_actions.py')
    )
    _pa_module = importlib.util.module_from_spec(_pa_spec)
    sys.modules['preset_actions'] = _pa_module
    _pa_spec.loader.exec_module(_pa_module)

from preset_actions import (
    actions_dict, sounds_dict,
    wave_hands, resist, act_cute, rub_hands, think, keep_think,
    shake_head, nod, depressed, twist_body, celebrate,
    honking, start_engine, advance_20cm, advance_safe, donar_la_volta,
    ballar_sardana, sardana,
    seguir_persona, aturar_seguiment,
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

    def test_seguir_persona_aturar_seguiment_callable(self):
        """Test que seguir_persona i aturar_seguiment són callable (executen start/stop a visual_tracking)."""
        self.assertTrue(callable(seguir_persona))
        self.assertTrue(callable(aturar_seguiment))

    def test_seguir_persona_aturar_seguiment_accepten_car(self):
        """Test que seguir_persona i aturar_seguiment accepten (car) sense llançar"""
        self.mock_car = Mock()
        seguir_persona(self.mock_car)
        aturar_seguiment(self.mock_car)

    def test_actions_dict_inclou_accions_seguiment(self):
        """Test que actions_dict inclou accions de seguiment en català i anglès"""
        seguidors = ("seguir persona", "follow me", "follow")
        aturadors = ("aturar seguiment", "stop following", "stop follow")
        for k in seguidors:
            self.assertIn(k, actions_dict, f"Falta acció '{k}' a actions_dict")
            self.assertIs(actions_dict[k], seguir_persona)
        for k in aturadors:
            self.assertIn(k, actions_dict, f"Falta acció '{k}' a actions_dict")
            self.assertIs(actions_dict[k], aturar_seguiment)

    def test_donar_la_volta_accio_disponible_i_callable(self):
        """Test que 'donar la volta' està al diccionari i es pot cridar amb un mock"""
        self.assertIn("donar la volta", actions_dict)
        self.assertIs(actions_dict["donar la volta"], donar_la_volta)
        donar_la_volta(self.mock_car)
        self.assertGreaterEqual(self.mock_car.reset.call_count, 1)
        self.mock_car.backward.assert_called_once()
        self.mock_car.forward.assert_called_once()
        self.assertGreaterEqual(self.mock_car.set_dir_servo_angle.call_count, 2)

    @patch('preset_actions.sleep')
    def test_ballar_sardana_accio_disponible_i_callable(self, mock_sleep):
        """Test que 'ballar sardana' està al diccionari i es pot cridar amb un mock"""
        self.assertIn("ballar sardana", actions_dict)
        self.assertIn("ballar una sardana", actions_dict)
        self.assertIs(actions_dict["ballar sardana"], ballar_sardana)
        ballar_sardana(self.mock_car)
        self.assertGreaterEqual(self.mock_car.reset.call_count, 1)
        self.assertGreaterEqual(self.mock_car.forward.call_count, 1)
        self.assertGreaterEqual(self.mock_car.set_dir_servo_angle.call_count, 1)

    def test_sardana_so_disponible_i_callable(self):
        """Test que 'sardana' està a sounds_dict i es pot cridar amb un mock"""
        self.assertIn("sardana", sounds_dict)
        self.assertIn("cantar sardana", sounds_dict)
        self.assertIs(sounds_dict["sardana"], sardana)
        sardana(self.mock_music)
        # sense fitxer sounds/sardana.wav no crida sound_play_threading; en test normalment no existeix

    def test_advance_safe_accio_disponible(self):
        """Test que 'advance safe' i 'avanci segur' estan al diccionari"""
        self.assertIn("advance safe", actions_dict)
        self.assertIn("avanci segur", actions_dict)
        self.assertIs(actions_dict["advance safe"], advance_safe)
        self.assertIs(actions_dict["avanci segur"], advance_safe)

    @patch('preset_actions.sleep')
    def test_advance_safe_amb_ultrasonic_avanca_i_atura(self, mock_sleep):
        """Test que advance_safe amb ultrasònic crida forward i stop"""
        mock_car = Mock()
        mock_ultrasonic = Mock()
        mock_ultrasonic.read.side_effect = [50, 30, 25]  # distàncies segures
        mock_car.ultrasonic = mock_ultrasonic
        advance_safe(mock_car)
        mock_car.reset.assert_called_once()
        self.assertGreaterEqual(mock_car.forward.call_count, 1)
        mock_car.stop.assert_called_once()

    @patch('preset_actions.sleep')
    def test_advance_safe_sense_ultrasonic_fa_fallback_a_advance_20cm(self, mock_sleep):
        """Test que advance_safe sense ultrasònic fa fallback a advance_20cm"""
        mock_car = Mock()
        mock_car.ultrasonic = None  # Simula absència d'ultrasònic
        advance_safe(mock_car)
        # reset cridat 2 vegades: advance_safe i advance_20cm
        self.assertGreaterEqual(mock_car.reset.call_count, 1)
        mock_car.forward.assert_called_once_with(30)
        mock_car.stop.assert_called_once()

    @patch('preset_actions.sleep')
    def test_advance_safe_atura_quan_obstacle_proper(self, mock_sleep):
        """Test que advance_safe s'atura abans d'hora quan read() retorna distància < 22 cm"""
        mock_car = Mock()
        mock_ultrasonic = Mock()
        mock_ultrasonic.read.side_effect = [50, 15]  # segon read: obstacle
        mock_car.ultrasonic = mock_ultrasonic
        advance_safe(mock_car)
        mock_car.stop.assert_called_once()
        # Hauria d'haver avançat poques vegades (1-2 passos abans de detectar obstacle)
        self.assertLessEqual(mock_car.forward.call_count, 3)


if __name__ == '__main__':
    unittest.main()
