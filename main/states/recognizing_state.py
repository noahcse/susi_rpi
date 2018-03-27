""" Class to Represent Recognizing State
"""
from .base_state import State
import speech_recognition as sr
import RPi.GPIO as GPIO


class RecognizingState(State):
    """ Recognizing State inherits from Base State class. In this state, audio is recorded from the microphone and
    recognized with the Speech Recognition Engine set as default in the configuration.
    """

    def __recognize_audio(self, recognizer, audio):
        if self.components.config['default_stt'] == 'google':
            return recognizer.recognize_google(audio)

        elif self.components.config['default_stt'] == 'watson':
            username = self.components.config['watson_stt_config']['username']
            password = self.components.config['watson_stt_config']['password']
            return recognizer.recognize_ibm(
                username=username,
                password=password,
                audio_data=audio)

        elif self.components.config['default_stt'] == 'bing':
            api_key = self.components.config['bing_speech_api_key']
            return recognizer.recognize_bing(audio_data=audio, key=api_key)

    def on_enter(self, payload=None):
        """ Executed on the entry to the Recognizing State. Upon entry, audio is captured from the Microphone and
        recognition with preferred speech recognition engine is done. If successful, the machine transitions to Busy
        State. On failure, it transitions to Error state.
        :param payload: No payload is expected by this state
        :return: None
        """

        self.notify_renderer('listening')
        recognizer = self.components.recognizer
        try:
            print("Say something!")
            GPIO.output(22, True)
            with self.components.microphone as source:
                audio = recognizer.listen(source, phrase_time_limit=5)
            self.notify_renderer('recognizing')
            GPIO.output(22, False)
            print("Got it! Now to recognize it...")
            try:
                value = self.__recognize_audio(
                    audio=audio, recognizer=recognizer)
                print(value)
                self.notify_renderer('recognized', value)
                self.transition(self.allowedStateTransitions.get(
                    'busy'), payload=value)
            except sr.UnknownValueError:
                print("Oops! Didn't catch that")
                self.transition(self.allowedStateTransitions.get(
                    'error'), payload='RecognitionError')

            except sr.RequestError as e:
                print(
                    "Uh oh! Couldn't request results from Speech Recognition service; {0}".format(e))
                self.transition(self.allowedStateTransitions.get(
                    'error'), payload='ConnectionError')

        except KeyboardInterrupt:
            pass

    def on_exit(self):
        """ Method to executed upon exit from Recognizing State.
        :return:
        """
        GPIO.output(17, False)
        GPIO.output(27, False)
        GPIO.output(22, False)
        pass
