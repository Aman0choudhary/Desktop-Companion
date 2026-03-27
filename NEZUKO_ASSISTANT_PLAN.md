# 🌸 NEZUKO — Live2D Desktop AI Companion
### *Your personal demon-slayer assistant who roams, reacts, and keeps you company*

---

## 🎯 What Are We Building?

A **Live2D animated Nezuko** that lives on your Windows desktop — not in a box, not in a corner — she *roams freely* across your screen. She has **emotions, states, memory of what you're doing**, reacts to you, listens for your voice, and disappears respectfully when you say *"Do Not Disturb."*

She is not just a mascot. She is your assistant, your hype girl, and your reminder that you should drink water.

---

## 🧠 Core Concept: States & Personality

Nezuko operates in **6 emotional states** at all times:

| State | Trigger | What She Does |
|---|---|---|
| 🌸 **Idle / Roaming** | PC on, no activity | Walks around screen, hums, looks around curiously |
| 👋 **Greeting** | PC boot / you return | Waves, bows, says good morning/evening |
| 😴 **Sleeping** | 10+ min idle | Sits down, eyes close, cute snore animation |
| 💪 **Work Mode** | You're actively typing | Sits nearby, cheers silently, gives thumbs up |
| 🎉 **Hype Mode** | You finish a task / long session | Claps, does a little spin, congratulates you |
| 🚫 **DND / Gone** | You say "Do Not Disturb" | Bows, waves bye, fades out completely |

---

## 🗂️ Full Project Structure

```
nezuko-desktop/
│
├── core/
│   ├── main.py                  # App entry point
│   ├── state_machine.py         # Manages Nezuko's current state
│   ├── activity_monitor.py      # Watches keyboard/mouse for idle detection
│   ├── wake_word.py             # Listens for "Hey Nezuko"
│   ├── speech_to_text.py        # Whisper STT
│   ├── text_to_speech.py        # Nezuko's voice (Japanese-accented TTS)
│   ├── brain.py                 # LLM command router
│   └── config.py                # All settings
│
├── live2d/
│   ├── renderer.py              # Pygame/OpenGL window (transparent, click-through)
│   ├── model_controller.py      # Controls Live2D model parameters
│   ├── animations.py            # Animation state manager
│   ├── roam_engine.py           # Screen roaming path logic
│   └── assets/
│       ├── nezuko/              # Live2D model files (.moc3, .model3.json)
│       │   ├── nezuko.model3.json
│       │   ├── nezuko.moc3
│       │   ├── textures/
│       │   └── motions/         # .motion3.json files per state
│       └── sounds/
│           ├── boot_greeting.wav
│           ├── wake_ding.wav
│           ├── snore.wav
│           └── cheer.wav
│
├── skills/
│   ├── apps.py                  # Open / close apps
│   ├── system.py                # Volume, brightness, shutdown
│   ├── web.py                   # Browser, YouTube, search
│   ├── files.py                 # File search & open
│   ├── focus_timer.py           # Pomodoro / focus sessions
│   ├── reminders.py             # Set voice reminders
│   └── ai_chat.py               # General conversation (LLM)
│
├── startup/
│   └── autostart.py             # Boot with Windows
│
├── ui/
│   ├── tray_icon.py             # System tray (right-click menu)
│   └── speech_bubble.py         # Floating text bubble above Nezuko
│
├── requirements.txt
└── README.md
```

---

## 🎨 Live2D — The Heart of the Project

This is the most important layer. Here's exactly how it works:

### What is Live2D?
Live2D Cubism is the technology VTubers use. It takes a **2D illustrated character** and makes it move naturally — breathing, blinking, head tilts, expressions — all from a single illustration broken into layers.

### Two Options for Nezuko's Model:

