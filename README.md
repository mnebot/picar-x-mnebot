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

### Permisos d'àudio a la Raspberry Pi

A la Raspberry Pi, abans d'executar el projecte, cal afegir l'usuari als grups d'àudio i PulseAudio (substitueix `[Usuari]` pel teu nom d'usuari):

```bash
sudo usermod -aG audio,pulse,pulse-access [Usuari]
```

Després d'executar la comanda, tanca sessió i torna a entrar (o reinicia) perquè els canvis tinguin efecte.

### Claus d'API d'OpenAI

Configura el fitxer `keys.py`:

```python
OPENAI_API_KEY = "la-teva-clau-api"

# Opció A: Prompt (recomanat). Crea un Prompt al dashboard a partir de l'assistent.
OPENAI_PROMPT_ID = "pmpt_xxx"

# Opció B: Model + instruccions. Les instruccions es llegeixen de assistents/arnau.txt
OPENAI_MODEL = "gpt-4.1-mini"

# Opció C: Compatibilitat. Usa OPENAI_ASSISTANT_ID; s'usa model per defecte i assistents/arnau.txt
OPENAI_ASSISTANT_ID = "asst_xxx"
```

Ordre de prioritat: `OPENAI_PROMPT_ID` > `OPENAI_MODEL` > `OPENAI_ASSISTANT_ID`.

**Nota**: L'API Assistants (beta) està deprecated. Ara s'utilitza la Responses API. Si tens un assistent antic, crea un Prompt a partir seu al dashboard d'OpenAI i usa `OPENAI_PROMPT_ID`. Altrament, usa `OPENAI_MODEL` amb les instruccions a `assistents/arnau.txt`.

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
- `sounds/`: Fitxers d'àudio per als efectes de so. Per la sardana (cantar i ballar), afegeix `sounds/sardana.wav` (música de sardana instrumental).
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
