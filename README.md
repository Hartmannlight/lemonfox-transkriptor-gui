# Lemonfox Transkriptor GUI

Simple Tkinter GUI for recording audio and sending it to the Lemonfox Speech-to-Text API.

## Run

```bash
poetry install --no-root
poetry run python -m lemonfox_gui
```

## Release (Windows EXE)

Tag and push to trigger the GitHub Actions build:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The workflow uploads `LemonfoxTranskriptor.exe` to the GitHub Release and as a build artifact.

## Manual test checklist

- Open Settings and set API token, audio/text folders, and language.
- Hold the Record button to capture audio and release to send.
- Enable Toggle mode, start/stop recording with a single click.
- Use "Transcribe File" and "Transcribe URL" to verify non-record inputs.
- Confirm transcript text appears in the textbox and JSON files are saved.