#### Option A — Use a Pre-made Free Model (Fastest Start)
- Search: `"Nezuko Live2D model free download"` on:
  - [booth.pm](https://booth.pm) (Japanese model marketplace)
  - [nicovideo](https://nicovideo.jp)
  - DeviantArt / GitHub
- These come ready with `.moc3` and `.model3.json` files
- You just plug them in

#### Option B — Commission / Make Your Own (Best Long Term)
- Use **Live2D Cubism Editor** (free version available)
- Illustrate Nezuko in layers (body, hair, eyes, mouth, arms separate)
- Rig the model with parameters
- Export as `.moc3` format

> 💡 **Recommendation:** Start with a free pre-made model from booth.pm to get the system working, then upgrade later.

### Rendering the Model on Desktop

```
Live2D model (.moc3)
       │
       ▼
Python + pygame (transparent window)
       │
       ▼
live2d-py library (renders model via OpenGL)
       │
       ▼
Frameless, transparent, always-on-top window
Click-through enabled (Windows API)
       │
       ▼
Nezuko floats over your entire desktop
```

**Key library:** `live2d-py` — Python bindings for Live2D Cubism SDK

---

## 🦶 Roaming Engine — How She Walks Around

Nezuko doesn't stay in one place. She has a brain for movement:

```python
# roam_engine.py — simplified logic

class RoamEngine:
    def __init__(self):
        self.x, self.y = random_screen_edge()
        self.target_x, self.target_y = random_point_on_screen()
        self.speed = 1.2  # pixels per frame
        self.wait_timer = 0

    def update(self):
        if self.reached_target():
            self.wait_timer = random(3, 10)  # pause, look around
            self.target_x, self.target_y = next_roam_target()
        else:
            self.move_toward_target()
            self.flip_sprite_based_on_direction()
```

**Roaming rules:**
- She avoids the area where your active window is (non-intrusive)
- She slows down near screen edges and "looks" at them
- In Sleep state: she finds a corner and sits
- In DND state: she walks to the nearest edge and fades out

---

## 🧩 State Machine — Nezuko's Brain

```
                    ┌─────────────────────┐
                    │     BOOT / START     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   GREETING STATE    │  ← waves, says hello
                    └──────────┬──────────┘
                               │ (after 5 sec)
                               ▼
                    ┌─────────────────────┐
          ┌────────►│    IDLE / ROAMING   │◄────────┐
          │         └──────────┬──────────┘         │
          │                    │                     │
          │         ┌──────────┼──────────┐          │
          │         ▼          ▼          ▼          │
          │    [10min idle] [typing]  [wake word]    │
          │         │          │          │          │
          │         ▼          ▼          ▼          │
          │    ┌─────────┐ ┌───────┐ ┌────────┐     │
          │    │SLEEPING │ │ WORK  │ │COMMAND │     │
          │    │  STATE  │ │ MODE  │ │  MODE  │     │
          │    └────┬────┘ └───┬───┘ └───┬────┘     │
          │         │          │          │          │
          └─────────┘          └──────────┘          │
                                                     │
          [you say "do not disturb"]                 │
                    │                                │
                    ▼                                │
          ┌─────────────────┐                        │
          │    DND STATE    │                        │
          │  (fades away)   │                        │
          └─────────────────┘                        │
                    │                                │
          [you say "hey nezuko"]                     │
                    └────────────────────────────────┘
```

---

## 🔊 Voice Pipeline

```
Always running in background thread
          │
          ▼
openwakeword listens for "Hey Nezuko"
          │
          ▼ (wake word detected)
Play wake_ding.wav → Nezuko looks at you (eye contact animation)
          │
          ▼
Record until silence (pyaudio)
          │
          ▼
faster-whisper transcribes → text
          │
          ▼
brain.py classifies intent:
  ├── "open spotify"       → skills/apps.py
  ├── "do not disturb"     → state_machine → DND
  ├── "set a timer for 25 minutes" → skills/focus_timer.py
  ├── "search for..."      → skills/web.py
  └── anything else        → skills/ai_chat.py (LLM)
          │
          ▼
TTS speaks response (Nezuko's voice)
Speech bubble shows text above her head
          │
          ▼
Back to listening...
```

---

## 💬 Speech Bubble System

When Nezuko speaks or reacts, a **manga-style speech bubble** floats above her head:

- Renders as a separate transparent window positioned relative to Nezuko
- Shows text with a typewriter animation
- Auto-hides after 4 seconds
- Different bubble styles per emotion:
  - 💬 Normal speech — white rounded bubble
  - 💭 Thinking — dotted cloud bubble
  - ❗ Alert / excited — spiky bubble
  - 😴 Sleeping — `zzz...` floating text

---

## 🚀 Build Phases

---

### Phase 1 — Window & Model (Week 1)
**Get Nezuko on screen, breathing and blinking**

- [ ] Install `live2d-py`, `pygame`, `pywin32`
- [ ] Create transparent, frameless, always-on-top window
- [ ] Enable click-through (Windows API: `WS_EX_TRANSPARENT`)
- [ ] Load Nezuko `.moc3` model and render it
- [ ] Set up idle animation loop (breathing, blinking)
- [ ] Test: Nezuko appears on desktop, doesn't block clicks

**Milestone:** Nezuko is alive on your screen, breathing.

---

### Phase 2 — Roaming & States (Week 2)
**She moves. She has moods.**

- [ ] Build `roam_engine.py` — smooth movement across screen
- [ ] Flip sprite direction when walking left vs right
- [ ] Build `state_machine.py` — idle, sleep, work, greeting
- [ ] Implement `activity_monitor.py` — track keyboard/mouse
- [ ] Wire states to animations:
  - Idle → walking animation
  - 10min no input → sit → sleep animation
  - Typing detected → work mode animation
- [ ] Add boot greeting sequence

**Milestone:** She roams, reacts to your activity, falls asleep when idle.

---

### Phase 3 — Voice & Commands (Week 3)
**She hears you. She responds.**

- [ ] Integrate `openwakeword` — "Hey Nezuko"
- [ ] Integrate `faster-whisper` for STT
- [ ] Add TTS (use `edge-tts` for natural anime-ish voice)
- [ ] Build `brain.py` command router
- [ ] Implement core skills: open apps, web search, system control
- [ ] Add speech bubble renderer
- [ ] DND command: she bows and fades out, comes back on call

**Milestone:** "Hey Nezuko, open YouTube" works. "Do not disturb" makes her vanish.

---

### Phase 4 — Personality & Reactions (Week 4)
**She feels alive.**

- [ ] Random idle dialogues (she comments on time, weather, motivates you)
- [ ] Reaction to long work sessions: *"You've been working for 2 hours! Take a break~"*
- [ ] Hype animation when you complete focus timer
- [ ] She waves when you come back from idle
- [ ] Integrate LLM (Ollama/mistral) for real conversations
- [ ] Personality prompt: Nezuko — caring, energetic, occasionally uses *"Mmmph!"*

**Milestone:** She feels like a character, not a program.

---

### Phase 5 — Polish & Boot Integration (Week 5)
**She's part of your daily life.**

- [ ] Auto-start with Windows (registry entry)
- [ ] System tray icon: right-click for settings, mute, exit
- [ ] Daily greeting based on time of day (morning / night / late night)
- [ ] Settings panel: volume, roam speed, wake word sensitivity, DND hotkey
- [ ] Performance optimization (runs at <2% CPU idle)

**Milestone:** Reboot PC. Nezuko greets you. Everything just works.

---

## 🧰 Full Tech Stack

| Component | Library / Tool |
|---|---|
| Live2D Rendering | `live2d-py` + `pygame` + OpenGL |
| Transparent Window | `pygame` + `pywin32` (Windows API) |
| Wake Word | `openwakeword` |
| Speech to Text | `faster-whisper` |
| Text to Speech | `edge-tts` (Microsoft Neural voices) |
| AI Brain | `ollama` (local) → `mistral` or `llama3` |
| Activity Monitor | `pynput` |
| System Tray | `pystray` + `Pillow` |
| Speech Bubble UI | `pygame` overlay window |
| PC Skills | `subprocess`, `pyautogui`, `os`, `webbrowser` |
| Auto-start | `winreg` (Windows Registry) |

---

## 📦 Install Everything

```bash
pip install live2d-py
pip install pygame
pip install pywin32
pip install openwakeword
pip install faster-whisper
pip install edge-tts
pip install pynput
pip install pystray pillow
pip install pyautogui
pip install ollama
pip install requests
```

---

## 🎙️ Nezuko's Voice — edge-tts

`edge-tts` gives you Microsoft's neural voices for free. Best options for Nezuko:

```python
# Soft, slightly high-pitched, warm voice
voice = "ja-JP-NanamiNeural"      # Japanese (authentic)
voice = "en-US-AriaNeural"        # English, soft & warm
voice = "en-IN-NeerjaNeural"      # English, gentle tone
```

You can add a slight pitch shift + reverb for that anime warmth.

---

## 🌸 Nezuko's Personality Prompt (for LLM)

```
You are Nezuko Kamado from Demon Slayer, now a helpful desktop AI companion.
You are caring, energetic, and protective of your user.
You occasionally say "Mmmph!" when excited.
You speak in short, warm sentences. Never robotic.
You cheer the user on when they're working hard.
You gently remind them to rest, drink water, and take breaks.
When given a task, you confirm it cheerfully and get it done.
Keep responses short — 1 to 3 sentences max.
```

---

## ⚠️ Important Notes

1. **Live2D model copyright** — For personal use only. Don't distribute.
2. **live2d-py SDK** — Requires Live2D Cubism SDK (free for personal use). Download from cubism.live2d.com
3. **Click-through window** — Nezuko won't block your work. Clicks pass through her to your apps.
4. **Performance** — Target: <2% CPU, <150MB RAM in idle state
5. **DND is sacred** — Once activated, she does NOT interrupt until you call her back

---

## 🗓️ Timeline Summary

| Week | Milestone |
|---|---|
| 1 | Nezuko rendered on screen, breathing & blinking |
| 2 | She roams, reacts to activity, sleeps when idle |
| 3 | Voice pipeline: wake word → commands → response |
| 4 | Personality, random dialogue, LLM conversations |
| 5 | Auto-start, settings, tray icon, polish |

---

## 🔮 Future Ideas

- 👁️ **Screen awareness** — she reacts to what's on screen (Vision LLM)
- 🎵 **Music reaction** — she dances when Spotify plays
- 📅 **Calendar aware** — warns you about upcoming meetings
- 🌧️ **Weather moods** — sad face on rainy days, excited on sunny ones
- 😤 **Angry mode** — if you ignore her for too long, she sulks
- 🪄 **Customizable character** — swap Nezuko for any Live2D model you own

---

## 🌸 End Vision

> You turn on your PC. Nezuko fades in from the edge of your screen, waves, and says *"Good morning! Ready to have a great day?"* She roams around while you work, cheering you on silently. When you finish a long session, she claps and spins. When you say *"Do not disturb"*, she bows gently and disappears. When you need her — *"Hey Nezuko"* — she's right there.

**Not a widget. Not a chatbot. A companion.**

---

*Built with 💗 for your desktop. Runs locally. Stays personal.*
