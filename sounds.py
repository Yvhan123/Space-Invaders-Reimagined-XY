"""
Procedural 8-Bit Retro Sound & Chiptune Music Synthesizer.
Generates authentic arcade sound effects and looping chiptune music in memory
without needing any external audio files!
"""

from array import array
import math
import random
import pygame

SAMPLE_RATE = 44100


def _make_sound(samples: array) -> pygame.mixer.Sound:
    """Converts a mono 16-bit signed integer array into a stereo Pygame Sound."""
    stereo = array("h")
    for s in samples:
        stereo.append(s)
        stereo.append(s)
    return pygame.mixer.Sound(buffer=stereo.tobytes())


def _synth_sweep(
    start_freq: float,
    end_freq: float,
    duration: float,
    volume: float = 0.35,
    wave: str = "square",
    vibrato_hz: float = 0.0,
    vibrato_depth: float = 0.0,
) -> pygame.mixer.Sound:
    """Synthesizes a frequency-swept 8-bit tone."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = array("h")
    phase = 0.0

    for i in range(num_samples):
        t = i / num_samples
        freq = start_freq + (end_freq - start_freq) * t
        if vibrato_hz > 0:
            freq += math.sin(2 * math.pi * vibrato_hz * (i / SAMPLE_RATE)) * vibrato_depth

        phase += freq / SAMPLE_RATE
        frac = phase - math.floor(phase)

        if wave == "square":
            raw = 1.0 if frac < 0.5 else -1.0
        elif wave == "pulse25":
            raw = 1.0 if frac < 0.25 else -1.0
        elif wave == "saw":
            raw = 2.0 * frac - 1.0
        else:  # triangle
            raw = 4.0 * abs(frac - 0.5) - 1.0

        # Smooth fade-out envelope
        env = (1.0 - t) ** 0.6
        val = int(raw * env * volume * 32767)
        samples.append(max(-32767, min(32767, val)))

    return _make_sound(samples)


def _synth_explosion(
    duration: float,
    base_freq: float = 280.0,
    volume: float = 0.4,
    heavy: bool = False,
) -> pygame.mixer.Sound:
    """Synthesizes an 8-bit crunchy retro explosion using stepped noise + tone drop."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = array("h")
    phase = 0.0
    noise_val = 0.0
    noise_hold = 28 if heavy else 14

    for i in range(num_samples):
        t = i / num_samples
        if i % noise_hold == 0:
            noise_val = random.uniform(-1.0, 1.0)

        freq = base_freq * ((1.0 - t * 0.8) if not heavy else (1.0 - t * 0.9))
        phase += max(30.0, freq) / SAMPLE_RATE
        square = 1.0 if (phase - math.floor(phase)) < 0.5 else -1.0

        mixed = (0.65 * noise_val + 0.35 * square) if not heavy else (0.75 * noise_val + 0.25 * square)
        env = (1.0 - t) ** (0.8 if not heavy else 0.5)
        val = int(mixed * env * volume * 32767)
        samples.append(max(-32767, min(32767, val)))

    return _make_sound(samples)


def _synth_melody(notes: list[tuple[float, float]], volume: float = 0.32, wave: str = "square") -> pygame.mixer.Sound:
    """Synthesizes a sequence of (frequency_hz, duration_sec) notes."""
    samples = array("h")
    phase = 0.0

    for freq, dur in notes:
        num_samples = int(SAMPLE_RATE * dur)
        for i in range(num_samples):
            t = i / num_samples
            if freq <= 0:
                samples.append(0)
                continue

            phase += freq / SAMPLE_RATE
            frac = phase - math.floor(phase)
            if wave == "square":
                raw = 1.0 if frac < 0.5 else -1.0
            elif wave == "pulse25":
                raw = 1.0 if frac < 0.25 else -1.0
            else:
                raw = 4.0 * abs(frac - 0.5) - 1.0

            # Staccato note envelope
            env = 1.0 if t < 0.82 else (1.0 - (t - 0.82) / 0.18)
            val = int(raw * env * volume * 32767)
            samples.append(max(-32767, min(32767, val)))

    return _make_sound(samples)


