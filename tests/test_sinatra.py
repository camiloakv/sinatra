import pytest
import sounddevice as sd
import yaml
import os
from pathlib import Path
from unittest.mock import patch

from sinatra.recorder.engine import RecordingEngine
from sinatra.cli import parse_args


class TestCLI:
    def test_parse_args_mic_only(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["sinatra", "-m"])
        args = parse_args()
        assert args.mic == True
        assert args.system == False

    def test_parse_args_system_only(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["sinatra", "-s"])
        args = parse_args()
        assert args.mic == False
        assert args.system == True

    def test_parse_args_both(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["sinatra", "-m", "-s"])
        args = parse_args()
        assert args.mic == True
        assert args.system == True

    def test_parse_args_with_verbose(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["sinatra", "-m", "-s", "-verbose", "2"])
        args = parse_args()
        assert args.verbose == 2

    def test_parse_args_with_gain(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["sinatra", "-m", "-gain", "2.5"])
        args = parse_args()
        assert args.gain == 2.5

    def test_parse_args_with_dir(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["sinatra", "-m", "-dir", "my_audios/"])
        args = parse_args()
        assert args.dir == "my_audios/"

    def test_parse_args_with_prefix(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["sinatra", "-m", "-prefix", "myrec"])
        args = parse_args()
        assert args.prefix == "myrec"

    def test_parse_args_list_devices(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["sinatra", "-list"])
        args = parse_args()
        assert args.list_devices == True

    def test_parse_args_default_device(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["sinatra", "-m", "-d", "0"])
        args = parse_args()
        assert args.device == 0


class TestDeviceDetection:
    def test_find_microphone_device(self):
        engine = RecordingEngine()
        
        mic_patterns = ["mic", "microphone"]
        loopback_patterns = ["stereo mix", "mezcla est", "loopback", "wave", "what u hear", "speaker", "sound mapper"]
        
        def is_loopback_device(name):
            name_lower = name.lower()
            return any(p in name_lower for p in loopback_patterns)
        
        def is_real_mic_device(name):
            name_lower = name.lower()
            return any(p in name_lower for p in mic_patterns) and not is_loopback_device(name)
        
        mic_device = None
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
                        break
                    except:
                        continue
        
        assert mic_device is not None, "Should find at least one working microphone device"

    def test_find_system_audio_device(self):
        engine = RecordingEngine()
        
        loopback_patterns = ["stereo mix", "mezcla est", "loopback", "wave", "what u hear"]
        
        def find_device_by_name(name_pattern):
            for i in range(len(sd.query_devices())):
                d = sd.query_devices(i)
                if name_pattern.lower() in d.get("name", "").lower():
                    return i, d
            return None, None
        
        sys_device = None
        for pattern in ["stereo mix", "mezcla estéreo", "loopback"]:
            idx, d = find_device_by_name(pattern)
            if idx is not None:
                try:
                    sr = int(d.get("default_samplerate", 44100))
                    ch = d.get("max_input_channels", 1)
                    with sd.InputStream(device=idx, channels=ch, samplerate=sr, callback=lambda *args: None):
                        pass
                    sys_device = idx
                    break
                except:
                    continue
        
        assert sys_device is not None, "Should find at least one working system audio device"


class TestEncoder:
    def test_find_ffmpeg(self):
        from sinatra.encoder import _find_ffmpeg
        result = _find_ffmpeg()
        assert result is None or result.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])