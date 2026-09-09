import shutil
import subprocess

VOICE = {"en": "en", "zh": "zh", "ms": "ms", "ta": "ta"}


def speak(language, text):
    """Speak through the Pi's default audio device if espeak-ng is installed."""
    binary = shutil.which("espeak-ng")
    if not binary:
        return
    voice = VOICE.get(language, "en")
    try:
        subprocess.Popen([binary, "-v", voice, "-s", "145", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
