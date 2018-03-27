"""Class to represent the Busy State
"""
from ..speech import TTS
from .base_state import State
import RPi.GPIO as GPIO


class BusyState(State):
    """Busy state inherits from base class State. In this state, SUSI API is called to perform query and the response
    is then spoken with the selected Text to Speech Service.
    """

    def on_enter(self, payload=None):
        """This method is executed on entry to Busy State. SUSI API is called via SUSI Python library to fetch the
        result. We then call TTS to speak the reply. If successful, we transition to Idle State else to the Error State.
        :param payload: query to be asked to SUSI
        :return: None
        """
        try:
            GPIO.output(17, True)
            reply = self.components.susi.ask(payload)
            GPIO.output(17, False)
            GPIO.output(27, True)
            if self.components.renderer is not None:
                self.notify_renderer('speaking', payload={'susi_reply': reply})

            if 'answer' in reply.keys():
                print('Susi:' + reply['answer'])
                self.__speak(reply['answer'])
            else:
                self.__speak("I don't have an answer to this")

            if 'table' in reply.keys():
                table = reply['table']
                for h in table.head:
                    print('%s\t' % h, end='')
                    self.__speak(h)
                print()
                for datum in table.data[0:4]:
                    for value in datum:
                        print('%s\t' % value, end='')
                        self.__speak(value)
                    print()

            if 'rss' in reply.keys():
                rss = reply['rss']
                entities = rss['entities']
                count = rss['count']
                for entity in entities[0:count]:
                    print(entity.title)
                    self.__speak(entity.title)

            self.transition(self.allowedStateTransitions.get('idle'))

        except ConnectionError:
            self.transition(self.allowedStateTransitions.get(
                'error'), payload='ConnectionError')
        except Exception as e:
            print(e)
            self.transition(self.allowedStateTransitions.get('error'))

    def on_exit(self):
        """Method executed on exit from the Busy State.
        """
        GPIO.output(17, False)
        GPIO.output(27, False)
        GPIO.output(22, False)
        pass

    def __speak(self, text):
        if self.components.config['default_tts'] == 'google':
            TTS.speak_google_tts(text)
        if self.components.config['default_tts'] == 'flite':
            TTS.speak_flite_tts(text)
        elif self.components.config['default_tts'] == 'watson':
            TTS.speak_watson_tts(text)
