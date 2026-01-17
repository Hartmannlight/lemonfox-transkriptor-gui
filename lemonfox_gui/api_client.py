import requests

from .settings import AppSettings


def transcribe_audio(settings: AppSettings, source, source_type: str):
    url = f"{settings.api_base}/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {settings.api_token}"}

    data_list = [("response_format", settings.response_format)]
    if settings.language:
        data_list.append(("language", settings.language))
    if settings.prompt:
        data_list.append(("prompt", settings.prompt))
    if settings.translate:
        data_list.append(("translate", "true"))
    if settings.speaker_labels:
        data_list.append(("speaker_labels", "true"))
        if settings.min_speakers:
            data_list.append(("min_speakers", settings.min_speakers))
        if settings.max_speakers:
            data_list.append(("max_speakers", settings.max_speakers))
    if settings.word_timestamps and settings.response_format == "verbose_json":
        data_list.append(("timestamp_granularities[]", "word"))
    if settings.callback_url:
        data_list.append(("callback_url", settings.callback_url))

    files = None
    if source_type == "url":
        data_list.append(("file", source))
    else:
        files = {"file": open(source, "rb")}

    try:
        resp = requests.post(url, headers=headers, data=data_list, files=files, timeout=300)
    finally:
        if files is not None:
            files["file"].close()

    if not resp.ok:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")

    if settings.response_format in ("json", "verbose_json"):
        return resp.json(), None
    return None, resp.text
