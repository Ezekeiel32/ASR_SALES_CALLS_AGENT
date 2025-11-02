# Models Used in IvriMeet

## Active Models (Downloaded from HuggingFace)

### 1. **PyAnnote Speaker Diarization**
- **Model ID**: `pyannote/speaker-diarization-3.1`
- **Purpose**: Speaker diarization (identifying "who spoke when")
- **Size**: ~500MB - 1GB (includes multiple sub-models)
- **Location**: `agent_service/services/diarization_service.py`
- **Usage**: Validates and enhances speaker labels from Ivrit.ai transcription
- **Note**: Requires HuggingFace auth token (set `PYANNOTE_AUTH_TOKEN` in .env)

**What it does:**
- Takes audio file
- Returns segments with speaker labels (SPEAKER_00, SPEAKER_01, etc.)
- Provides timing for each speaker's turns
- Can handle overlapping speech better than Ivrit.ai alone

**Sub-models included:**
- Segmentation model (detects speech vs silence)
- Embedding model (speaker features)
- Clustering model (groups speakers)

---

### 2. **SpeechBrain Voiceprint Encoder**
- **Model ID**: `speechbrain/spkrec-ecapa-voxceleb`
- **Purpose**: Generate speaker voiceprints (embeddings)
- **Size**: ~100-200MB
- **Location**: `agent_service/services/voiceprint_service.py`
- **Usage**: Creates 192-dimensional embeddings to identify known speakers

**What it does:**
- Takes 15-second audio snippet
- Generates 192-dim embedding vector
- Embeddings stored in PostgreSQL with pgvector
- Used to match new speakers to known speakers (by voice)

**Model type**: ECAPA-TDNN (Efficient Channel Attention)

---

## Models NOT Downloaded (External APIs)

### 3. **Ivrit.ai Transcription**
- **Provider**: Ivrit.ai API (external service)
- **Purpose**: Hebrew speech-to-text transcription
- **Usage**: Via API call, no local model
- **Location**: `agent_service/clients/ivrit_client.py`

---

### 4. **DeepSeek Summarization**
- **Model**: `deepseek-ai/deepseek-v3.1-terminus`
- **Provider**: NVIDIA API (external service)
- **Purpose**: Generate meeting summaries
- **Usage**: Via NVIDIA API, no local model
- **Location**: `agent_service/summarizers/nvidia.py`

---

## Model Storage Strategy

### Before S3 Integration:
```
Container Disk:
├── ~/.cache/huggingface/         (~2-3GB)
│   ├── pyannote/                 (~500MB-1GB)
│   └── speechbrain/              (~200MB)
└── Audio files                   (Variable, can be huge)
Total: ~6GB+ (large container size, slow cold starts)
```

### After S3 Integration:
```
S3 Bucket:
├── models/
│   ├── pyannote_speaker-diarization-3.1/
│   └── speechbrain_spkrec-ecapa-voxceleb/
├── meetings/
│   └── {meeting_id}/
│       ├── audio.mp3
│       └── snippets/
│           └── {speaker}_snippet.wav
└── [Old models moved to Glacier after 90 days]

Container Disk (Koyeb):
├── /tmp/hf_cache/                (~100MB, cleaned on restart)
├── Code + dependencies           (~1GB)
└── Temp files                    (~100MB)
Total: ~1.2GB (small container, faster deployments)
```

---

## Model Download Flow

1. **First Time (Model not in S3)**:
   ```
   Request → Download from HuggingFace → Use locally → Upload to S3 → Delete local copy
   ```

2. **Subsequent Times (Model in S3)**:
   ```
   Request → Download from S3 → Use locally → Keep in temp cache → Auto-cleanup
   ```

3. **After Container Restart**:
   ```
   Temp cache cleared → Download from S3 again (fast, ~500MB)
   ```

---

## Configuration

### Environment Variables:

```bash
# S3 Storage
S3_BUCKET=ivrimeet-models
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# PyAnnote (optional - only if using PyAnnote diarization)
PYANNOTE_AUTH_TOKEN=your_huggingface_token

# Model Selection (optional)
PYANNOTE_MODEL=pyannote/speaker-diarization-3.1  # Default
```

---

## Model Sizes (Approximate)

| Model | Size | Purpose |
|-------|------|---------|
| `pyannote/speaker-diarization-3.1` | ~800MB | Speaker diarization |
| `speechbrain/spkrec-ecapa-voxceleb` | ~150MB | Voiceprint generation |
| **Total** | **~1GB** | Both models |

**Note**: These are downloaded on-demand. If PyAnnote isn't configured, only SpeechBrain (~150MB) is downloaded.

---

## Why Store in S3?

1. **Container Size**: Smaller containers = faster deployments and cold starts on Koyeb
2. **Cost**: S3 storage is cheaper than larger container storage tiers
3. **Speed**: Models download from S3 faster than HuggingFace (especially on subsequent runs)
4. **Scalability**: Multiple Koyeb services can share the same models from S3
5. **Persistence**: Models safe in S3 even if containers restart or redeploy
6. **Cold Starts**: Smaller container images mean faster cold start times

---

## Testing Models

```python
# Test PyAnnote
from agent_service.services.diarization_service import DiarizationService
service = DiarizationService()
segments = service.diarize(audio_path="test.wav")

# Test SpeechBrain
from agent_service.services.voiceprint_service import VoiceprintService
service = VoiceprintService()
embedding = service.generate_embedding(audio_path="snippet.wav")
```

