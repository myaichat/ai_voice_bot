
# AI Voice Bot

This project is an AI-powered voice bot built using OpenAI's Realtime API. It allows for real-time voice interaction through a command-line interface (CLI) and can be modified to handle text output, as well as include a mocked version for cost-effective testing.

## Project Structure

- `ai_voice_bot/`: Contains the main implementation of the voice bot.
```
├───ai_voice_bot
│   ├───client
│   │   └───__pycache__
│   ├───handlers
│   │   └───__pycache__
│   ├───mock
│   │   └───__pycache__
│   └───__pycache__
```
- `misc/`: Directory for miscellaneous files.
- `.gitignore`: Specifies which files should be ignored by Git.
- `LICENSE`: The project's license file.
- `README.md`: The README file that you're reading right now.
- `install.bat`: A batch script for setting up the environment.
- `mock_bot.py`: A mock version of the bot for testing without using the API.
- `push.bat`: A batch script for pushing changes to GitHub.
- `setup.py`: The setup script for packaging and distributing the project.
- `text_bot.py`: The script for handling text-based output from the bot.
- `voice_bot.py`: The script for handling voice-based interaction.

## Features

- **Voice Interaction**: The bot supports real-time voice input and can generate real-time responses using OpenAI's Realtime API.
- **Text-Based Interaction**: You can modify the bot to handle text input and output instead of voice, allowing for more versatile use cases.
- **Mock Bot**: The mock bot allows for testing and development without incurring costs from the API.

## Installation

To install this project, clone the repository and run the following commands:

```bash
git clone https://github.com/myaichat/ai_voice_bot.git
cd ai_voice_bot
pip install -e .
```

## Usage

### Voice Interaction

To start the voice interaction bot, run the following command:

```bash
python voice_bot.py
```

### Text-Based Interaction

To start the text-based interaction bot, run the following command:

```bash
python text_bot.py
```

### Mock Bot

To run the mock bot for testing, use the following command:

```bash
python mock_bot.py
```

## Building the Project

To build the project and create a wheel distribution:

```bash
pip install wheel
python setup.py sdist bdist_wheel
```

You can find the built wheel file in the `dist/` folder.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## References
https://github.com/run-llama/openai_realtime_client
