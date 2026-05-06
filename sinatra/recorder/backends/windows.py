from ..base import AudioBackend


class WindowsBackend(AudioBackend):
    def list_devices(self):
        import sounddevice as sd

        devices = []
        for idx, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                devices.append(AudioDevice(name=dev["name"], index=idx, is_input=True))
        return devices

    def record(
        self,
        device,
        duration,
        output_file,
        progress_callback=None,
    ):
        import sounddevice as sd
        import numpy as np

        if device is None:
            device = self._get_default_input_device()

        if device is None:
            raise RuntimeError("No input device available")

        sample_rate = 44100
        channels = 1

        recording = []

        def callback(indata, frames, time_info, status):
            if status:
                print(status)
            recording.append(indata.copy())

        with sd.InputStream(
            device=device.index,
            channels=channels,
            samplerate=sample_rate,
            callback=callback,
        ):
            import time

            start_time = time.time()
            while True:
                time.sleep(0.1)
                if progress_callback:
                    progress_callback(time.time() - start_time)

                if duration and (time.time() - start_time) >= duration:
                    break

        if recording:
            audio_data = np.concatenate(recording, axis=0)
            audio_data = audio_data.flatten().astype(np.float32)

            import wave

            with wave.open(output_file, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())

    def _get_default_input_device(self):
        import sounddevice as sd

        devices = sd.query_devices()
        if isinstance(devices, list):
            for dev in devices:
                if dev["max_input_channels"] > 0:
                    return AudioDevice(name=dev["name"], index=dev["index"], is_input=True)
        else:
            if devices["max_input_channels"] > 0:
                return AudioDevice(name=devices["name"], index=devices["index"], is_input=True)
        return None