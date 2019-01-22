import os
import pyaudio
import wave
import Adafruit_PCA9685
import time

import math

from pocketsphinx import Decoder
import speech_recognition as sr


class ServoDriver(Adafruit_PCA9685):
    def __init__(self, freq=50, min_us=544, max_us=2400):
        super(ServoDriver, self).__init__()

        self.FREQ = freq
        self.MIN_US = min_us
        self.MAX_US = max_us
        super(ServoDriver, self).set_pwm_freq(self.FREQ)

    def set_servo(self, channel, pos):
        if pos < 0:
            pos = 0
        if pos > 180:
            pos = 180

        u_seconds = self.map(pos, 0, 180, self.MIN_US, self.MAX_US)
        ticks = self.get_ticks(u_seconds)

        super(ServoDriver, self).set_pwm(channel, 0, int(ticks))

    @staticmethod
    def map(value, in_min, in_max, out_min, out_max):
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    @staticmethod
    def get_ticks(u_seconds):
        us_per_tick = (1000000 / self.FREQ) / 4096
        ticks = u_seconds / us_per_tick
        ticks = math.ceil(ticks - 0.5)
        return ticks

class Voice(object):
    def play(self, filepath):
        raise NotImplementedError

    def recognize(self):
        raise NotImplementedError


class RgbLed(object):
    r = 0.0
    g = 0.0
    b = 0.0

    def setColor(self, r, g, b):
        raise NotImplementedError

    def blink(self, times, interval):
        raise NotImplementedError


class Traction(object):
    def forward(self, duration):
        raise NotImplementedError

    def backward(self, duration):
        raise NotImplementedError

    def left(self, duration):
        raise NotImplementedError

    def right(self, duration):
        raise NotImplementedError


class Torso(object):
    def greeting(self, times, duration):
        raise NotImplementedError

    def nope(self, times, duration):
        raise NotImplementedError

    def yep(self, times, duration):
        raise NotImplementedError


class TestVoice(Voice):
    # playback
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    CHUNK = 1024
    FILE_NAME = 'aux.wav'

    # recognition
    MODELDIR = "es-ES"
    GRAMMARDIR = "gram"

    def __init__(self, file_name='aux.wav', raspi=False):
        self.FILE_NAME = file_name
        self.audio = pyaudio.PyAudio()
        self.raspi = raspi

        self.config = Decoder.default_config()
        self.config.set_string('-hmm', os.path.join(self.MODELDIR, 'acoustic-model'))
        self.config.set_string('-dict', os.path.join(self.MODELDIR, 'pronounciation-dictionary.dict'))
        self.config.set_string('-logfn', os.devnull)
        self.decoder = Decoder(self.config)
        self.r = sr.Recognizer()

    def play(self, filename):

        wf = wave.open(filename, 'rb')
        stream = self.audio.open(format=self.audio.get_format_from_width(wf.getsampwidth()),
                                 channels=wf.getnchannels(),
                                 rate=wf.getframerate(),
                                 output=True)
        data = wf.readframes(self.CHUNK)

        # play
        while len(data) > 0:
            stream.write(data)
            data = wf.readframes(self.CHUNK)
        stream.stop_stream()
        stream.close()

    def listen(self, duration=3):
        # start recording
        if self.raspi:
            stream = self.audio.open(format=self.FORMAT,
                                     channels=1,
                                     rate=self.RATE,
                                     input_device_index=2,
                                     input=True,
                                     frames_per_buffer=self.CHUNK)
        else:
            stream = self.audio.open(format=self.FORMAT,
                                     channels=self.CHANNELS,
                                     rate=self.RATE,
                                     # input_device_index = input_index,
                                     input=True,
                                     frames_per_buffer=self.CHUNK)

        frames = []

        for i in range(0, int(self.RATE / self.CHUNK * duration)):
            data = stream.read(self.CHUNK, exception_on_overflow=False)
            frames.append(data)

        stream.stop_stream()
        stream.close()

        wave_file = wave.open(self.FILE_NAME, 'wb')
        if self.raspi:
            wave_file.setnchannels(1)
        else:
            wave_file.setnchannels(self.CHANNELS)

        wave_file.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        wave_file.setframerate(self.RATE)
        wave_file.writeframes(b''.join(frames))
        wave_file.close()

        with sr.AudioFile(self.FILE_NAME) as source:
            audio = self.r.record(source)

        raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)

        return raw_data

    def echo(self):
        self.play(self.FILE_NAME)

    def recognize(self):

        try:
            self.decoder.start_utt()
            self.decoder.process_raw(self.listen(), False, True)
            self.decoder.end_utt()
            hyp = self.decoder.hyp()
            return hyp.hypstr

        except Exception:
            return None

    def loadGrammar(self, grammar):
        # delete(self.decoder)
        grammar_file = grammar + '.gram'
        c_string = os.path.join(self.GRAMMARDIR, grammar_file).encode('ascii')
        print(c_string)

        self.config.set_string('-jsgf', c_string)

        self.decoder.reinit(self.config)

    def close(self):
        self.audio.terminate()


class CholitaTraction(Traction):

    def __init__(self, left=1, right=2):
        self.left_motor = left
        self.right_motor = right
        self.driver = ServoDriver()

    def forward(self, duration):
        print("forward")
        self.driver.set_servo(self.left_motor, 180)
        self.driver.set_servo(self.right_motor, 0)
        time.sleep(duration)
        self.driver.set_pwm(self.left_motor, 0, 0)
        self.driver.set_pwm(self.right_motor, 0, 0)

    def backward(self, duration):
        print("backward")
        self.driver.set_servo(self.left_motor, 0)
        self.driver.set_servo(self.right_motor, 180)
        time.sleep(duration)
        self.driver.set_pwm(self.left_motor, 0, 0)
        self.driver.set_pwm(self.right_motor, 0, 0)

    def left(self, duration):
        print("left")
        self.driver.set_servo(self.left_motor, 180)
        self.driver.set_servo(self.right_motor, 180)
        time.sleep(duration)
        self.driver.set_pwm(self.left_motor, 0, 0)
        self.driver.set_pwm(self.right_motor, 0, 0)

    def right(self, duration):
        print("right")
        self.driver.set_servo(self.left_motor, 0)
        self.driver.set_servo(self.right_motor, 0)
        time.sleep(duration)
        self.driver.set_pwm(self.left_motor, 0, 0)
        self.driver.set_pwm(self.right_motor, 0, 0)