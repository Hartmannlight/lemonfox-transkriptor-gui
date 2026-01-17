# Lemonfox Speech-to-Text API (Whisper large-v3)

Lemonfox provides an OpenAI-compatible Speech-to-Text endpoint to transcribe audio (and common video containers) into plain text, JSON, subtitle formats (SRT/VTT), or a verbose JSON structure with segments, timestamps, and optional speaker diarization.

## Base URLs

- Global processing (default): `https://api.lemonfox.ai`
- EU-based processing (data processed within the EU): `https://eu-api.lemonfox.ai`  
  **Note:** EU-based processing has a **20% surcharge** compared to the default endpoint.

All examples below use the global endpoint. To switch to EU processing, replace `api.lemonfox.ai` with `eu-api.lemonfox.ai`.

## Authentication

All requests require a Bearer token:

- Header: `Authorization: Bearer <YOUR_API_KEY>`

Create/manage API keys in the Lemonfox dashboard.

## Endpoint

### Transcribe audio
`POST /v1/audio/transcriptions`

Full URL:
- `https://api.lemonfox.ai/v1/audio/transcriptions`

Request type:
- `multipart/form-data` (recommended; required for file upload)
- Form fields also support providing an audio file **via a public URL** (see `file` parameter).

---

## Parameters

### `file` (required)
The audio/video to transcribe. Two supported modes:

1) **Public URL** (Lemonfox downloads the file)
- Send as a form field `file=https://...`
- Max size via URL: **1GB**

2) **Upload a local file**
- Send as multipart file field named `file`
- Max upload size: **100MB**

Supported formats include (not exhaustive): `mp3`, `wav`, `flac`, `aac`, `opus`, `ogg`, `m4a`, `mp4`, `mpeg`, `mov`, `webm`, and more.

### `response_format` (optional, default: `json`)
Controls the output format. Allowed values:
- `json` – JSON object with transcript text
- `text` – plain text response body
- `srt` – subtitles (SRT)
- `vtt` – subtitles (VTT)
- `verbose_json` – rich JSON with segments, timestamps, and (optionally) speaker labels

### `language` (optional)
Language of the input audio. If omitted, Lemonfox auto-detects the language. Providing it can improve accuracy and latency.

Example values: `english`, `german`, `spanish`, … (Lemonfox supports 100+ languages).

### `prompt` (optional)
Text to guide style/wording or bias recognition toward specific terms. Should be in the same language as the audio.

Typical uses:
- Ensure acronyms/terms are recognized correctly (e.g., “NFT, DeFi, DAO”)
- Encourage punctuation (e.g., “Hello, welcome to the podcast.”)
- Keep filler words (e.g., “Umm, let’s see, hmm...”)

### `translate` (optional, boolean)
If `true`, translates the audio content to **English**.

### `timestamp_granularities[]` (optional, array)
Enable word-level timestamps by including `word`:
- `timestamp_granularities[]=word`

**Requires** `response_format=verbose_json`.

### `speaker_labels` (optional, boolean)
Enable speaker diarization (who spoke when). Set:
- `speaker_labels=true`

Recommendations:
- Also set `min_speakers` and/or `max_speakers` if you know the speaker count range.

**Important:** To access speaker labels, you must use:
- `response_format=verbose_json`

**Note:** Lemonfox states that OpenAI’s official SDK does not support speaker diarization, so this feature is not available via “OpenAI library” mode; use direct HTTP calls for diarization.

### `min_speakers`, `max_speakers` (optional)
Used with `speaker_labels=true` to improve diarization accuracy by constraining the speaker count.

### `callback_url` (optional, URL)
Asynchronous-style usage for long files:
- Lemonfox will send a `POST` to your `callback_url` once the transcription is ready.
- The callback payload will contain the transcript in the specified `response_format`.

**Note:** Lemonfox states OpenAI’s SDK doesn’t support asynchronous requests; use direct HTTP calls.

---

## Responses

### `response_format=json` (default)
Returns JSON like:
```json
{
  "text": "..."
}
````

### `response_format=text`

Returns plain text in the HTTP response body.

### `response_format=srt` / `vtt`

Returns subtitle text in SRT/VTT format in the HTTP response body.

### `response_format=verbose_json`

Returns JSON with additional metadata (commonly includes fields like `duration`, `segments`, and timestamps). When enabled, speaker diarization and word-level timestamps appear in this structure.

---

## Examples

## cURL

### 1) Transcribe from a public URL (JSON)

```bash
curl -X POST 'https://api.lemonfox.ai/v1/audio/transcriptions' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -F 'file=https://output.lemonfox.ai/wikipedia_ai.mp3' \
  -F 'language=english' \
  -F 'response_format=json'
```

### 2) Upload a local file (JSON)

```bash
curl -X POST 'https://api.lemonfox.ai/v1/audio/transcriptions' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -F 'file=@/path/to/audio.mp3' \
  -F 'language=english' \
  -F 'response_format=json'
