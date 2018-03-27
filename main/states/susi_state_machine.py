"""This module declares the SUSI State Machine Class and Component Class.
The SUSI State Machine works on the concept of Finite State Machine.
"""
import json_config
import logging
import requests
import RPi.GPIO as GPIO
from speech_recognition import Recognizer, Microphone

import susi_python as susi
from .busy_state import BusyState
from .error_state import ErrorState
from .idle_state import IdleState
from .recognizing_state import RecognizingState
from threading import Thread


class Components:
    """Common components accessible by each state of the the  SUSI state Machine.
    """

    def __init__(self, renderer=None):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup (17, GPIO.OUT)
        GPIO.setup (27, GPIO.OUT)
        GPIO.setup (22, GPIO.OUT)

        recognizer = Recognizer()
        recognizer.dynamic_energy_threshold = False
        recognizer.energy_threshold = 1000
        self.recognizer = recognizer
        self.microphone = Microphone()
        self.susi = susi
        self.renderer = renderer

        try:
            res = requests.get('http://ip-api.com/json').json()
            self.susi.update_location(
                longitude=res['lon'], latitude=res['lat'])

        except ConnectionError as e:
            logging.error(e)

        self.config = json_config.connect('config.json')

        if self.config['usage_mode'] == 'authenticated':
            try:
                susi.sign_in(email=self.config['login_credentials']['email'],
                             password=self.config['login_credentials']['password'])
            except Exception:
                print('Some error occurred in login. Check you login details in config.json')

        if self.config['hotword_engine'] == 'Snowboy':
            from main.hotword_engine import SnowboyDetector
            self.hotword_detector = SnowboyDetector()
        else:
            from main.hotword_engine import PocketSphinxDetector
            self.hotword_detector = PocketSphinxDetector()

        if self.config['WakeButton'] == 'enabled':
            print("\nSusi has the wake button enabled")
            if self.config['Device'] == 'RaspberryPi':
                print("\nSusi runs on a RaspberryPi")
                from ..hardware_components import RaspberryPiWakeButton
                self.wake_button = RaspberryPiWakeButton()
            else:
                print("\nSusi is not running on a RaspberryPi")
                self.wake_button = None
        else:
            print("\nSusi has the wake button disabled")
            self.wake_button = None


class SusiStateMachine(Thread):
    """SUSI State Machine works on the concept of Finite State Machine. Each step of working of this app is divided into
    a state of the State Machine. Each state can transition into one of the allowed states and pass some information
    to other states as PAYLOAD. Upon Error, transition should happen to Error State and after speaking the correct error
    message, the machine transitions to the Idle State.
    """

    def __init__(self, renderer=None):
        super().__init__()
        components = Components(renderer)
        self.__idle_state = IdleState(components)
        self.__recognizing_state = RecognizingState(components)
        self.__busy_state = BusyState(components)
        self.__error_state = ErrorState(components)
        self.current_state = self.__idle_state

        self.__idle_state.allowedStateTransitions = \
            {'recognizing': self.__recognizing_state, 'error': self.__error_state}
        self.__recognizing_state.allowedStateTransitions = \
            {'busy': self.__busy_state, 'error': self.__error_state}
        self.__busy_state.allowedStateTransitions = \
            {'idle': self.__idle_state, 'error': self.__error_state}
        self.__error_state.allowedStateTransitions = \
            {'idle': self.__idle_state}

    def run(self):
        self.current_state.on_enter(payload=None)
