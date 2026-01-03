# Arnau-X

**Read this in [English](README_EN.md)**

Aquest projecte és un fork del projecte original [Picar-X de SunFounder](https://github.com/sunfounder/picar-x) que afegeix funcionalitat d'intel·ligència artificial per controlar el robot Picar-X mitjançant veu i visió.

## Projecte Original

Aquest projecte està basat en el projecte original de SunFounder:
- **Repositori original**: <https://github.com/sunfounder/picar-x>
- **Documentació original**: <https://docs.sunfounder.com/projects/picar-x-v20/en/latest/>
- **Robot Hat**: <https://docs.sunfounder.com/projects/robot-hat-v4/en/latest/>

## Funcionalitats

Aquest fork exté les funcions gpt al robot Picar-X i està en evolució. Els objectius són:

- **Control per veu**: Reconeixement de veu en català mitjançant Speech Recognition
- **Intel·ligència artificial**: Integració amb OpenAI Assistant per processar comandes naturals
- **Text-to-Speech**: Generació de veu sintètica en català
- **Visió per computador**: Processament d'imatges en temps real amb detecció de persones, objectiu pròxim: que et segueixi com un gosset.
- **Seguiment visual**: Capacitat de seguir objectes amb la càmera
- **Reconeixements d'emocions**: Es vol introudir una pantalla per a reaccionar a les emocions que detecti, reconeient a les persones i interactui de forma diferent per a cada persona utilitzant un assistent d'OpenAI amb personalitats diferents. 


## Requisits

- Raspberry Pi amb el robot Picar-X de SunFounder
- Python 3.11+
- Les biblioteques originals de Picar-X:
  - `robot_hat`
  - `vilib`
  - `sunfounder_controller`
  - `picarx`

Per instal·lar les dependències originals, consulta la [documentació oficial](https://docs.sunfounder.com/projects/picar-x-v20/en/latest/python/python_start/install_all_modules.html).

## Instal·lació

```bash
git clone https://github.com/mnebot/picar-x-mnebot.git
cd picar-x-mnebot
pip install -r requirements.txt
```

## Configuració

Abans d'executar el projecte, cal configurar les claus d'API d'OpenAI al fitxer `keys.py`:

```python
OPENAI_API_KEY = "la-teva-clau-api"
OPENAI_ASSISTANT_ID = "el-teu-assistant-id"
```

### Crear un assistent d'OpenAI

Per crear un assistent d'OpenAI, tens dues opcions:

#### Opció 1: Utilitzant el dashboard web d'OpenAI (recomanat)

1. Accedeix a [OpenAI Platform](https://platform.openai.com/)
2. Inicia sessió amb el teu compte d'OpenAI
3. Ves a la secció **Assistants** al menú lateral
4. Fes clic a **Create assistant** o **+ Create**
5. Configura l'assistent:
   - **Name**: Posa un nom descriptiu (per exemple, "Arnau-X Robot")
   - **Instructions**: Afegeix instruccions sobre com ha de comportar-se l'assistent. Per exemple:
     ```
     Ets un assistent per controlar un robot Picar-X. Respon sempre en català.
     Pots controlar el robot amb accions com: moure el cap, aixecar les mans, avançar, etc.
     ```
   - **Model**: Selecciona un model (per exemple, `gpt-4` o `gpt-3.5-turbo`)
   - **Tools**: Opcionalment, afegeix funcions o altres eines si cal
6. Fes clic a **Save**
7. Copia l'**Assistant ID** que apareix a la part superior de la pàgina de l'assistent
8. Pega aquest ID al fitxer `keys.py` com a `OPENAI_ASSISTANT_ID`

#### Opció 2: Utilitzant l'API d'OpenAI

També pots crear un assistent programàticament utilitzant l'API d'OpenAI:

```python
from openai import OpenAI

client = OpenAI(api_key="la-teva-clau-api")

assistant = client.beta.assistants.create(
    name="Arnau-X Robot",
    instructions="Ets un assistent per controlar un robot Picar-X. Respon sempre en català.",
    model="gpt-4",
)

print(f"Assistant ID: {assistant.id}")
```

Copia l'`assistant.id` i utilitza'l com a `OPENAI_ASSISTANT_ID` al fitxer `keys.py`.

**Nota**: Necessitaràs una clau d'API d'OpenAI vàlida. Pots obtenir-la a [OpenAI API Keys](https://platform.openai.com/api-keys).

## Ús

Executar el robot amb control per veu i visió:

```bash
python3 gpt_car.py
```

Opcions disponibles:
- `--keyboard`: Utilitzar entrada per teclat en lloc de veu
- `--no-img`: Desactivar el processament d'imatges

## Estructura del Projecte

- `gpt_car.py`: Fitxer principal que gestiona el robot i la integració amb OpenAI
- `openai_helper.py`: Classe helper per interactuar amb l'API d'OpenAI
- `preset_actions.py`: Accions predefinides del robot (moviments, gestos, sons)
- `utils.py`: Funcions auxiliars (TTS,<> processament de so, etc.)
- `visual_tracking.py`: Funcionalitat de seguiment visual
- `sounds/`: Fitxers d'àudio per als efectes de so
- `tests/`: Tests unitaris del projecte

## Tests

Per executar els tests:

```bash
python3 -m pytest tests/ -v
```

Amb cobertura:

```bash
python3 -m pytest tests/ --cov=. --cov-report=html
```

## Llicència

Aquest projecte està llicenciat sota la llicència MIT. Vegeu el fitxer [LICENSE](LICENSE) per a més detalls.

## Crèdits

- **Projecte original**: SunFounder (<https://www.sunfounder.com/>)
- **Fork i millores**: Marçal Nebot (<https://github.com/mnebot>)

## Contacte

Per a preguntes sobre aquest fork, obre un issue al repositori.