```

### 3) Subtitles (SRT)

```bash
curl -X POST 'https://api.lemonfox.ai/v1/audio/transcriptions' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -F 'file=@/path/to/audio.mp4' \
  -F 'response_format=srt' > subtitles.srt
```

### 4) Verbose JSON + word timestamps + diarization

```bash
curl -X POST 'https://api.lemonfox.ai/v1/audio/transcriptions' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -F 'file=@/path/to/audio.wav' \
  -F 'response_format=verbose_json' \
  -F 'speaker_labels=true' \
  -F 'min_speakers=2' \
  -F 'max_speakers=4' \
  -F 'timestamp_granularities[]=word'
```

---

## Python (requests)

Install:

```bash
pip install requests
```

### 1) Transcribe from a public URL (JSON)

```python
import requests

url = 'https://api.lemonfox.ai/v1/audio/transcriptions'
headers = {'Authorization': 'Bearer YOUR_API_KEY'}

data = {
    'file': 'https://output.lemonfox.ai/wikipedia_ai.mp3',
    'language': 'english',
    'response_format': 'json',
}

resp = requests.post(url, headers=headers, data=data, timeout=120)
resp.raise_for_status()
print(resp.json()['text'])
```

### 2) Upload a local file (JSON)

```python
import requests

url = 'https://api.lemonfox.ai/v1/audio/transcriptions'
headers = {'Authorization': 'Bearer YOUR_API_KEY'}

data = {
    'language': 'english',
    'response_format': 'json',
}

with open('/path/to/audio.mp3', 'rb') as f:
    files = {'file': f}
    resp = requests.post(url, headers=headers, data=data, files=files, timeout=120)

resp.raise_for_status()
print(resp.json()['text'])
```

### 3) Get subtitles (SRT/VTT)

For `text`, `srt`, and `vtt`, the response is typically plain text:

```python
import requests

url = 'https://api.lemonfox.ai/v1/audio/transcriptions'
headers = {'Authorization': 'Bearer YOUR_API_KEY'}

data = {
    'file': 'https://output.lemonfox.ai/wikipedia_ai.mp3',
    'response_format': 'srt',
}

resp = requests.post(url, headers=headers, data=data, timeout=120)
resp.raise_for_status()

with open('subtitles.srt', 'w', encoding='utf-8') as f:
    f.write(resp.text)
```

### 4) Verbose JSON + diarization + word timestamps

Note the `timestamp_granularities[]` form field:

```python
import requests

url = 'https://api.lemonfox.ai/v1/audio/transcriptions'
headers = {'Authorization': 'Bearer YOUR_API_KEY'}

data = [
    ('response_format', 'verbose_json'),
    ('speaker_labels', 'true'),
    ('min_speakers', '2'),
    ('max_speakers', '4'),
    ('timestamp_granularities[]', 'word'),
]

with open('/path/to/audio.wav', 'rb') as f:
    files = {'file': f}
    resp = requests.post(url, headers=headers, data=data, files=files, timeout=300)

resp.raise_for_status()
payload = resp.json()

for seg in payload.get('segments', []):
    speaker = seg.get('speaker')
    start = seg.get('start')
    end = seg.get('end')
    text = seg.get('text')
    print(f'[{start:>6.2f}-{end:>6.2f}] {speaker}: {text}')
```

---

## JavaScript (fetch)

### 1) Transcribe from a public URL (JSON)

```js
const body = new FormData()
body.append('file', 'https://output.lemonfox.ai/wikipedia_ai.mp3')
body.append('language', 'english')
body.append('response_format', 'json')

const resp = await fetch('https://api.lemonfox.ai/v1/audio/transcriptions', {
  method: 'POST',
  headers: { Authorization: 'Bearer YOUR_API_KEY' },
  body
})

if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
const data = await resp.json()
console.log(data.text)
```

### 2) Upload a File object (browser)

```js
const body = new FormData()
body.append('file', fileInput.files[0]) // <input type="file" />
body.append('response_format', 'json')

const resp = await fetch('https://api.lemonfox.ai/v1/audio/transcriptions', {
  method: 'POST',
  headers: { Authorization: 'Bearer YOUR_API_KEY' },
  body
})

if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
console.log((await resp.json()).text)
```

---

## Operational notes / best practices

* If you know the language, set `language=...` to reduce latency and improve accuracy.
* Use `response_format=srt` or `vtt` for subtitles; store the response as a file.
* Use `response_format=verbose_json` for:

  * Segment timestamps
  * Word-level timestamps (`timestamp_granularities[]=word`)
  * Speaker diarization (`speaker_labels=true`)
* For diarization, set `min_speakers` / `max_speakers` if you have a good estimate.
* If you need EU processing, use `eu-api.lemonfox.ai` (expect a surcharge).
* Keep your API key secret; do not embed it in frontend code unless you proxy requests through your backend.
