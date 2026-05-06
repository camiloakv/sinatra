Sinatra

Command line audio capturing tool

## Version

Current version supports simultaneous recording of microfone and/or speaker on Windows. Does not support:

- Bluetooth headphones
- Other OS

## Usage

Start recording with following commands, safely end with `Ctrl+C`.

- `python -m sinatra` defaults to recording only microphone

- `python -m sinatra -s -m -gain 2 -verbose 2 -prefix party -dir somedir`
