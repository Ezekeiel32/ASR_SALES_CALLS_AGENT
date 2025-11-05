"""LangGraph workflow for ASR Sales Calls Agent meeting processing."""

from __future__ import annotations

from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import uuid
import logging
import json

logger = logging.getLogger(__name__)


class ASRMeetingState(TypedDict):
	"""
	Represents the state of the ASR meeting processing workflow.
	"""
	meeting_id: str
	organization_id: str
	audio_s3_key: Optional[str]
	audio_bytes: Optional[bytes]
	audio_path: Optional[str]
	
	# Processing results
	transcription_result: Optional[dict]
	ivrit_segments: List[dict]
	pyannote_segments: Optional[List[dict]]
	merged_segments: List[dict]
	speaker_labels: List[str]
	speaker_segments: List[dict]
	
	# Speaker identification
	speaker_snippets: List[dict]
	speaker_voiceprints: dict[str, Optional[List[float]]]
	matched_speakers: dict[str, dict]
	
	# Name extraction
	name_suggestions: List[dict]
	
	# Summarization
	summary: Optional[str]
	key_points: List[str]
	action_items: List[str]
	
	# Communication Health Analysis (for meeting transcripts)
	preprocessed_transcript: Optional[str]  # Full transcript text
	communication_health_scores: dict  # Per-speaker and overall scores
	aggregated_health: dict  # Consolidated results
	health_explanation: Optional[str]  # Natural language explanation
	
	# Status
	status: str
	error: Optional[str]


