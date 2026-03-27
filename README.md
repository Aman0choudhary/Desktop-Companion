# Desktop-Companion

## Nezuko Desktop Prototype

This repository now contains the first safe implementation slice for the Nezuko desktop companion plan.

What is built today:

- A runnable Python prototype with a simple desktop companion window
- A state machine for greeting, idle, work, sleeping, and DND
- A roaming engine that moves the companion around the screen
- A lightweight activity monitor with simulated typing/activity controls
- A speech bubble overlay for short reactions
- Unit tests for the state machine and roaming logic

What is intentionally not wired yet:

- Real Live2D rendering
- Click-through transparent Windows window behavior
- Global keyboard and mouse hooks
- Wake word, STT, TTS, LLM chat, and autostart
- Launching apps or changing system settings

Those items either need external assets, extra dependencies, or user approval before they become reasonable to enable.

## Run the prototype

Use Python 3.11+:

```bash
python -m core.main
```

Controls inside the prototype window:

- `T`: simulate active typing and switch toward Work mode
- `H`: wake Nezuko back up and replay the greeting
- `D`: toggle Do Not Disturb
- `Space`: show a short speech bubble
- `Esc`: quit

## Tests

```bash
python -m unittest discover -s tests
```

## Next safe steps

1. Add a real Windows activity monitor behind the existing interface.
2. Swap the placeholder renderer for `pygame` and then `live2d-py`.
3. Add skills and command routing in a dry-run mode before any real system actions.
4. Ask for approval before dependency installs, voice capture, startup changes, or app-launch/system-control features.
