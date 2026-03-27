# Desktop-Companion

## Nezuko Desktop Companion

This repository now contains a working Windows desktop companion prototype that follows the Nezuko assistant plan.

What is built today:

- A runnable pygame overlay companion window with roaming, emotions, and speech bubbles
- A state machine for greeting, idle, work, sleeping, hype, and DND
- Real global keyboard and mouse activity hooks through `pynput`
- Typed commands for timers, reminders, status, dry-run app/web/file/system actions, and chat
- Wake word, STT, and TTS pipeline wiring using `openwakeword`, `faster-whisper`, and `edge-tts`
- Real Live2D loading support through `live2d-py`
- A bundled Cubism sample model (`Haru`) for renderer validation
- System tray controls, persistent settings, and Windows autostart integration

Current stand-ins and limitations:

- The repo does not bundle a true Nezuko Live2D model. `Haru` is still the technical validation model.
- The wake-word detector still defaults to `hey_jarvis` because there is no bundled `Hey Nezuko` model.
- `edge-tts` needs network access when speech is synthesized.
- The first real Whisper transcription may download model files into `assets/voice/whisper_models/`.

## Run the prototype

Use Python 3.11+:

```bash
python -m core.main
```

Controls inside the prototype window:

- `Enter`: open the typed command box
- `T`: simulate active typing and switch toward Work mode
- `H`: wake Nezuko back up and replay the greeting
- `D`: toggle Do Not Disturb
- `V`: show the current wake-word detector status
- `Space`: show a short speech bubble
- `Esc`: quit

Example typed commands:

- `help`
- `status`
- `focus 10 seconds`
- `timer status`
- `remind me to drink water in 30 seconds`
- `open spotify`
- `search for cozy coding music`
- `do not disturb`

## Tray and settings

- The app now creates a tray icon with toggles for DND, voice, click-through, startup, settings, and quit.
- Settings are stored in `assets/settings.json`.
- The settings window lets you change:
  - voice enable/disable
  - global activity hooks
  - click-through behavior
  - startup with Windows
  - wake phrase
  - wake model name or custom `.onnx` path
  - Live2D model path
  - Edge TTS voice
- Voice settings reload immediately after save.
- Live2D model path changes are saved, but the app should be restarted to load a different model cleanly.

## Live2D model support

- The app uses a frameless always-on-top Windows overlay window.
- If a Cubism `*.model3.json` file is available, the renderer will try to initialize `live2d-py`.
- The bundled `assets/live2d/Haru/` folder is only a sample validation model.
- You can point Settings at a real licensed model file elsewhere on disk if you have one.

## Activity monitoring

- `pynput` is now used for real global keyboard and mouse activity hooks.
- Work mode and idle/sleep transitions can react to actual desktop activity instead of only the in-window simulation keys.
- The old manual controls still exist for quick testing inside the app window.

## Voice pipeline

- `openwakeword`, `faster-whisper`, `edge-tts`, `sounddevice`, and `soundfile` are now wired into the project.
- Wake-word models are stored locally under `assets/voice/openwakeword_models/`.
- The current wake model is `hey_jarvis` as a temporary stand-in.
- You can override it with a custom `.onnx` wake-word model path from Settings.
- The app now has background voice pipeline plumbing for wake detection, microphone capture, transcription, and spoken replies.
- The first real Whisper transcription may download the configured model (`tiny.en`) into `assets/voice/whisper_models/`.

## Tests

```bash
python -m unittest discover -s tests
```