def _synth_chiptune_loop(volume: float = 0.16) -> pygame.mixer.Sound:
    """
    Builds a looping 8-bit space arcade chiptune soundtrack (lead pulse + triangle bass).
    """
    # Note frequencies (Hz)
    A2, C3, D3, E3, F3, G3 = 110.0, 130.81, 146.83, 164.81, 174.61, 196.00
    A3, C4, D4, E4, F4, G4 = 220.0, 261.63, 293.66, 329.63, 349.23, 392.00
    A4, B4, C5, D5, E5 = 440.0, 493.88, 523.25, 587.33, 659.25

    step_dur = 0.15  # 16th-note step duration (~100 BPM)
    # 32-step retro space melody & bassline
    lead_steps = [
        A4, 0, C5, 0, E5, 0, C5, A4,
        G4, 0, B4, 0, D5, 0, B4, G4,
        F4, 0, A4, 0, C5, 0, A4, F4,
        E4, E4, G4, 0, B4, 0, E5, 0,
    ]
    bass_steps = [
        A2, A3, A2, A3, A2, A3, A2, C3,
        G3, D3, G3, D3, G3, D3, G3, B4 / 4,
        F3, C3, F3, C3, F3, C3, F3, A3,
        E3, B4 / 4, E3, B4 / 4, E3, G3, A3, E3,
    ]

    samples = array("h")
    lead_phase = 0.0
    bass_phase = 0.0
    samples_per_step = int(SAMPLE_RATE * step_dur)

    for l_freq, b_freq in zip(lead_steps, bass_steps):
        for i in range(samples_per_step):
            t = i / samples_per_step
            # 25% pulse lead
            if l_freq > 0:
                lead_phase += l_freq / SAMPLE_RATE
                l_frac = lead_phase - math.floor(lead_phase)
                l_raw = (1.0 if l_frac < 0.25 else -1.0) * (1.0 - t * 0.5)
            else:
                l_raw = 0.0

            # Triangle bass
            if b_freq > 0:
                bass_phase += b_freq / SAMPLE_RATE
                b_frac = bass_phase - math.floor(bass_phase)
                b_raw = (4.0 * abs(b_frac - 0.5) - 1.0) * (1.0 - t * 0.35)
            else:
                b_raw = 0.0

            mixed = (0.55 * l_raw + 0.45 * b_raw) * volume
            samples.append(max(-32767, min(32767, int(mixed * 32767))))

    return _make_sound(samples)


class SoundManager:
    """Manages all retro sound effects and background chiptune music."""

    def __init__(self):
        self.enabled = False
        self.music_muted = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(16)
            self.enabled = True
        except pygame.error:
            return

        # 1. Player laser "pew!"
        self.sfx_player_shoot = _synth_sweep(
            start_freq=980.0, end_freq=210.0, duration=0.13, volume=0.32, wave="pulse25"
        )
        # 2. Alien laser zap
        self.sfx_alien_shoot = _synth_sweep(
            start_freq=480.0,
            end_freq=150.0,
            duration=0.17,
            volume=0.26,
            wave="saw",
            vibrato_hz=35.0,
            vibrato_depth=45.0,
        )
        # 3. Alien killed pop/explosion
        self.sfx_alien_killed = _synth_explosion(duration=0.22, base_freq=340.0, volume=0.36, heavy=False)
        # 4. Player hit (lost a life)
        self.sfx_player_hit = _synth_explosion(duration=0.48, base_freq=180.0, volume=0.48, heavy=True)
        # 5. Player died (Game Over explosion + descending notes)
        self.sfx_player_die = _synth_melody(
            [(392.0, 0.16), (370.0, 0.16), (349.2, 0.16), (329.6, 0.38)],
            volume=0.38,
            wave="square",
        )
        # 6. Bunker shield hit
        self.sfx_bunker_hit = _synth_sweep(
            start_freq=260.0, end_freq=90.0, duration=0.06, volume=0.22, wave="square"
        )
        # 7. Wave cleared victory fanfare
        self.sfx_wave_clear = _synth_melody(
            [(523.25, 0.10), (659.25, 0.10), (783.99, 0.10), (1046.50, 0.26)],
            volume=0.35,
            wave="pulse25",
        )
        # 8. Classic 4-note Space Invaders alien march bass thumps
        self.sfx_march = [
            _synth_sweep(f, f * 0.85, duration=0.075, volume=0.28, wave="triangle")
            for f in (98.0, 87.3, 82.4, 73.4)  # G2, F2, E2, D2
        ]
        self.march_index = 0

        # 9. Looping background retro chiptune music
        self.bg_music = _synth_chiptune_loop(volume=0.15)
        self.music_channel = pygame.mixer.Channel(0)

    def start_music(self):
        if self.enabled and not self.music_muted:
            self.music_channel.play(self.bg_music, loops=-1)

    def stop_music(self):
        if self.enabled:
            self.music_channel.stop()

    def toggle_music(self):
        if not self.enabled:
            return
        self.music_muted = not self.music_muted
        if self.music_muted:
            self.music_channel.pause()
        else:
            if self.music_channel.get_busy():
                self.music_channel.unpause()
            else:
                self.music_channel.play(self.bg_music, loops=-1)

    def play_player_shoot(self):
        if self.enabled:
            self.sfx_player_shoot.play()

    def play_alien_shoot(self):
        if self.enabled:
            self.sfx_alien_shoot.play()

    def play_alien_killed(self):
        if self.enabled:
            self.sfx_alien_killed.play()

    def play_player_hit(self):
        if self.enabled:
            self.sfx_player_hit.play()

    def play_player_die(self):
        if self.enabled:
            self.sfx_player_hit.play()
            self.sfx_player_die.play()

    def play_bunker_hit(self):
        if self.enabled:
            self.sfx_bunker_hit.play()

    def play_wave_clear(self):
        if self.enabled:
            self.sfx_wave_clear.play()

    def play_march_step(self):
        if self.enabled:
            self.sfx_march[self.march_index].play()
            self.march_index = (self.march_index + 1) % len(self.sfx_march)
