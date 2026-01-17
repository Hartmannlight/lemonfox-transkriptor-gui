import threading

import numpy as np
import sounddevice as sd


class AudioRecorder:
    def __init__(self):
        self._stream = None
        self._frames = []
        self._recording = False
        self._lock = threading.Lock()

    def start(self, sample_rate: int, channels: int):
        with self._lock:
            if self._recording:
                return
            self._frames = []
            self._recording = True

            def callback(indata, frames, time_info, status):
                if status:
                    pass
                self._frames.append(indata.copy())

            self._stream = sd.InputStream(
                samplerate=sample_rate,
                channels=channels,
                dtype="float32",
                callback=callback,
            )
            self._stream.start()

    def stop(self):
        with self._lock:
            if not self._recording:
                return None
            self._recording = False
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None
            if not self._frames:
                return None
            data = np.concatenate(self._frames, axis=0)
            return data

    @property
    def recording(self):
        with self._lock:
            return self._recording
