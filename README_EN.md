# Arnau-X

This project is a fork of the original [SunFounder Picar-X project](https://github.com/sunfounder/picar-x) that adds artificial intelligence functionality to control the Picar-X robot through voice and vision.

**Read this in [Catalan](README.md)**

## Original Project

This project is based on the original SunFounder project:
- **Original repository**: <https://github.com/sunfounder/picar-x>
- **Original documentation**: <https://docs.sunfounder.com/projects/picar-x-v20/en/latest/>
- **Robot Hat**: <https://docs.sunfounder.com/projects/robot-hat-v4/en/latest/>

## Features

This fork extends GPT functions to the Picar-X robot and is under active development. The objectives are:

- **Voice control**: Voice recognition in Catalan using Speech Recognition
- **Artificial intelligence**: Integration with OpenAI Assistant to process natural commands
- **Text-to-Speech**: Synthetic voice generation in Catalan
- **Computer vision**: Real-time image processing with person detection, near-term goal: follow you like a puppy.
- **Visual tracking**: Ability to track objects with the camera
- **Emotion recognition**: Plans to introduce a screen to react to detected emotions, recognize people and interact differently with each person using an OpenAI assistant with different personalities.

## Requirements

- Raspberry Pi with SunFounder Picar-X robot
- Python 3.11+
- Original Picar-X libraries:
  - `robot_hat`
  - `vilib`
  - `sunfounder_controller`
  - `picarx`

To install the original dependencies, see the [official documentation](https://docs.sunfounder.com/projects/picar-x-v20/en/latest/python/python_start/install_all_modules.html).

## Installation

```bash
git clone https://github.com/mnebot/picar-x-mnebot.git
cd picar-x-mnebot
pip install -r requirements.txt
```

## Configuration

Before running the project, you need to configure the OpenAI API keys in the `keys.py` file:

```python
OPENAI_API_KEY = "your-api-key"
OPENAI_ASSISTANT_ID = "your-assistant-id"
```

### Creating an OpenAI Assistant

To create an OpenAI Assistant, you have two options:

#### Option 1: Using OpenAI's web dashboard (recommended)

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign in with your OpenAI account
3. Navigate to **Assistants** in the sidebar menu
4. Click **Create assistant** or **+ Create**
5. Configure the assistant:
   - **Name**: Give it a descriptive name (e.g., "Arnau-X Robot")
   - **Instructions**: Add instructions on how the assistant should behave. For example:
     ```
     You are an assistant to control a Picar-X robot. Always respond in Catalan.
     You can control the robot with actions like: move head, raise hands, move forward, etc.
     ```
   - **Model**: Select a model (e.g., `gpt-4` or `gpt-3.5-turbo`)
   - **Tools**: Optionally, add functions or other tools if needed
6. Click **Save**
7. Copy the **Assistant ID** that appears at the top of the assistant page
8. Paste this ID into the `keys.py` file as `OPENAI_ASSISTANT_ID`

#### Option 2: Using the OpenAI API

You can also create an assistant programmatically using the OpenAI API:

```python
from openai import OpenAI

client = OpenAI(api_key="your-api-key")

assistant = client.beta.assistants.create(
    name="Arnau-X Robot",
    instructions="You are an assistant to control a Picar-X robot. Always respond in Catalan.",
    model="gpt-4",
)

print(f"Assistant ID: {assistant.id}")
```

Copy the `assistant.id` and use it as `OPENAI_ASSISTANT_ID` in the `keys.py` file.

**Note**: You will need a valid OpenAI API key. You can get one at [OpenAI API Keys](https://platform.openai.com/api-keys).

## Usage

Run the robot with voice and vision control:

```bash
python3 gpt_car.py
```

Available options:
- `--keyboard`: Use keyboard input instead of voice
- `--no-img`: Disable image processing

## Project Structure

- `gpt_car.py`: Main file that manages the robot and OpenAI integration
- `openai_helper.py`: Helper class to interact with the OpenAI API
- `preset_actions.py`: Predefined robot actions (movements, gestures, sounds)
- `utils.py`: Auxiliary functions (TTS, sound processing, etc.)
- `visual_tracking.py`: Visual tracking functionality
- `sounds/`: Audio files for sound effects
- `tests/`: Project unit tests

## Tests

To run the tests:

```bash
python3 -m pytest tests/ -v
```

With coverage:

```bash
python3 -m pytest tests/ --cov=. --cov-report=html
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Credits

- **Original project**: SunFounder (<https://www.sunfounder.com/>)
- **Fork and improvements**: Marçal Nebot (<https://github.com/mnebot>)

## Contact

For questions about this fork, open an issue in the repository.

