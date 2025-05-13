# Sales Personalized Email using Gemini 2.0 Flash

This project uses crewAI with Google's Gemini 2.0 Flash model to generate personalized sales emails based on prospect information.

## Setup

1. Clone this repository:
```
git clone <repository-url>
cd <repository-directory>
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory and add your Gemini API key:
```
# Get your API key from https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_api_key_here

# Model Configuration
MODEL=gemini/gemini-2.0-flash
```

## Usage

Run the main script:
```
python -m sales_personalized_email.main
```

This will generate a personalized sales email based on the prospect information provided in the `main.py` file.

## Configuration

- The project uses the Gemini 2.0 Flash model by default. You can change it to other Gemini models by modifying the `MODEL` variable in your `.env` file.
- Prospect information can be customized in the `main.py` file.
- Agent configurations are defined in the `config/agents.yaml` file.
- Task configurations are defined in the `config/tasks.yaml` file.

## Available Models

- `gemini/gemini-2.0-flash` - Fast, efficient model for most tasks
- `gemini/gemini-2.0-lite` - Lighter version with reduced latency
- `gemini/gemini-1.5-flash` - Previous version flash model

## License

This project is licensed under the MIT License. 