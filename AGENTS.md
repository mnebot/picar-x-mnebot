# AGENTS.md

## Project overview
- Python project for controlling a SunFounder Picar-X robot with voice, vision,
  and OpenAI Assistant integration (responses in Catalan by default).
- Entry point: `gpt_car.py`.
- Key modules: `openai_helper.py`, `preset_actions.py`, `utils.py`,
  `visual_tracking.py`.
- Tests live under `tests/` and are designed to mock external services
  (OpenAI, hardware, audio, camera).

## Local setup (developer machine)
- Python 3.11+ recommended.
- Hardware/robot dependencies (not needed for tests):
  `robot_hat`, `vilib`, `sunfounder_controller`, `picarx`.
- OpenAI credentials are expected in `keys.py` for runtime usage.

## Running tests
```bash
python3 -m pip install pytest pytest-cov
python3 -m pytest
```

Common variants:
```bash
python3 -m pytest tests/test_openai_helper.py -v
python3 -m pytest tests/ --cov=. --cov-report=html
```

## Agent notes
- Avoid running `gpt_car.py` in CI or headless environments; it requires robot
  hardware, audio devices, and OpenAI credentials.
- Prefer mocking hardware and external APIs when adding tests.
