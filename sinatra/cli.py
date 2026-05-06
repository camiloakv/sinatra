import argparse
from dataclasses import dataclass


@dataclass
class Args:
    mic: bool = False
    system: bool = False
    dir: str = "audios/"
    prefix: str = "rec"
    verbose: int = 0
    gain: float = 1.0
    device: int | None = None
    list_devices: bool = False


def parse_args() -> Args:
    parser = argparse.ArgumentParser(prog="sinatra", add_help=False)

    parser.add_argument(
        "-m", dest="mic", action="store_true", help="Record microphone"
    )
    parser.add_argument(
        "-s", dest="system", action="store_true", help="Record system/speaker audio"
    )
    parser.add_argument(
        "-dir", dest="dir", type=str, default="audios/", help="Output directory"
    )
    parser.add_argument(
        "-prefix", dest="prefix", type=str, default="rec", help="Filename prefix"
    )
    parser.add_argument(
        "-verbose",
        dest="verbose",
        type=int,
        default=0,
        choices=[0, 1, 2],
        help="Verbosity level (0=silent, 1=finish msg, 2=elapsed)",
    )
    parser.add_argument(
        "-gain",
        dest="gain",
        type=float,
        default=1.0,
        help="Audio gain multiplier (default 1.0)",
    )
    parser.add_argument(
        "-d",
        dest="device",
        type=int,
        default=None,
        help="Input device index (use -list to see available)",
    )
    parser.add_argument(
        "-list",
        dest="list_devices",
        action="store_true",
        help="List available audio devices",
    )

    args = parser.parse_args()

    return Args(
        mic=args.mic,
        system=args.system,
        dir=args.dir,
        prefix=args.prefix,
        verbose=args.verbose,
        gain=args.gain,
        device=args.device,
        list_devices=args.list_devices,
    )