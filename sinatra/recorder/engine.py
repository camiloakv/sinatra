import sys
import time
from datetime import datetime
from pathlib import Path

from sinatra.config import load_config
from sinatra.encoder import encode_to_mp3


class RecordingEngine:
    def __init__(self):
        pass

    def record(
        self,
        mic: bool = False,
        system: bool = False,
        dir: str = "audios/",
        prefix: str = "rec",
        verbose: int = 0,
        gain: float = 1.0,
        device: int | None = None,
    ) -> str | None:
        import sounddevice as sd
        import numpy as np
        import wave

        if not mic and not system:
            mic = True

        input_type = "both" if (mic and system) else ("mic" if mic else ("speaker" if system else "mic"))

        timestamp = datetime.now().strftime("%Y%m%d-%H.%M.%S")
        filename = f"{prefix}_{input_type}_{timestamp}"
        output_dir = Path(dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        wav_file = output_dir / f"{filename}.wav"
        mp3_file = output_dir / f"{filename}.mp3"

        config = load_config()
        max_size_bytes = config.get("max_file_size_mb", 1024) * 1024 * 1024
        max_duration = config.get("max_duration_hours", 2) * 3600

        sample_rate = 44100
        channels = 1
        input_device = None
        stereo_mix_device = None

        def find_device_by_name(name_pattern):
            for i in range(len(sd.query_devices())):
                d = sd.query_devices(i)
                if name_pattern.lower() in d.get("name", "").lower():
                    return i, d
            return None, None

        if device is not None:
            d = sd.query_devices(device)
            input_device = device
            sample_rate = int(d.get("default_samplerate", 44100))
            actual_channels = d.get("max_input_channels", 1)
        elif system and not mic:
            default_output = sd.query_devices(kind="output")
            default_output_name = default_output.get("name", "").lower() if isinstance(default_output, dict) else ""
            
            candidates = []
            for pattern in ["stereo mix", "mezcla estéreo", "loopback", "wave", "what u hear", "hdmi"]:
                idx, d = find_device_by_name(pattern)
                if idx is not None and idx not in [x[0] for x in candidates]:
                    candidates.append((idx, d))
            
            if not candidates:
                for i in range(len(sd.query_devices())):
                    d = sd.query_devices(i)
                    if d.get("max_input_channels", 0) > 0:
                        name = d.get("name", "").lower()
                        if "mic" not in name and "microphone" not in name:
                            candidates.append((i, d))
            
            input_device = None
            capture_device_name = None
            for idx, d in candidates:
                try:
                    sample_rate = int(d.get("default_samplerate", 44100))
                    actual_channels = d.get("max_input_channels", 1)
                    with sd.InputStream(device=idx, channels=actual_channels, samplerate=sample_rate, callback=lambda *args: None):
                        pass
                    input_device = idx
                    capture_device_name = d.get("name", "")
                    break
                except Exception as e:
                    if verbose >= 2:
                        print(f"Device {idx} failed: {e}")
                    continue
            
            if input_device is None:
                if verbose >= 1:
                    print("No working system audio device found")
                return None
            
            if "bluetooth" in default_output_name or "headphone" in default_output_name or "headset" in default_output_name:
                if verbose >= 1:
                    print(f"WARNING: Recording from {capture_device_name[:40]} but default output is {default_output.get('name', '')[:40]}")
                    print("Note: Stereo Mix may not capture Bluetooth/USB audio. Use speakers for system audio capture.")
        elif mic and not system:
            mic_patterns = ["mic", "microphone"]
            loopback_patterns = ["stereo mix", "mezcla est", "loopback", "wave", "what u hear", "speaker", "sound mapper"]
            
            def is_loopback_device(name):
                name_lower = name.lower()
                return any(p in name_lower for p in loopback_patterns)
            
            def is_real_mic_device(name):
                name_lower = name.lower()
                return any(p in name_lower for p in mic_patterns) and not is_loopback_device(name)
            
            mic_device = None
            mic_sample_rate = 44100
            
            for i in range(len(sd.query_devices())):
                d = sd.query_devices(i)
                if d.get("max_input_channels", 0) > 0:
                    name = d.get("name", "")
                    if is_real_mic_device(name):
                        try:
                            sr = int(d.get("default_samplerate", 44100))
                            ch = d.get("max_input_channels", 1)
                            with sd.InputStream(device=i, channels=ch, samplerate=sr, callback=lambda *args: None):
                                pass
                            mic_device = i
                            mic_sample_rate = sr
                            if verbose >= 1:
                                print(f"Using microphone device {i}: {name[:50]}")
                            break
                        except:
                            continue
            
            if mic_device is None:
                if verbose >= 1:
                    print("No microphone device found")
                return None
            
            input_device = mic_device
            sample_rate = mic_sample_rate
            actual_channels = 1
        elif mic and system:
            mic_patterns = ["mic", "microphone"]
            loopback_patterns = ["stereo mix", "mezcla est", "loopback", "wave", "what u hear", "speaker", "sound mapper"]
            
            def is_loopback_device(name):
                name_lower = name.lower()
                return any(p in name_lower for p in loopback_patterns)
            
            def is_real_mic_device(name):
                name_lower = name.lower()
                return any(p in name_lower for p in mic_patterns) and not is_loopback_device(name)
            
            mic_device = None
            mic_sample_rate = 44100
            sys_device = None
            sys_sample_rate = 44100
            
            for i in range(len(sd.query_devices())):
                d = sd.query_devices(i)
                if d.get("max_input_channels", 0) > 0:
                    name = d.get("name", "")
                    if is_real_mic_device(name):
                        try:
                            sr = int(d.get("default_samplerate", 44100))
                            ch = d.get("max_input_channels", 1)
                            with sd.InputStream(device=i, channels=ch, samplerate=sr, callback=lambda *args: None):
                                pass
                            mic_device = i
                            mic_sample_rate = sr
                            break
                        except:
                            continue
            
            candidates = []
            for pattern in ["stereo mix", "mezcla estéreo", "loopback"]:
                idx, d = find_device_by_name(pattern)
                if idx is not None:
                    candidates.append((idx, d))
            
            for idx, d in candidates:
                try:
                    sr = int(d.get("default_samplerate", 44100))
                    ch = d.get("max_input_channels", 1)
                    with sd.InputStream(device=idx, channels=ch, samplerate=sr, callback=lambda *args: None):
                        pass
                    sys_device = idx
                    sys_sample_rate = sr
                    break
                except:
                    continue
            
            if mic_device is not None and sys_device is not None:
                if verbose >= 1:
                    print(f"Recording both: mic device {mic_device}, system device {sys_device}")
                return self._record_both(
                    mic_device=mic_device,
                    sys_device=sys_device,
                    mic_sample_rate=mic_sample_rate,
                    sys_sample_rate=sys_sample_rate,
                    max_duration=max_duration,
                    max_size_bytes=max_size_bytes,
                    verbose=verbose,
                    gain=gain,
                    output_dir=output_dir,
                    filename=filename,
                )
            elif mic_device is not None:
                input_device = mic_device
                sample_rate = mic_sample_rate
                actual_channels = 1
                if verbose >= 1:
                    print("System audio device not available, recording mic only")
            elif sys_device is not None:
                input_device = sys_device
                sample_rate = sys_sample_rate
                actual_channels = d.get("max_input_channels", 1)
                if verbose >= 1:
                    print("Mic device not available, recording system audio only")
            else:
                if verbose >= 1:
                    print("No audio input devices available")
                return None
        else:
            try:
                default_input = sd.query_devices(kind="input")
                if isinstance(default_input, dict):
                    input_device = default_input["index"]
                    sample_rate = int(default_input["default_samplerate"])
                else:
                    input_device = default_input
            except Exception:
                devices = sd.query_devices()
                for dev in devices:
                    if dev["max_input_channels"] > 0:
                        input_device = dev["index"]
                        break
            actual_channels = 1

        if input_device is None:
            if verbose >= 1:
                print("No input device available")
            return None

        start_time = time.time()
        last_elapsed = 0
        recording = []

        def audio_callback(indata, frames, time_info, status):
            if status:
                pass
            recording.append(indata.copy())

        try:
            with sd.InputStream(
                device=input_device,
                channels=actual_channels,
                samplerate=sample_rate,
                callback=audio_callback,
            ) as stream:
                while True:
                    time.sleep(0.1)
                    elapsed = time.time() - start_time

                    if verbose >= 2 and int(elapsed) > last_elapsed:
                        sys.stderr.write(f"Recording: {int(elapsed)}s\n")
                        last_elapsed = int(elapsed)

                    if elapsed >= max_duration:
                        break

                    total_bytes = sum(arr.nbytes for arr in recording)
                    if total_bytes >= max_size_bytes:
                        break
        except KeyboardInterrupt:
            pass
        except Exception as e:
            if verbose >= 1:
                sys.stderr.write(f"Error: {e}\n")

        if recording:
            audio_data = np.concatenate(recording, axis=0)
            if actual_channels == 2:
                audio_data = audio_data.mean(axis=1)
            else:
                audio_data = audio_data.flatten()
            
            if gain != 1.0:
                audio_data = audio_data * gain
            
            audio_data = np.clip(audio_data, -1.0, 1.0)
            audio_int16 = (audio_data * 32767).astype(np.int16)

            with wave.open(str(wav_file), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_int16.tobytes())

        if wav_file.exists():
            output_file = mp3_file
            try:
                encode_to_mp3(str(wav_file), str(mp3_file))
                wav_file.unlink()
            except RuntimeError as e:
                if "ffmpeg" in str(e).lower():
                    if verbose >= 1:
                        sys.stderr.write(f"Warning: ffmpeg not found, saving as WAV\n")
                    output_file = wav_file.with_suffix(".wav")
                    wav_file.rename(output_file)
                else:
                    raise

            if verbose >= 1:
                print(f"Saved to {output_file}")

            return str(output_file)

        return None

    def _record_both(
        self,
        mic_device,
        sys_device,
        mic_sample_rate,
        sys_sample_rate,
        max_duration,
        max_size_bytes,
        verbose,
        gain,
        output_dir,
        filename,
    ):
        import sounddevice as sd
        import numpy as np
        import wave

        wav_file = output_dir / f"{filename}.wav"
        mp3_file = output_dir / f"{filename}.mp3"

        recording_mic = []
        recording_sys = []
        start_time = time.time()
        last_elapsed = 0

        def mic_callback(indata, frames, time_info, status):
            if status:
                pass
            recording_mic.append(indata.copy())

        def sys_callback(indata, frames, time_info, status):
            if status:
                pass
            recording_sys.append(indata.copy())

        try:
            with sd.InputStream(
                device=mic_device,
                channels=1,
                samplerate=mic_sample_rate,
                callback=mic_callback,
            ) as mic_stream, sd.InputStream(
                device=sys_device,
                channels=2,
                samplerate=sys_sample_rate,
                callback=sys_callback,
            ) as sys_stream:
                while True:
                    time.sleep(0.1)
                    elapsed = time.time() - start_time

                    if verbose >= 2 and int(elapsed) > last_elapsed:
                        sys.stderr.write(f"Recording: {int(elapsed)}s\n")
                        last_elapsed = int(elapsed)

                    if elapsed >= max_duration:
                        break

                    total_bytes = sum(arr.nbytes for arr in recording_mic + recording_sys)
                    if total_bytes >= max_size_bytes:
                        break
        except KeyboardInterrupt:
            pass
        except Exception as e:
            if verbose >= 1:
                sys.stderr.write(f"Error: {e}\n")

        if recording_mic or recording_sys:
            audio_data = []
            if recording_mic:
                mic_data = np.concatenate(recording_mic, axis=0).flatten()
                audio_data.append(mic_data)
            if recording_sys:
                sys_data = np.concatenate(recording_sys, axis=0)
                if sys_data.shape[1] > 1:
                    sys_data = sys_data.mean(axis=1)
                else:
                    sys_data = sys_data.flatten()
                audio_data.append(sys_data)

            if len(audio_data) == 2:
                min_len = min(len(audio_data[0]), len(audio_data[1]))
                audio_data = (audio_data[0][:min_len] + audio_data[1][:min_len]) / 2
            else:
                audio_data = audio_data[0]

            if gain != 1.0:
                audio_data = audio_data * gain

            audio_data = np.clip(audio_data, -1.0, 1.0)
            audio_int16 = (audio_data * 32767).astype(np.int16)

            sample_rate = (mic_sample_rate + sys_sample_rate) // 2

            with wave.open(str(wav_file), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_int16.tobytes())

        if wav_file.exists():
            output_file = mp3_file
            try:
                encode_to_mp3(str(wav_file), str(mp3_file))
                wav_file.unlink()
            except RuntimeError as e:
                if "ffmpeg" in str(e).lower():
                    if verbose >= 1:
                        sys.stderr.write(f"Warning: ffmpeg not found, saving as WAV\n")
                    output_file = wav_file.with_suffix(".wav")
                    wav_file.rename(output_file)
                else:
                    raise

            if verbose >= 1:
                print(f"Saved to {output_file}")

            return str(output_file)

        return None