# tasky-ai
An open-to-use command line interface (CLI) for Tasky AI — an AI task management agent, powered by google/adk-python.

## Installation

Note: This project is in its early stages and there no CLI yet. But you can test the agent using following steps.

1. Clone the repository:
   ```bash
   git clone https://github.com/anemvamsi4/tasky-ai.git
   cd tasky-ai
   ```

2. Install the required dependencies:
   ```bash
    pip install uv
    uv sync

    source .venv/bin/activate
    ```

3. Set up GEMINI API key:
   ```bash
    mv .env.example .env
    ```
    add your GEMINI_API_KEY to the `.env` file. Go to [Google AI Studio](https://aistudio.google.com/apikey) to get your API key.

4. Run the agent:
   ```bash
   mkdir -p .tasky/dbs
   adk web --session_service_uri sqlite:///.tasky/dbs/sessions.db ./tasky-ai/agent
   ```

After running the above commands, you can interact with the Tasky AI agent through the web interface. Open your browser and navigate to `http://localhost:8000` to start using the agent.

## Contributing
Contributions are welcome! If you have suggestions for improvements or new features, feel free to open an issue or submit a pull request.

## License

Tasky AI © 2025 by [Vamsi Anem](https://github.com/anemvamsi4) is licensed under 
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

See [LICENSE](./LICENSE) for full terms.
