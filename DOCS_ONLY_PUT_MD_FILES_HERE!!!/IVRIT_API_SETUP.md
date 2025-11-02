# IVRIT.AI API Configuration Guide

## Overview

The IvriMeet backend supports two modes for Hebrew transcription via Ivrit.ai:

1. **Direct Ivrit.ai API** - Direct API calls to `https://api.ivrit.ai`
2. **RunPod Serverless** - Using Ivrit.ai model deployed on RunPod Serverless

## Configuration

### Option 1: Direct Ivrit.ai API

Add your API key to `.env`:

```bash
IVRIT_API_KEY=your_api_key_here
```

**Required Settings:**
- `IVRIT_API_KEY` - Your Ivrit.ai API key

**Optional Settings:**
- `IVRIT_API_URL` - Default: `https://api.ivrit.ai`
- `IVRIT_TRANSCRIBE_PATH` - Default: `/v1/transcribe`
- `IVRIT_LANGUAGE` - Default: `he` (Hebrew)

### Option 2: RunPod Serverless

If you're using RunPod to host the Ivrit.ai model:

```bash
IVRIT_API_KEY=your_runpod_api_key
IVRIT_RUNPOD_ENDPOINT_ID=your_endpoint_id
```

**Required Settings:**
- `IVRIT_API_KEY` - Your RunPod API key
- `IVRIT_RUNPOD_ENDPOINT_ID` - Your RunPod endpoint ID

**Optional Settings:**
- `IVRIT_RUNPOD_MODE` - `runsync` (default) or `run`
- `IVRIT_RUNPOD_BASE_URL` - Default: `https://api.runpod.ai/v2`

## How It Works

### Direct API Mode
1. Audio file is sent as multipart/form-data to `https://api.ivrit.ai/v1/transcribe`
2. API key is sent as `Authorization: Bearer {API_KEY}` header
3. Returns transcription with speaker segments

### RunPod Mode
1. Audio is base64-encoded and sent as JSON
2. If `runsync`: Waits for synchronous response
3. If `run`: Creates job and polls status until completion
4. Returns transcription with speaker segments

## Getting an API Key

### Ivrit.ai Direct API
1. Visit [Ivrit.ai](https://ivrit.ai) or contact Ivrit.ai for API access
2. Sign up for an account
3. Generate an API key from your dashboard
4. Add it to `.env` as `IVRIT_API_KEY`

### RunPod Serverless
1. Create a RunPod account at [runpod.io](https://runpod.io)
2. Deploy the Ivrit.ai model as a Serverless endpoint
3. Get your RunPod API key from account settings
4. Get your endpoint ID from the Serverless endpoint page
5. Add both to `.env`

## Current Configuration

Check your current setup:

```bash
grep IVRIT .env
```

## Testing

Once configured, test the API:

```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@test_audio.wav" \
  -H "Content-Type: multipart/form-data"
```

Or use the Swagger UI at http://localhost:8000/docs

## Notes

- The system automatically prefers RunPod if `IVRIT_RUNPOD_ENDPOINT_ID` is set
- Otherwise, it uses the direct Ivrit.ai API
- Both modes extract speaker labels and segments automatically
- Language defaults to Hebrew (`he`) but can be overridden per request

## Troubleshooting

### API Key Not Working
- Verify the key is correct
- Check for extra spaces in `.env` file
- Ensure the backend has been restarted after adding the key

### RunPod Issues
- Verify endpoint ID is correct
- Check RunPod endpoint status
- Ensure RunPod API key has access to the endpoint

### No Transcription
- Check audio format is supported (WAV, MP3, M4A, AAC, WebM)
- Verify API quota/limits
- Check backend logs for error messages

