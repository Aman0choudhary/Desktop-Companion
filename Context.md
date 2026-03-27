# NEZUKO - Active Session Context

## What We're Building

Nezuko desktop companion for Windows based on the plan in `NEZUKO_ASSISTANT_PLAN.md`.
The goal is a roaming desktop assistant with Live2D rendering, emotional states,
activity awareness, typed/voice commands, reminders, and DND behavior.

## Current Status

- [x] Project scaffold created
- [x] Core app loop built
- [x] State machine built for greeting, idle, work, sleeping, hype, and DND
- [x] Roaming engine built
- [x] Typed command flow built
- [x] Safe dry-run skill routing built for apps, web, files, system, timer, reminders, and chat
- [x] Pygame + pywin32 desktop overlay renderer path added
- [x] `live2d-py` import path fixed by moving local rendering code out of the old `live2d` package name
- [x] Live2D model discovery/loader shell added in `rendering/model_controller.py`
- [x] Real Cubism v3 sample model bundled for renderer validation (`assets/live2d/Haru/`)
- [x] Real Live2D state-to-motion/expression mapping added for the bundled sample model
- [ ] Real Nezuko Live2D model asset added
- [x] Import-ready custom Live2D model path support added through persistent settings
- [x] Activity monitor upgraded from simulated input to real desktop activity hooks
- [x] Wake word / STT / TTS pipeline scaffolded and connected to the app loop
- [x] System tray, startup integration, and settings UI
- [x] Import-ready custom wake-word ONNX path support added through persistent settings

## Files That Matter Most Right Now

- `core/main.py` - app orchestration
- `core/state_machine.py` - state transitions
- `rendering/renderer.py` - pygame overlay window and drawing path
- `rendering/model_controller.py` - Live2D model discovery/loading
- `rendering/roam_engine.py` - roaming movement
- `Context.md` - current working memory for the project

## What Was Finished Before This Step

1. Built the initial runnable prototype and project structure.
2. Added tests for state machine and roaming logic.
3. Added typed commands and dry-run assistant skills.
4. Replaced the Tk renderer path with a Windows-oriented pygame overlay path.
5. Installed `pygame`, `pywin32`, and `live2d-py`.
6. Verified that `import live2d.v3` works from this repo.

## Current Task

> Just finished: added tray/settings/startup integration and made the app ready for user-supplied Live2D and wake-word assets.

## Known Issues / Blockers

- A true Nezuko Cubism asset is still not present. The repo currently uses `Haru` only as a technical validation stand-in.
- A true Nezuko wake-word ONNX model is still not present. The default remains `hey_jarvis`.
- The app now supports custom model paths for both of those assets, but it does not bundle third-party Nezuko files.
- `edge-tts` requires network access when it synthesizes speech.
- The first actual Whisper transcription may trigger a model download into `assets/voice/whisper_models/`.
- The plan file text has encoding issues in places, but the intent is still clear.

## Next 3 Steps

1. Drop in a legitimate Nezuko Cubism model and point Settings to its `*.model3.json`.
2. Drop in a custom wake-word ONNX model for `Hey Nezuko` and point Settings to it.
3. Continue polish on voice behavior, renderer UX, and later-phase assistant actions.

## Session Outcome

- Added a real Cubism v3 sample model under `assets/live2d/Haru/`.
- Verified `live2d-py` can load and render a real model in this repo.
- Added state-aware motion/expression mapping in `rendering/model_controller.py`.
- Kept the project honest: this is a working sample model integration, not yet a true Nezuko model drop-in.
- Installed `pynput` and upgraded `core/activity_monitor.py` to use real global keyboard and mouse hooks.
- Verified the hook startup path returns: `Global keyboard and mouse activity hooks are running.`
- Installed `openwakeword`, `faster-whisper`, `edge-tts`, `sounddevice`, and `soundfile`.
- Added `core/wake_word.py`, `core/speech_to_text.py`, `core/text_to_speech.py`, and `core/voice_pipeline.py`.
- Downloaded local wake-word assets into `assets/voice/openwakeword_models/`.
- Verified the wake detector initializes locally and the voice pipeline starts with microphone capture.
- Added persistent settings helpers in `core/config.py` and store settings in `assets/settings.json`.
- Added tray/runtime command plumbing with `core/commands.py`, `core/status.py`, `ui/tray_icon.py`, and `ui/settings_window.py`.
- Replaced the autostart placeholder with real Windows Run-key integration in `startup/autostart.py`.
- Wired the running app to saved settings, tray commands, autostart state, and on-the-fly voice reloads in `core/main.py`.
- Added import-ready support for custom Live2D `*.model3.json` paths and custom wake-word `.onnx` paths.
- Verified the updated build with `python -m unittest discover -s tests -v`, `python -m compileall core rendering ui skills startup main.py`, and direct imports for `core.main`, `ui.tray_icon`, and `ui.settings_window`.
