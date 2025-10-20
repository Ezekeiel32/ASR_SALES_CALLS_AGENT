ASR Sales Calls Agent
======================

End-to-end agent for Hebrew medical sales calls:

- Transcribe audio via Ivrit.ai (RunPod Serverless)
- Summarize and analyze via NVIDIA DeepSeek (OpenAI-compatible API)
- Expose Power Automate–friendly HTTP endpoints
- CLI for local batch runs, with JSON/TXT/SRT and Markdown outputs

Repository: https://github.com/Ezekeiel32/ASR_SALES_CALLS_AGENT


Features
--------

- FastAPI service with endpoints:
  - `POST /transcribe`: accepts file upload, raw audio, URL, or base64 → returns transcript, segments, SRT, TXT
  - `POST /analyze`: accepts transcript → returns Markdown summary and structured analysis JSON
- RunPod Serverless integration for Ivrit.ai (base64 blob input, polling for completion)
- NVIDIA DeepSeek v3.1 Terminus summarization via OpenAI-compatible client
- CLI supports:
  - Full pipeline: transcribe + summarize
  - Summarize-only from an existing transcript (`--from-transcript`)
  - Multi-variant outputs via `--variant`
- Outputs saved alongside the audio or to `agent_service/agent_out/` during runs:
  - Transcript: `.transcript.{json,txt}`
  - Captions: `.captions.srt`
  - Analysis: `.analysis.{md,json,txt}`


Architecture (High-level)
-------------------------

1) Ingestion: Audio (MP3/WAV/M4A/AAC) → Ivrit.ai via RunPod → transcript + segments
2) Analysis: Transcript → NVIDIA DeepSeek → Markdown summary + analysis JSON
3) Automation: Power Automate orchestrates SharePoint writes for Audio, Transcripts, Analyses


Requirements
------------

- Python 3.11+
- A RunPod Serverless endpoint backed by an Ivrit.ai Whisper-compatible worker
- NVIDIA API key for `integrate.api.nvidia.com`


Quick Start
-----------

1) Clone and install

```
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

2) Environment

```
export IVRIT_API_KEY="<runpod_api_key>"
export IVRIT_RUNPOD_ENDPOINT_ID="<runpod_endpoint_id>"
export IVRIT_RUNPOD_MODE="runsync"   # or "run" (polling)
export IVRIT_MODEL="large-v3-turbo"  # whisper size supported by your Ivrit.ai worker

export NVIDIA_API_KEY="<nvidia_api_key>"
export NVIDIA_API_URL="https://integrate.api.nvidia.com/v1"
```

3) Run the CLI

```
python -m agent_service.cli \
  -w \
  "/path/to/audio.aac"

# Variants (avoid overwriting)
python -m agent_service.cli -w --variant v1 "/path/to/audio.aac"

# Summarize-only from existing transcript
python -m agent_service.cli -w --variant v2 \
  --from-transcript "/path/to/audio.transcript.json" \
  "/path/to/audio.aac"
```

Outputs are written next to the audio path or to `agent_service/agent_out/` depending on run context.


Run the API
-----------

```
uvicorn agent_service.api:app --host 0.0.0.0 --port 8000
# Open interactive docs: http://localhost:8000/docs
```

### POST /transcribe

Accepts one of:

- multipart/form-data file: `file`
- raw audio body with headers `x-filename`, `x-language` (optional)
- JSON `{ url, language?, filename? }`
- JSON `{ base64, language?, filename? }`

Response example (truncated):

```
{
  "transcript": "...",
  "segments": [
    {"start": 0.0, "end": 2.5, "text": "...", "words": [...]},
    ...
  ],
  "srt": "1\n00:00:00,000 --> 00:00:02,520\n...\n\n",
  "txt": "..."
}
```

### POST /analyze

Request:

```
{
  "transcript": "...",
  "sourceAudio": "https://.../Audio%20Uploads/file.wav",
  "transcriptFile": "https://.../Transcripts/file.transcript.json"
}
```

Response:

```
{
  "summary_markdown": "...",
  "analysis": {
    "sourceAudio": "...",
    "transcriptFile": "...",
    "summary": "...",
    "keyPoints": ["..."],
    "actionItems": [],
    "entities": {},
    "sentiment": null,
    "topics": [],
    "confidence": null,
    "runId": "nvidia-...",
    "createdAt": "2025-10-20T...Z"
  }
}
```


Environment Variables
---------------------

- Ivrit.ai / RunPod (transcription)
  - `IVRIT_API_KEY`: RunPod API token (Authorization header)
  - `IVRIT_RUNPOD_ENDPOINT_ID`: Your RunPod Serverless endpoint ID
  - `IVRIT_RUNPOD_MODE`: `runsync` or `run` (polling)
  - `IVRIT_MODEL`: Whisper model size expected by your worker (e.g., `large-v3-turbo`)
  - Optional advanced:
    - `IVRIT_INPUT_AUDIO_FIELD` (default: `audio`)
    - `IVRIT_INPUT_LANGUAGE_FIELD` (default: `language`)
    - `IVRIT_INPUT_FILENAME_FIELD` (default: `filename`)
    - `IVRIT_TRANSCRIBE_ARGS_FIELD` (default: `transcribe_args`)
    - `IVRIT_RETURN_SEGMENTS` (default: `true`)

- NVIDIA (summarization)
  - `NVIDIA_API_KEY`: API key for `integrate.api.nvidia.com`
  - `NVIDIA_API_URL`: API base URL (`https://integrate.api.nvidia.com/v1`)
  - Optional via config: model (`deepseek-ai/deepseek-v3.1-terminus`), temperature, top_p, max_tokens


