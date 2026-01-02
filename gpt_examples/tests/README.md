# Tests Unitaris

Aquest directori conté els tests unitaris per al projecte picar-x-mnebot.

## Executar els tests

### Amb pytest (recomanat)

```bash
# Instal·lar dependències de test
python3 -m pip install pytest pytest-cov

# Executar tots els tests (des del directori gpt_examples)
python3 -m pytest tests/ -v

# Executar amb cobertura
python3 -m pytest tests/ --cov=. --cov-report=html

# Executar un fitxer específic
python3 -m pytest tests/test_openai_helper.py -v

# Executar amb verbositat
python3 -m pytest tests/ -v
```

**Nota**: A Windows, si `pytest` no està al PATH, cal usar `python3 -m pytest` en lloc de només `pytest`.

### Amb unittest (estàndard)

```bash
# Executar tots els tests
python -m unittest discover tests

# Executar un fitxer específic
python -m unittest tests.test_openai_helper
```

## Estructura

- `test_openai_helper.py`: Tests per a `openai_helper.py`
- `test_utils.py`: Tests per a `utils.py`
- `test_visual_tracking.py`: Tests per a `visual_tracking.py`
- `test_gpt_car.py`: Tests per a `gpt_car.py`

## Cobertura

L'objectiu és assolir una cobertura mínima del 70% segons el pla de millores.

Per veure la cobertura:
```bash
python3 -m pytest tests/ --cov=. --cov-report=html
# Obrir htmlcov/index.html al navegador
```

## Notes

- Els tests utilitzen mocks per a dependències externes (OpenAI, hardware, etc.)
- Els tests són independents i repetibles
- No requereixen hardware real per executar-se

