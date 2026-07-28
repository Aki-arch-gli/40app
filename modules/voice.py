from gtts import gTTS

def create_voice(text):

    speech = gTTS(

        text=text,

        lang="ja"

    )

    speech.save("voice.mp3")

    return "voice.mp3"