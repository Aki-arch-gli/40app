from gtts import gTTS
import tempfile
import os


def make_voice(text):

    tts = gTTS(
        text=text,
        lang="ja"
    )

    file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp3"
    )

    tts.save(file.name)

    return file.name