Power Automate (SharePoint) Flows
---------------------------------

Two-flow pattern (recommended):

Flow 1: Audio → ivrit.ai

1. Trigger: When a file is created in SharePoint Library A (Audio Uploads)
2. Get file content
3. HTTP: POST to `/transcribe` with raw body (audio bytes) or `{ url }`
4. Create files in Library B (Transcripts):
   - `filename.transcript.txt`
   - `filename.transcript.json`
   - `filename.captions.srt`
   - Metadata: `SourceAudioLink`, `IvritJobId` (if available), `Duration`, `AvgConfidence` (optional), `Status=Transcribed`
5. Error handling: set item `Status=Transcription_Failed`, write `ErrorMessage`

Flow 2: Transcript → NVIDIA analysis

1. Trigger: When a file is created in Library B filtered by `.transcript.json`
2. HTTP: POST `/analyze` with `{ transcript: <txt or JSON field>, sourceAudio, transcriptFile }`
3. Create files in Library C (Analyses):
   - `filename.analysis.md`
   - `filename.analysis.json`
   - Metadata: `TranscriptLink`, `Status=Complete`, `CopilotRunId` (here: NVIDIA run id)
4. Update transcript item `Status=Analyzed`

Libraries & Columns (suggested)

- Library A – Audio Uploads: `Status`, `LanguageHint`, `Project`, `IvritJobId`, `ErrorMessage`
- Library B – Transcripts: `Status`, `SourceAudioLink`, `Duration`, `SpeakerCount`, `AvgConfidence`, `IvritJobId`, `ErrorMessage`
- Library C – Analyses: `Status`, `TranscriptLink`, `RunId`, `PIIFlag`, `Sensitivity`


Outputs & File Naming
---------------------

- Transcript text: `<base>.transcript.txt`
- Transcript JSON: `<base>.transcript.json` (contains `transcript`, `segments`, `sourceFile`, `createdAt`)
- Captions (SRT): `<base>.captions.srt`
- Analysis Markdown: `<base>.analysis.md`
- Analysis JSON: `<base>.analysis.json` (includes `keyPoints`, `actionItems`, `entities`, etc.)
- Variants: append `.vN` before suffix (e.g., `.v3.analysis.md`) using CLI `--variant`


Troubleshooting
---------------

- `NVIDIA API key not configured. Set NVIDIA_API_KEY.`
  - Export `NVIDIA_API_KEY` and re-run

- RunPod `Model not provided.` or invalid model size
  - Set `IVRIT_MODEL` to a supported model for your worker (e.g., `large-v3-turbo`)

- RunPod `transcribe_args field not provided.` or `transcribe_args must contain either 'blob' or 'url'.`
  - Ensure the worker expects `transcribe_args` and that the client sends base64 blob

- RunPod `status: IN_PROGRESS` forever or `executionTimeout exceeded`
  - Use `IVRIT_RUNPOD_MODE=run` to submit a job and poll `/status/{id}` until completion

- Empty SRT files
  - Some RunPod templates nest segments under `output → result` (list-of-lists). This project parses those structures and will populate SRTs if segments exist.

- CLI multi-variant summaries without re-transcription
  - Use `--from-transcript` with an existing `.transcript.json` and vary temperature via env/config (or simply different `--variant` tags)


Security & Compliance
---------------------

- Do not commit secrets; use environment variables or a secrets manager
- Add an API key middleware or gateway in front of FastAPI if exposing publicly
- Handle PII: redact names/IDs in summaries and apply SharePoint sensitivity labels as needed


Development Notes
-----------------

- Code entry points:
  - API: `agent_service/api.py`
  - CLI: `agent_service/cli.py`
  - Ivrit client: `agent_service/clients/ivrit_client.py`
  - Summarizer: `agent_service/summarizers/nvidia.py`
- Lint/type checks: run your preferred tools; ensure `requirements.txt` is installed
- FastAPI docs: `GET /docs`, health: `GET /healthz`


Acknowledgements
----------------

- Ivrit.ai ASR and RunPod Serverless hosting
- NVIDIA DeepSeek v3.1 Terminus on `integrate.api.nvidia.com`


