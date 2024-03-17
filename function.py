def main():
    tiny_model = whisper.load_model('tiny')
    while True:
        with sr.Microphone() as source:
            recognizer = sr.Recognizer()
            recognizer.adjust_for_ambient_noise(source)
            print("Say 'hello' to start recording")
            audio = recognizer.listen(source)
            with open('wake_detect.wav', "wb") as f:
                f.write(audio.get_wav_data()) 
            try:
                result = tiny_model.transcribe('wake_detect.wav')
                text_input = result['text']
                while True:
                    if 'hello'  in text_input.lower().strip():
                        break
                    audio = recognizer.listen(source)
                    with open('wake_detect.wav', "wb") as f:
                        f.write(audio.get_wav_data()) 
                    result = tiny_model.transcribe('wake_detect.wav')
                    text_input = result['text']
                    print(text_input)
                print("Recording...")
                speak_text('Recording')
                print("32")
                filename = "input.wav"
                print("1")
                with sr.Microphone() as source:
                    recognizer = sr.Recognizer()
                    source.pause_threshold = 2
                    audio = recognizer.listen(source, phrase_time_limit=None, timeout=None)
                    with open(filename, "wb") as f:
                        f.write(audio.get_wav_data())
                    
                audio_text = tiny_model.transcribe(filename)
                text = audio_text['text']
                if text:
                    print(f"User: {text}")
                    response = generate_mixtral_response(text)
                    message = ''.join(response)
                    full_respone = ''
                    # for item in response:
                    #     full_respone += item
                    #     print(f"AI: {full_respone}")
                    #     speak_text(item)
                    print(f"AI: {message}")
                    speak_text(message)
            except Exception as e:
                print("An error occurred: ", e)
