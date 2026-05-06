from .cli import parse_args
from .recorder.engine import RecordingEngine
import sounddevice as sd


def main():
    args = parse_args()

    if args.list_devices:
        print("Available audio devices:")
        for i in range(len(sd.query_devices())):
            d = sd.query_devices(i)
            in_ch = d.get("max_input_channels", 0)
            out_ch = d.get("max_output_channels", 0)
            if in_ch > 0 or out_ch > 0:
                print(f"  {i}: {d.get('name', '')[:60]} (in:{in_ch} out:{out_ch})")
        return

    engine = RecordingEngine()
    engine.record(
        mic=args.mic,
        system=args.system,
        dir=args.dir,
        prefix=args.prefix,
        verbose=args.verbose,
        gain=args.gain,
        device=args.device,
    )


if __name__ == "__main__":
    main()