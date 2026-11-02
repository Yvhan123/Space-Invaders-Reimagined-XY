# Space Invaders Reimagined XY

A retro-inspired **Space Invaders** arcade game built with Python and **Pygame (`pygame-ce`)**, featuring:
- **Pixelated Green X-Wing Starfighter** with full 4-directional movement (`X` & `Y` axes)
- **Vibrant Multi-Colored Pixel-Art Aliens** with randomized spawning and unpredictable flight patterns (`weaver`, `zigzag`, `swooper`)
- **Procedural 8-Bit Audio & Chiptune Soundtrack** synthesized in real time (zero external audio files needed)

## How to Run

1. **Windows One-Click**: Double-click `play.bat`
2. **Using Python**:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```

## Controls

| Key | Action |
| --- | --- |
| **WASD** or **Arrow Keys** | Fly your Green X-Wing in all 4 directions |
| **Spacebar** (hold) | Fire lasers |
| **M** | Toggle 8-bit chiptune background music On / Off |
| **P** or **ESC** | Pause / Resume game |
| **Enter** | Play again after Game Over |

## Project Structure

- `main.py` — Main game loop, wave spawning, collision detection, and HUD.
- `sprites.py` — `Player` (Green X-Wing), `Alien` (multi-colored invaders), `Bullet`, and `Particle`.
- `sounds.py` — Procedural 8-bit sound effect & chiptune music synthesizer (`SoundManager`).
- `settings.py` — Game configuration and constants.
- `play.bat` — Quick launcher script for Windows.
