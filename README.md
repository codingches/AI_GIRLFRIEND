# AI_WAIFU

A simple ChatGPT-powered anime waifu chat application.

## Setup

1. Create a virtual environment:
   ```powershell
   cd c:\Users\user\Desktop\AI_WAIFU
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   .venv\Scripts\activate.bat
   ```

2. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Provide your OpenAI API key:
   - Windows PowerShell:
     ```powershell
     $env:OPENAI_API_KEY = "your_api_key_here"
     ```
   - Or create a `.env` file in `AI_WAIFU` with:
     ```text
     OPENAI_API_KEY=your_api_key_here
     ```

4. Run the chat:
   ```powershell
   python folder1\aiwaifu.py
   ```

### Voice mode

To enable local voice input/output when packages are installed:
```powershell
python folder1\aiwaifu.py --voice
```

To use OpenAI Whisper transcription for voice input:
```powershell
python folder1\aiwaifu.py --whisper
```

Type `voice` during the chat to speak instead of typing.

## Usage

Type messages and press Enter. Use `exit` or `quit` to end the chat.

## Notes

- The assistant uses a cute anime waifu persona.
- You can customize the system prompt in `folder1/aiwaifu.py`.
- Voice mode is optional and requires extra packages.