class ASRWorkflow:
	"""
	ASR Sales Calls Agent workflow for processing meetings.
	
	This workflow orchestrates the complete meeting processing pipeline:
	1. Audio Transcription (Ivrit.ai API)
	2. Speaker Diarization (Ivrit.ai + PyAnnote.audio)
	3. Diarization Merging (Custom algorithm)
	4. Speaker Snippet Extraction (Audio processing)
	5. Voiceprint Generation & Matching (SpeechBrain ECAPA-TDNN + Cosine Similarity)
	6. Hebrew Name Extraction (NLP-based)
	7. Speaker-Aware Summarization (DeepSeek LLM)
	"""
	
	def __init__(self):
		from agent_service.config import get_settings
		
		self.settings = get_settings()
		# Initialize LLM for communication health analysis
		self.llm = ChatNVIDIA(
			model=self.settings.nvidia_model,
			temperature=self.settings.nvidia_temperature,
			max_tokens=self.settings.nvidia_max_tokens,
			api_key=self.settings.nvidia_api_key,
			base_url=self.settings.nvidia_api_url,
			extra_body={"chat_template_kwargs": {"thinking": self.settings.nvidia_enable_thinking}},
		)
		# Note: Orchestrator is imported lazily when needed to avoid heavy dependencies
		# For LangGraph Studio visualization, we just need the workflow structure
	
	def transcribe_audio_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 1: Audio Transcription via Ivrit.ai API
		
		Algorithm: Ivrit.ai ASR Service (Hebrew-focused speech recognition)
		- Input: Audio bytes/file
		- Output: Text transcript with timestamped segments
		- Includes basic speaker diarization (SPK_1, SPK_2, etc.)
		
		Rating Principle: 
		- Transcription quality measured by confidence scores from Ivrit.ai
		- Segments with low confidence flagged for review
		"""
		logger.info("Node 1/7: Transcription via Ivrit.ai")
		# This would be implemented using ProcessingOrchestrator
		# For now, marking as placeholder
		state["status"] = "transcribing"
		return state
	
	def diarize_pyannote_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 2: PyAnnote Diarization Validation
		
		Algorithm: PyAnnote.audio speaker diarization model
		- Model: pyannote/speaker-diarization-3.1
		- Input: Audio file/bytes
		- Output: Speaker-labeled segments with timestamps
		
		Rating Principle:
		- Overlap detection: Segments with speaker overlap flagged
		- Confidence threshold: Low-confidence segments require review
		- Speaker count validation: Validates against Ivrit.ai speaker count
		"""
		logger.info("Node 2/7: PyAnnote diarization validation")
		state["status"] = "diarizing"
		return state
	
	def merge_diarization_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 3: Merge Diarization Results
		
		Algorithm: Custom DiarizationMerger algorithm
		- Combines Ivrit.ai and PyAnnote results
		- Time-window based alignment
		- Confidence-weighted consensus
		
		Rating Principle:
		- Agreement score: Higher when both systems agree on speaker
		- Disagreement resolution: Uses PyAnnote for high-confidence segments
		- Final confidence: Weighted average of both systems' confidence
		"""
		logger.info("Node 3/7: Merging diarization results")
		state["status"] = "merging"
		return state
	
	def extract_snippets_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 4: Extract Speaker Audio Snippets
		
		Algorithm: Audio processing with FFmpeg
		- Extracts 15-second representative snippets per speaker
		- Selects snippets with highest audio quality (SNR)
		- Stores snippets in S3 for voiceprint generation
		
		Rating Principle:
		- Audio quality score: SNR (Signal-to-Noise Ratio)
		- Selection: Highest quality snippet per speaker
		- Minimum duration: 10 seconds required for reliable voiceprint
		"""
		logger.info("Node 4/7: Extracting speaker snippets")
		state["status"] = "extracting_snippets"
		return state
	
	def generate_voiceprints_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 5: Generate Voiceprints & Match Speakers
		
		Algorithm: SpeechBrain ECAPA-TDNN embedding model
		- Model: speechbrain/spkrec-ecapa-voxceleb
		- Input: 15-second audio snippets
		- Output: 192-dimensional embedding vectors
		- Matching: Cosine similarity search in PostgreSQL (pgvector)
		
		Rating Principle:
		- Similarity threshold: 0.9 (90% similarity) for match
		- Ranking: Cosine similarity scores, highest first
		- Multiple matches: Closest match above threshold
		"""
		logger.info("Node 5/7: Generating voiceprints and matching speakers")
		state["status"] = "matching_speakers"
		return state
	
	def extract_names_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 6: Extract Hebrew Names & Create Suggestions
		
		Algorithm: Custom Hebrew NLP + Pattern matching
		- Hebrew name pattern recognition
		- Context-based name extraction from transcript
		- Database lookup for known speakers in organization
		
		Rating Principle:
		- Confidence score: Based on pattern match quality
		- Context relevance: Names mentioned in greeting/introduction get higher score
		- Frequency: Names mentioned multiple times get higher confidence
		"""
		logger.info("Node 6/7: Extracting Hebrew names")
		state["status"] = "extracting_names"
		return state
	
	def summarize_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 7: Speaker-Aware Summarization
		
		Algorithm: DeepSeek LLM (via NVIDIA API)
		- Model: deepseek-ai/deepseek-v3.1-terminus
		- Input: Full transcript with speaker labels
		- Output: Structured summary with key points, action items
		
		Rating Principle:
		- Completeness: Coverage of all speakers and topics
		- Actionability: Clear, specific action items extracted
		- Relevance: Key points ranked by importance
		"""
		logger.info("Node 7/13: Generating speaker-aware summary")
		state["status"] = "summarizing"
		# Also prepare transcript for communication health analysis
		if state.get("merged_segments"):
			transcript_text = "\n".join([
				f"{seg.get('speaker', 'UNKNOWN')}: {seg.get('text', '')}"
				for seg in state["merged_segments"]
			])
			state["preprocessed_transcript"] = transcript_text
		return state
	
	def preprocess_transcript_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 8: Preprocess Transcript for Communication Health Analysis
		
		Algorithm: Text preprocessing and segmentation
		- Input: Merged transcript segments with speaker labels
		- Processing: 
		  * Combine segments into full transcript
		  * Extract speaker-specific contributions
		  * Prepare for parallel analysis
		- Output: Structured transcript data ready for analysis
		
		Rating Principle: N/A (preprocessing only)
		"""
		logger.info("Node 8/13: Preprocessing transcript for communication health analysis")
		state["status"] = "preprocessing_transcript"
		
		# Build full transcript with speaker labels
		if state.get("merged_segments"):
			transcript_text = "\n".join([
				f"{seg.get('speaker', 'UNKNOWN')}: {seg.get('text', '')}"
				for seg in state["merged_segments"]
			])
			state["preprocessed_transcript"] = transcript_text
		
		return state
	
	def analyze_meeting_clarity_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 9: Analyze Meeting Clarity & Conciseness
		
		Algorithm: LLM-based qualitative analysis (DeepSeek v3.1 via NVIDIA API)
		- Model: deepseek-ai/deepseek-v3.1-terminus
		- Input: Full meeting transcript with speaker labels
		- Processing: Zero-shot prompt-based evaluation for spoken communication
		- Output: JSON with clarity_score (0.0-1.0) per speaker + overall, with reasoning
		
		Rating Principle (Meeting Context):
		- Score Range: 0.0 (very unclear) to 1.0 (extremely clear)
		- Factors Evaluated:
		  * Articulation: Clear pronunciation, minimal filler words
		  * Structure: Logical flow of ideas, organized thoughts
		  * Conciseness: Direct communication without unnecessary repetition
		  * Jargon: Technical terms explained appropriately for audience
		- Thresholds:
		  * Excellent (0.8-1.0): Clear, well-structured, concise
		  * Good (0.6-0.8): Mostly clear, minor improvements needed
		  * Fair (0.4-0.6): Some clarity issues, needs improvement
		  * Poor (0.0-0.4): Unclear, confusing, requires significant improvement
		"""
		logger.info("Node 9/13: Analyzing meeting clarity & conciseness")
		
		if "communication_health_scores" not in state:
			state["communication_health_scores"] = {}
		
		transcript = state.get("preprocessed_transcript", "")
		if not transcript:
			state["communication_health_scores"]["clarity"] = []
			return state
		
		prompt = ChatPromptTemplate.from_template(
			"""
			Evaluate the clarity and conciseness of this meeting transcript on a scale of 0.0 to 1.0.
			Consider: articulation quality, logical structure, directness, appropriate use of technical terms.
			
			Meeting Transcript:
			{transcript}
			
			Respond with JSON: {{
				"overall_clarity_score": 0.0-1.0,
				"per_speaker_scores": {{
					"SPK_1": 0.0-1.0,
					"SPK_2": 0.0-1.0
				}},
				"reasoning": "brief explanation"
			}}
			"""
		)
		
		chain = prompt | self.llm | StrOutputParser()
		result = chain.invoke({"transcript": transcript})
		
		try:
			analysis = json.loads(result)
			state["communication_health_scores"]["clarity"] = {
				"overall": float(analysis.get("overall_clarity_score", 0.5)),
				"per_speaker": analysis.get("per_speaker_scores", {}),
				"reasoning": analysis.get("reasoning", "")
			}
		except:
			state["communication_health_scores"]["clarity"] = {
				"overall": 0.5,
				"per_speaker": {},
				"reasoning": "Analysis failed"
			}
		
		return state
	
	def analyze_meeting_completeness_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 10: Analyze Meeting Completeness
		
		Algorithm: LLM-based qualitative analysis (DeepSeek v3.1 via NVIDIA API)
		- Model: deepseek-ai/deepseek-v3.1-terminus
		- Input: Full meeting transcript
		- Processing: Structured prompt evaluating information sufficiency
		- Output: JSON with completeness_score (0.0-1.0) and reasoning
		
		Rating Principle (Meeting Context):
		- Score Range: 0.0 (very incomplete) to 1.0 (completely comprehensive)
		- Factors Evaluated:
		  * Topic Coverage: All agenda items addressed
		  * Information Sufficiency: Adequate detail for decisions
		  * Action Items: Clear next steps identified
		  * Question Resolution: Questions raised are answered
		- Thresholds:
		  * Excellent (0.8-1.0): All topics covered, clear actions
		  * Good (0.6-0.8): Most topics covered, minor gaps
		  * Fair (0.4-0.6): Missing some important information
		  * Poor (0.0-0.4): Critical information missing
		"""
		logger.info("Node 10/13: Analyzing meeting completeness")
		
		if "communication_health_scores" not in state:
			state["communication_health_scores"] = {}
		
		transcript = state.get("preprocessed_transcript", "")
		if not transcript:
			state["communication_health_scores"]["completeness"] = {}
			return state
		
		prompt = ChatPromptTemplate.from_template(
			"""
			Evaluate the completeness of this meeting on a scale of 0.0 to 1.0.
			Consider: all topics addressed, sufficient information for decisions, clear action items, questions answered.
			
			Meeting Transcript:
			{transcript}
			
			Respond with JSON: {{"completeness_score": 0.0-1.0, "reasoning": "brief explanation"}}
			"""
		)
		
		chain = prompt | self.llm | StrOutputParser()
		result = chain.invoke({"transcript": transcript})
		
		try:
			analysis = json.loads(result)
			state["communication_health_scores"]["completeness"] = {
				"overall": float(analysis.get("completeness_score", 0.5)),
				"reasoning": analysis.get("reasoning", "")
			}
		except:
			state["communication_health_scores"]["completeness"] = {
				"overall": 0.5,
				"reasoning": "Analysis failed"
			}
		
		return state
	
	def analyze_meeting_correctness_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 11: Analyze Meeting Correctness & Coherence
		
		Algorithm: LLM-based qualitative analysis (DeepSeek v3.1 via NVIDIA API)
		- Model: deepseek-ai/deepseek-v3.1-terminus
		- Input: Full meeting transcript
		- Processing: Factual accuracy and logical coherence evaluation
		- Output: JSON with correctness_score (0.0-1.0) and reasoning
		
		Rating Principle (Meeting Context):
		- Score Range: 0.0 (many errors) to 1.0 (perfectly correct)
		- Factors Evaluated:
		  * Factual Accuracy: Information shared is correct
		  * Logical Coherence: Ideas connect logically
		  * Consistency: No contradictions between speakers or statements
		  * Grammar/Clarity: Proper use of language (for spoken context)
		- Thresholds:
		  * Excellent (0.8-1.0): Highly accurate, coherent
		  * Good (0.6-0.8): Mostly accurate, minor issues
		  * Fair (0.4-0.6): Some errors or coherence issues
		  * Poor (0.0-0.4): Multiple errors, confusing
		"""
		logger.info("Node 11/13: Analyzing meeting correctness & coherence")
		
		if "communication_health_scores" not in state:
			state["communication_health_scores"] = {}
		
		transcript = state.get("preprocessed_transcript", "")
		if not transcript:
			state["communication_health_scores"]["correctness"] = {}
			return state
		
		prompt = ChatPromptTemplate.from_template(
			"""
			Evaluate the correctness and coherence of this meeting on a scale of 0.0 to 1.0.
			Consider: factual accuracy, logical flow, consistency, proper language use.
			
			Meeting Transcript:
			{transcript}
			
			Respond with JSON: {{"correctness_score": 0.0-1.0, "reasoning": "brief explanation"}}
			"""
		)
		
		chain = prompt | self.llm | StrOutputParser()
		result = chain.invoke({"transcript": transcript})
		
		try:
			analysis = json.loads(result)
			state["communication_health_scores"]["correctness"] = {
				"overall": float(analysis.get("correctness_score", 0.5)),
				"reasoning": analysis.get("reasoning", "")
			}
		except:
			state["communication_health_scores"]["correctness"] = {
				"overall": 0.5,
				"reasoning": "Analysis failed"
			}
		
		return state
	
	def analyze_meeting_courtesy_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 12: Analyze Meeting Courtesy & Tone
		
		Algorithm: LLM-based qualitative analysis (DeepSeek v3.1 via NVIDIA API)
		- Model: deepseek-ai/deepseek-v3.1-terminus
		- Input: Full meeting transcript
		- Processing: Interpersonal communication evaluation
		- Output: JSON with courtesy_score (0.0-1.0) per speaker + overall, with reasoning
		
		Rating Principle (Meeting Context):
		- Score Range: 0.0 (very discourteous) to 1.0 (extremely courteous)
		- Factors Evaluated:
		  * Respect: Respectful treatment of all participants
		  * Professionalism: Appropriate business tone
		  * Empathy: Acknowledgment of others' perspectives
		  * Turn-taking: Balanced participation, no interruptions
		- Thresholds:
		  * Excellent (0.8-1.0): Highly respectful, professional
		  * Good (0.6-0.8): Polite and professional
		  * Fair (0.4-0.6): Adequate but could improve
		  * Poor (0.0-0.4): Discourteous, unprofessional
		"""
		logger.info("Node 12/13: Analyzing meeting courtesy & tone")
		
		if "communication_health_scores" not in state:
			state["communication_health_scores"] = {}
		
		transcript = state.get("preprocessed_transcript", "")
		if not transcript:
			state["communication_health_scores"]["courtesy"] = {}
			return state
		
		prompt = ChatPromptTemplate.from_template(
			"""
			Evaluate the courtesy and tone of this meeting on a scale of 0.0 to 1.0.
			Consider: respect for participants, professionalism, empathy, balanced participation.
			
			Meeting Transcript:
			{transcript}
			
			Respond with JSON: {{
				"overall_courtesy_score": 0.0-1.0,
				"per_speaker_scores": {{
					"SPK_1": 0.0-1.0,
					"SPK_2": 0.0-1.0
				}},
				"reasoning": "brief explanation"
			}}
			"""
		)
		
		chain = prompt | self.llm | StrOutputParser()
		result = chain.invoke({"transcript": transcript})
		
		try:
			analysis = json.loads(result)
			state["communication_health_scores"]["courtesy"] = {
				"overall": float(analysis.get("overall_courtesy_score", 0.5)),
				"per_speaker": analysis.get("per_speaker_scores", {}),
				"reasoning": analysis.get("reasoning", "")
			}
		except:
			state["communication_health_scores"]["courtesy"] = {
				"overall": 0.5,
				"per_speaker": {},
				"reasoning": "Analysis failed"
			}
		
		return state
	
	def analyze_meeting_audience_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 13: Analyze Meeting Audience-Centricity
		
		Algorithm: LLM-based qualitative analysis (DeepSeek v3.1 via NVIDIA API)
		- Model: deepseek-ai/deepseek-v3.1-terminus
		- Input: Full meeting transcript with speaker roles
		- Processing: Participant engagement and relevance evaluation
		- Output: JSON with audience_score (0.0-1.0) and reasoning
		
		Rating Principle (Meeting Context):
		- Score Range: 0.0 (not audience-focused) to 1.0 (perfectly audience-focused)
		- Factors Evaluated:
		  * Engagement: All participants actively engaged
		  * Relevance: Content relevant to all participants' roles
		  * Participation Balance: Equal opportunity to contribute
		  * Context Awareness: Speakers acknowledge others' perspectives
		- Thresholds:
		  * Excellent (0.8-1.0): Highly engaging, balanced participation
		  * Good (0.6-0.8): Good engagement, mostly balanced
		  * Fair (0.4-0.6): Some participants disengaged
		  * Poor (0.0-0.4): Poor engagement, unbalanced participation
		"""
		logger.info("Node 13/13: Analyzing meeting audience-centricity")
		
		if "communication_health_scores" not in state:
			state["communication_health_scores"] = {}
		
		transcript = state.get("preprocessed_transcript", "")
		if not transcript:
			state["communication_health_scores"]["audience"] = {}
			return state
		
		prompt = ChatPromptTemplate.from_template(
			"""
			Evaluate how well this meeting engaged all participants on a scale of 0.0 to 1.0.
			Consider: all participants engaged, content relevant to everyone, balanced participation, acknowledgment of perspectives.
			
			Meeting Transcript:
			{transcript}
			
			Respond with JSON: {{"audience_score": 0.0-1.0, "reasoning": "brief explanation"}}
			"""
		)
		
		chain = prompt | self.llm | StrOutputParser()
		result = chain.invoke({"transcript": transcript})
		
		try:
			analysis = json.loads(result)
			state["communication_health_scores"]["audience"] = {
				"overall": float(analysis.get("audience_score", 0.5)),
				"reasoning": analysis.get("reasoning", "")
			}
		except:
			state["communication_health_scores"]["audience"] = {
				"overall": 0.5,
				"reasoning": "Analysis failed"
			}
		
		return state
	
	def analyze_meeting_timeliness_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 14: Analyze Meeting Timeliness & Efficiency
		
		Algorithm: LLM-based qualitative analysis + Heuristic timing analysis
		- Model: deepseek-ai/deepseek-v3.1-terminus (for content evaluation)
		- Input: Full meeting transcript + meeting metadata
		- Processing: 
		  * LLM evaluates pacing and efficiency
		  * Heuristic analysis of meeting duration appropriateness
		  * Time management evaluation
		- Output: JSON with timeliness_score (0.0-1.0) and reasoning
		
		Rating Principle (Meeting Context):
		- Score Range: 0.0 (very inefficient) to 1.0 (perfectly efficient)
		- Factors Evaluated:
		  * Pacing: Appropriate pace, not rushed or dragging
		  * Time Management: Stays on schedule, respects time limits
		  * Efficiency: No unnecessary digressions, focused discussion
		  * Follow-up Timing: Appropriate time allocated for action items
		- Thresholds:
		  * Excellent (0.8-1.0): Perfect pacing, efficient use of time
		  * Good (0.6-0.8): Generally efficient, minor pacing issues
		  * Fair (0.4-0.6): Some inefficiency or pacing problems
		  * Poor (0.0-0.4): Inefficient, poor time management
		"""
		logger.info("Node 14/13: Analyzing meeting timeliness & efficiency")
		
		if "communication_health_scores" not in state:
			state["communication_health_scores"] = {}
		
		transcript = state.get("preprocessed_transcript", "")
		if not transcript:
			state["communication_health_scores"]["timeliness"] = {}
			return state
		
		prompt = ChatPromptTemplate.from_template(
			"""
			Evaluate the timeliness and efficiency of this meeting on a scale of 0.0 to 1.0.
			Consider: appropriate pacing, time management, efficiency, focus on agenda.
			
			Meeting Transcript:
			{transcript}
			
			Respond with JSON: {{"timeliness_score": 0.0-1.0, "reasoning": "brief explanation"}}
			"""
		)
		
		chain = prompt | self.llm | StrOutputParser()
		result = chain.invoke({"transcript": transcript})
		
		try:
			analysis = json.loads(result)
			state["communication_health_scores"]["timeliness"] = {
				"overall": float(analysis.get("timeliness_score", 0.5)),
				"reasoning": analysis.get("reasoning", "")
			}
		except:
			state["communication_health_scores"]["timeliness"] = {
				"overall": 0.5,
				"reasoning": "Analysis failed"
			}
		
		return state
	
	def aggregate_meeting_health_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 15: Aggregate Meeting Communication Health Scores
		
		Algorithm: Weighted Average Aggregation
		- Input: Individual scores from 6 analysis dimensions
		- Processing:
		  * Overall aggregation: Simple average of all 6 dimension scores
		  * Per-speaker aggregation: Average scores where available
		  * Cross-dimension analysis: Identify strengths and weaknesses
		- Output: Structured JSON with overall and per-speaker health scores
		
		Rating Principle:
		- Overall Health Score: Unweighted mean of 6 dimensions
		  * Formula: (clarity + completeness + correctness + courtesy + audience + timeliness) / 6
		- Per-Speaker Health: Average of speaker-specific scores (clarity, courtesy)
		- Health Classification:
		  * Excellent (0.8-1.0): High scores across all dimensions
		  * Good (0.6-0.8): Solid performance, minor improvements possible
		  * Fair (0.4-0.6): Mixed performance, several areas need improvement
		  * Poor (0.0-0.4): Low scores, significant improvements needed
		"""
		# Check if already aggregated (idempotent check)
		if "aggregated_health" in state and state.get("aggregated_health"):
			existing = state["aggregated_health"]
			health_scores = state.get("communication_health_scores", {})
			expected_dims = {'clarity', 'completeness', 'correctness', 'courtesy', 'audience', 'timeliness'}
			available_dims = set(health_scores.keys())
			if expected_dims.issubset(available_dims) and existing.get('overall'):
				# Already complete, return early
				return state
		
		logger.info("Node 15/16: Aggregating meeting communication health scores")
		
		health_scores = state.get("communication_health_scores", {})
		
		# Wait for all 6 dimensions to be available
		expected_dims = {'clarity', 'completeness', 'correctness', 'courtesy', 'audience', 'timeliness'}
		available_dims = set(health_scores.keys())
		
		if not expected_dims.issubset(available_dims):
			# Not all dimensions analyzed yet, return state as-is (will be called again)
			logger.info(f"Waiting for all dimensions. Available: {available_dims}, Expected: {expected_dims}")
			return state
		
		# Aggregate overall scores
		dimension_scores = {}
		for dim in ['clarity', 'completeness', 'correctness', 'courtesy', 'audience', 'timeliness']:
			dim_data = health_scores.get(dim, {})
			if isinstance(dim_data, dict):
				dimension_scores[dim] = dim_data.get('overall', 0.5)
			else:
				dimension_scores[dim] = 0.5
		
		overall_health = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0.5
		
		# Aggregate per-speaker scores
		per_speaker_scores = {}
		speakers = state.get("speaker_labels", [])
		
		for speaker in speakers:
			speaker_scores = []
			# Clarity and courtesy have per-speaker scores
			if 'clarity' in health_scores and 'per_speaker' in health_scores['clarity']:
				clarity_score = health_scores['clarity']['per_speaker'].get(speaker, 0.5)
				speaker_scores.append(clarity_score)
			if 'courtesy' in health_scores and 'per_speaker' in health_scores['courtesy']:
				courtesy_score = health_scores['courtesy']['per_speaker'].get(speaker, 0.5)
				speaker_scores.append(courtesy_score)
			
			if speaker_scores:
				per_speaker_scores[speaker] = sum(speaker_scores) / len(speaker_scores)
		
		state["aggregated_health"] = {
			"overall": overall_health,
			"dimensions": dimension_scores,
			"per_speaker": per_speaker_scores,
			"total_speakers": len(speakers)
		}
		
		return state
	
	def explain_meeting_health_node(self, state: ASRMeetingState) -> ASRMeetingState:
		"""
		Node 16: Explain Meeting Communication Health Results
		
		Algorithm: LLM-based natural language generation
		- Model: deepseek-ai/deepseek-v3.1-terminus
		- Input: Aggregated health scores and dimension reasoning
		- Processing: Synthesize scores into actionable insights
		- Output: Natural language explanation of communication health
		
		Rating Principle: N/A (explanation generation only)
		"""
		logger.info("Node 16/16: Generating meeting communication health explanation")
		
		aggregated = state.get("aggregated_health", {})
		health_scores = state.get("communication_health_scores", {})
		
		prompt = ChatPromptTemplate.from_template(
			"""
			Based on the meeting communication health analysis, provide a concise natural language explanation
			summarizing the main findings and actionable recommendations.
			
			Overall Health Score: {overall_score}
			Dimension Scores: {dimensions}
			
			Key findings:
			- Clarity: {clarity_findings}
			- Completeness: {completeness_findings}
			- Correctness: {correctness_findings}
			- Courtesy: {courtesy_findings}
			- Audience-Centricity: {audience_findings}
			- Timeliness: {timeliness_findings}
			
			Provide a 2-3 paragraph summary explaining:
			1. Overall meeting communication health assessment
			2. Key strengths and weaknesses
			3. Actionable recommendations for improving future meetings
			"""
		)
		
		# Extract reasoning from each dimension
		dimension_findings = {}
		for dim in ['clarity', 'completeness', 'correctness', 'courtesy', 'audience', 'timeliness']:
			dim_data = health_scores.get(dim, {})
			if isinstance(dim_data, dict):
				dimension_findings[dim] = dim_data.get('reasoning', 'No findings')
			else:
				dimension_findings[dim] = 'No data available'
		
		chain = prompt | self.llm | StrOutputParser()
		explanation = chain.invoke({
			"overall_score": aggregated.get('overall', 0.5),
			"dimensions": aggregated.get('dimensions', {}),
			"clarity_findings": dimension_findings.get('clarity', ''),
			"completeness_findings": dimension_findings.get('completeness', ''),
			"correctness_findings": dimension_findings.get('correctness', ''),
			"courtesy_findings": dimension_findings.get('courtesy', ''),
			"audience_findings": dimension_findings.get('audience', ''),
			"timeliness_findings": dimension_findings.get('timeliness', '')
		})
		
		state["health_explanation"] = explanation
		return state


def create_asr_workflow():
	"""
	Creates the ASR meeting processing workflow with communication health analysis.
	
	Workflow Structure:
	1. transcribe_audio -> Ivrit.ai transcription
	2. diarize_pyannote -> PyAnnote validation
	3. merge_diarization -> Merge results
	4. extract_snippets -> Extract speaker snippets
	5. generate_voiceprints -> Voiceprint matching
	6. extract_names -> Hebrew name extraction
	7. summarize -> LLM summarization
	8. preprocess_transcript -> Prepare for communication health analysis
	9-14. Parallel communication health analysis (6 dimensions)
	15. aggregate_meeting_health -> Consolidate scores
	16. explain_meeting_health -> Generate explanation
	"""
	workflow = StateGraph(ASRMeetingState)
	asr = ASRWorkflow()
	
	# Add ASR processing nodes
	workflow.add_node("transcribe_audio", asr.transcribe_audio_node)
	workflow.add_node("diarize_pyannote", asr.diarize_pyannote_node)
	workflow.add_node("merge_diarization", asr.merge_diarization_node)
	workflow.add_node("extract_snippets", asr.extract_snippets_node)
	workflow.add_node("generate_voiceprints", asr.generate_voiceprints_node)
	workflow.add_node("extract_names", asr.extract_names_node)
	workflow.add_node("summarize", asr.summarize_node)
	
	# Add communication health analysis nodes
	workflow.add_node("preprocess_transcript", asr.preprocess_transcript_node)
	workflow.add_node("analyze_meeting_clarity", asr.analyze_meeting_clarity_node)
	workflow.add_node("analyze_meeting_completeness", asr.analyze_meeting_completeness_node)
	workflow.add_node("analyze_meeting_correctness", asr.analyze_meeting_correctness_node)
	workflow.add_node("analyze_meeting_courtesy", asr.analyze_meeting_courtesy_node)
	workflow.add_node("analyze_meeting_audience", asr.analyze_meeting_audience_node)
	workflow.add_node("analyze_meeting_timeliness", asr.analyze_meeting_timeliness_node)
	workflow.add_node("aggregate_meeting_health", asr.aggregate_meeting_health_node)
	workflow.add_node("explain_meeting_health", asr.explain_meeting_health_node)
	
	# Set workflow edges - ASR processing
	workflow.set_entry_point("transcribe_audio")
	workflow.add_edge("transcribe_audio", "diarize_pyannote")
	workflow.add_edge("diarize_pyannote", "merge_diarization")
	workflow.add_edge("merge_diarization", "extract_snippets")
	workflow.add_edge("extract_snippets", "generate_voiceprints")
	workflow.add_edge("generate_voiceprints", "extract_names")
	workflow.add_edge("extract_names", "summarize")
	
	# Communication health analysis branch
	workflow.add_edge("summarize", "preprocess_transcript")
	
	# Preprocessing feeds into all 6 parallel analysis nodes
	workflow.add_edge("preprocess_transcript", "analyze_meeting_clarity")
	workflow.add_edge("preprocess_transcript", "analyze_meeting_completeness")
	workflow.add_edge("preprocess_transcript", "analyze_meeting_correctness")
	workflow.add_edge("preprocess_transcript", "analyze_meeting_courtesy")
	workflow.add_edge("preprocess_transcript", "analyze_meeting_audience")
	workflow.add_edge("preprocess_transcript", "analyze_meeting_timeliness")
	
	# All parallel nodes feed into aggregation
	workflow.add_edge("analyze_meeting_clarity", "aggregate_meeting_health")
	workflow.add_edge("analyze_meeting_completeness", "aggregate_meeting_health")
	workflow.add_edge("analyze_meeting_correctness", "aggregate_meeting_health")
	workflow.add_edge("analyze_meeting_courtesy", "aggregate_meeting_health")
	workflow.add_edge("analyze_meeting_audience", "aggregate_meeting_health")
	workflow.add_edge("analyze_meeting_timeliness", "aggregate_meeting_health")
	
	# Aggregation -> Explanation -> End
	workflow.add_edge("aggregate_meeting_health", "explain_meeting_health")
	workflow.add_edge("explain_meeting_health", END)
	
	return workflow


def get_asr_workflow():
	"""Export ASR workflow for LangGraph Studio."""
	return create_asr_workflow().compile()

