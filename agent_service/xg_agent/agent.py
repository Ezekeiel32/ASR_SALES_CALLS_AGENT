"""LangGraph agent workflows for XGBoost and email analysis."""

from __future__ import annotations

from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import base64
import email
from datetime import datetime, timedelta
import json

from agent_service.xg_agent.data_processing import load_and_preprocess_data
from agent_service.xg_agent.analysis import perform_xgboost_analysis, generate_retail_summary
from agent_service.xg_agent.email_analysis import (
	create_email_database, 
	perform_email_xgboost_analysis, 
	create_email_visualizations, 
	generate_email_summary, 
	save_email_database
)
from agent_service.config import get_settings


class AgentState(TypedDict):
	"""
	Represents the state of our LangGraph agent.
	"""
	data: dict
	analysis_results: dict
	summary: str
	emails: List[dict]
	email_analysis: List[dict]
	drafts: List[dict]
	email_database: dict
	email_analysis_results: dict
	email_visualizations: dict
	email_summary: str
	# Communication health analysis state
	preprocessed_emails: List[dict]
	communication_health_scores: dict  # Individual scores for each dimension
	aggregated_health: dict  # Consolidated results
	health_explanation: str  # Natural language explanation
	# User context for database lookups
	user_id: Optional[str]  # User ID for retrieving Gmail credentials from database


class Agent:
	"""
	The main agent class that orchestrates the data analysis and summarization.
	"""
	def __init__(self):
		settings = get_settings()
		
		# Ensure the NVIDIA_API_KEY is set
		if not settings.nvidia_api_key:
			raise ValueError("NVIDIA_API_KEY is not set. Please check your .env file.")
		
		self.llm = ChatNVIDIA(
			model=settings.nvidia_model,
			api_key=settings.nvidia_api_key,
			base_url=settings.nvidia_api_url,
			temperature=settings.nvidia_temperature,
			top_p=settings.nvidia_top_p,
			max_tokens=settings.nvidia_max_tokens,
			extra_body={"chat_template_kwargs": {"thinking": settings.nvidia_enable_thinking}},
		)
		self.gmail_service = None
		self.settings = settings

	def _calculate_communication_health_features(self, email_data: dict) -> dict:
		"""
		Extract features for communication health analysis.
		Returns features for XGBoost model to predict health scores.
		"""
		body = email_data.get('body', '')
		subject = email_data.get('subject', '')
		text = (subject + ' ' + body).lower()
		
		# Text features for communication health
		word_count = len(body.split())
		sentence_count = body.count('.') + body.count('!') + body.count('?')
		avg_sentence_length = word_count / max(sentence_count, 1)
		
		# Clarity indicators
		has_clear_subject = 1 if subject and len(subject) > 5 else 0
		has_structure = 1 if any(marker in body.lower() for marker in ['bullet', 'list', '1.', '2.', '- ', '* ']) else 0
		
		# Completeness indicators
		has_question_marks = 1 if '?' in text else 0
		has_action_items = 1 if any(word in text for word in ['please', 'action', 'required', 'next steps', 'todo']) else 0
		has_contact_info = 1 if '@' in body or 'phone' in text or 'contact' in text else 0
		
		# Correctness indicators
		has_typos = 1 if any(word in text for word in ['teh', 'adn', 'recieve', 'seperate']) else 0  # Simple heuristic
		has_caps_lock = 1 if sum(1 for c in body if c.isupper()) > len(body) * 0.3 else 0
		
		# Courtesy indicators
		polite_words = sum(1 for word in ['please', 'thank', 'appreciate', 'kindly', 'sorry', 'apologize'] if word in text)
		has_greeting = 1 if any(word in body.lower()[:100] for word in ['hi', 'hello', 'dear', 'good morning', 'good afternoon']) else 0
		has_closing = 1 if any(word in body.lower()[-100:] for word in ['regards', 'sincerely', 'best', 'thanks', 'thank you']) else 0
		
		# Audience-centricity indicators
		has_recipient_name = 1 if email_data.get('to', '') and '@' not in email_data.get('to', '') else 0
		personalization_score = polite_words + has_greeting + has_closing
		
		# Timeliness indicators (would need metadata)
		has_timestamp = 1 if email_data.get('date') else 0
		
		return {
			'word_count': float(word_count),
			'avg_sentence_length': float(avg_sentence_length),
			'has_clear_subject': float(has_clear_subject),
			'has_structure': float(has_structure),
			'has_question_marks': float(has_question_marks),
			'has_action_items': float(has_action_items),
			'has_contact_info': float(has_contact_info),
			'has_typos': float(has_typos),
			'has_caps_lock': float(has_caps_lock),
			'polite_words': float(polite_words),
			'has_greeting': float(has_greeting),
			'has_closing': float(has_closing),
			'personalization_score': float(personalization_score),
			'has_recipient_name': float(has_recipient_name),
			'has_timestamp': float(has_timestamp)
		}

	def get_gmail_service(self, user_id: Optional[str] = None):
		"""
		Authenticate and build the Gmail API service.
		Retrieves credentials from database if user_id is provided, otherwise falls back to file-based auth.
		"""
		SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
		creds = None
		
		# If user_id is provided, retrieve credentials from database
		if user_id:
			from agent_service.database import get_db_session
			from agent_service.database.models import UserGmailCredentials
			import uuid
			
			try:
				user_uuid = uuid.UUID(user_id)
				with get_db_session() as db:
					gmail_creds = db.query(UserGmailCredentials).filter(
						UserGmailCredentials.user_id == user_uuid
					).first()
					
					if gmail_creds:
						# Load credentials from database
						token_data = json.loads(gmail_creds.token_json)
						creds = Credentials.from_authorized_user_info(token_data, SCOPES)
						
						# Refresh token if expired
						if creds.expired and creds.refresh_token:
							creds.refresh(Request())
							# Update stored credentials
							gmail_creds.token_json = creds.to_json()
							db.commit()
					else:
						raise Exception(f"Gmail credentials not found for user {user_id}. Please connect Gmail account first.")
			except ValueError:
				raise Exception(f"Invalid user_id format: {user_id}")
			except Exception as e:
				raise Exception(f"Failed to retrieve Gmail credentials from database: {str(e)}")
		else:
			# Fallback to file-based authentication (for backward compatibility)
			token_file = 'token.json'
			
			if os.path.exists(token_file):
				creds = Credentials.from_authorized_user_file(token_file, SCOPES)
			
			# If there are no (valid) credentials available, raise error
			if not creds or not creds.valid:
				if creds and creds.expired and creds.refresh_token:
					creds.refresh(Request())
				else:
					raise Exception("Gmail credentials not found. Please connect your Gmail account via the OAuth flow.")
		
		return build('gmail', 'v1', credentials=creds)

	def validate_data_node(self, state: AgentState) -> AgentState:
		"""
		Node 1: Validate Data Input
		
		Algorithm: Data validation and quality checks
		- Input: Raw data (dict or file path)
		- Processing:
		  * Check for required columns (Quantity, Price, Year, Month, Day, TotalPrice)
		  * Validate data types
		  * Check for missing values
		  * Basic data quality metrics
		- Output: Validation results and data quality report
		
		Rating Principle:
		- Validation Score: 1.0 if all required columns present and data valid
		- Quality Flags: Missing columns, null values, type mismatches flagged
		- Data Quality Thresholds:
		  * Excellent (0.9-1.0): All columns present, <5% missing values
		  * Good (0.7-0.9): Most columns present, <10% missing values
		  * Fair (0.5-0.7): Some columns missing, <20% missing values
		  * Poor (0.0-0.5): Critical columns missing, >20% missing values
		"""
		print("---VALIDATING DATA---")
		
		data = state.get("data")
		if not data:
			# Try loading default data
			from langgraph_xgboost_agent.data_processing import load_and_preprocess_data
			try:
				df = load_and_preprocess_data()
				state["data"] = df.to_dict()
				data = state["data"]
			except Exception as e:
				state["validation_results"] = {
					"valid": False,
					"error": f"Failed to load data: {str(e)}",
					"quality_score": 0.0
				}
				return state
		
		# Convert to DataFrame for validation
		try:
			df = pd.DataFrame(data)
			
			# Required columns
			required_cols = ['Quantity', 'Price', 'Year', 'Month', 'Day', 'TotalPrice']
			available_cols = list(df.columns)
			
			# Check for column name variations
			col_mapping = {}
			missing_cols = []
			
			for req_col in required_cols:
				if req_col in available_cols:
					col_mapping[req_col] = req_col
				elif req_col == 'Quantity' and 'Qty' in available_cols:
					col_mapping[req_col] = 'Qty'
				elif req_col == 'Price' and 'UnitPrice' in available_cols:
					col_mapping[req_col] = 'UnitPrice'
				else:
					missing_cols.append(req_col)
			
			# Calculate quality metrics
			missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns)) if len(df) > 0 else 0
			quality_score = 1.0 - (len(missing_cols) / len(required_cols)) * 0.5 - min(missing_pct, 0.5)
			quality_score = max(0.0, min(1.0, quality_score))
			
			state["validation_results"] = {
				"valid": len(missing_cols) == 0,
				"quality_score": quality_score,
				"missing_columns": missing_cols,
				"available_columns": available_cols,
				"column_mapping": col_mapping,
				"data_shape": list(df.shape),
				"missing_value_percentage": float(missing_pct),
				"total_records": len(df)
			}
			
		except Exception as e:
			state["validation_results"] = {
				"valid": False,
				"error": f"Validation error: {str(e)}",
				"quality_score": 0.0
			}
		
		return state
	
	def load_data_node(self, state: AgentState) -> AgentState:
		"""
		Node 2: Load and Preprocess Data
		
		Algorithm: Data loading and basic preprocessing
		- Input: Validated data or file path
		- Processing:
		  * Load data from source (file or state)
		  * Apply column name normalization
		  * Basic cleaning (remove duplicates, handle nulls)
		  * Data type conversions
		- Output: Cleaned DataFrame ready for analysis
		
		Rating Principle: N/A (data transformation only)
		"""
		print("---LOADING DATA---")
		
		# Check if data is already in state (from uploaded file)
		if state.get("data") and isinstance(state["data"], dict) and len(state["data"]) > 0:
			print("Using data from state (uploaded file)")
			df = pd.DataFrame(state["data"])
		else:
			# Load from default file if no data in state
			from langgraph_xgboost_agent.data_processing import load_and_preprocess_data
			df = load_and_preprocess_data()
		
		# Apply column mapping if validation provided it
		validation = state.get("validation_results", {})
		col_mapping = validation.get("column_mapping", {})
		if col_mapping:
			df = df.rename(columns={v: k for k, v in col_mapping.items()})
		
		# Basic cleaning
		df = df.dropna(subset=['Quantity', 'Price', 'TotalPrice'])  # Remove rows with missing critical data
		df = df.drop_duplicates()
		
		# Ensure numeric types
		for col in ['Quantity', 'Price', 'TotalPrice', 'Year', 'Month', 'Day']:
			if col in df.columns:
				df[col] = pd.to_numeric(df[col], errors='coerce')
		
		state["data"] = df.to_dict()
		state["data_shape"] = list(df.shape)
		return state
	
	def explore_data_node(self, state: AgentState) -> AgentState:
		"""
		Node 3: Explore Data and Generate Statistics
		
		Algorithm: Descriptive statistics and data profiling
		- Input: Cleaned DataFrame
		- Processing:
		  * Calculate descriptive statistics (mean, median, std, min, max)
		  * Generate correlation matrix
		  * Identify outliers (IQR method)
		  * Distribution analysis
		- Output: Comprehensive data statistics and insights
		
		Rating Principle:
		- Completeness: Percentage of statistics successfully calculated
		- Data Quality Indicators:
		  * Outlier Percentage: <5% (excellent), 5-10% (good), 10-20% (fair), >20% (poor)
		  * Correlation Strength: Strong correlations (>0.7) indicate good feature relationships
		"""
		print("---EXPLORING DATA---")
		
		df = pd.DataFrame(state["data"])
		
		# Descriptive statistics
		numeric_cols = ['Quantity', 'Price', 'TotalPrice', 'Year', 'Month', 'Day']
		available_numeric = [col for col in numeric_cols if col in df.columns]
		
		descriptive_stats = df[available_numeric].describe().to_dict() if available_numeric else {}
		
		# Correlation analysis
		correlation_matrix = df[available_numeric].corr().to_dict() if len(available_numeric) > 1 else {}
		
		# Outlier detection (IQR method)
		outlier_counts = {}
		for col in available_numeric:
			if col in ['Quantity', 'Price', 'TotalPrice']:
				Q1 = df[col].quantile(0.25)
				Q3 = df[col].quantile(0.75)
				IQR = Q3 - Q1
				lower_bound = Q1 - 1.5 * IQR
				upper_bound = Q3 + 1.5 * IQR
				outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
				outlier_counts[col] = {
					"count": len(outliers),
					"percentage": float(len(outliers) / len(df) * 100) if len(df) > 0 else 0
				}
		
		# Distribution summaries
		distributions = {}
		for col in available_numeric:
			distributions[col] = {
				"mean": float(df[col].mean()),
				"median": float(df[col].median()),
				"std": float(df[col].std()),
				"skewness": float(df[col].skew()),
				"kurtosis": float(df[col].kurtosis())
			}
		
		state["data_exploration"] = {
			"descriptive_stats": {k: {k2: float(v2) for k2, v2 in v.items()} for k, v in descriptive_stats.items()},
			"correlation_matrix": {k: {k2: float(v2) for k2, v2 in v.items()} for k, v in correlation_matrix.items()},
			"outlier_analysis": outlier_counts,
			"distributions": distributions,
			"total_records": len(df),
			"numeric_features": available_numeric
		}
		
		return state
	
	def engineer_features_node(self, state: AgentState) -> AgentState:
		"""
		Node 4: Feature Engineering
		
		Algorithm: Derived feature creation and transformation
		- Input: Cleaned DataFrame
		- Processing:
		  * Create temporal features (day_of_week, quarter, season)
		  * Price per unit calculations
		  * Revenue segments (if applicable)
		  * Normalization/scaling if needed
		- Output: Enhanced DataFrame with derived features
		
		Rating Principle:
		- Feature Richness: Number of meaningful derived features created
		- Feature Quality: Correlation with target variable
		- Enhancement Score: 1.0 if all meaningful features created successfully
		"""
		print("---ENGINEERING FEATURES---")
		
		df = pd.DataFrame(state["data"])
		
		# Create derived features
		# Day of week (if date components available)
		if all(col in df.columns for col in ['Year', 'Month', 'Day']):
			try:
				df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day']])
				df['DayOfWeek'] = df['Date'].dt.dayofweek
				df['Quarter'] = df['Date'].dt.quarter
				df['IsWeekend'] = (df['DayOfWeek'] >= 5).astype(int)
			except:
				pass
		
		# Price per unit
		if 'Price' in df.columns and 'Quantity' in df.columns:
			df['PricePerUnit'] = df['Price'] / df['Quantity'].replace(0, 1)  # Avoid division by zero
		
		# Revenue segments (if TotalPrice available)
		if 'TotalPrice' in df.columns:
			df['RevenueCategory'] = pd.cut(
				df['TotalPrice'],
				bins=[0, df['TotalPrice'].quantile(0.33), df['TotalPrice'].quantile(0.67), float('inf')],
				labels=['Low', 'Medium', 'High']
			)
		
		# Log transformations for skewed features
		if 'TotalPrice' in df.columns and df['TotalPrice'].min() > 0:
			df['LogTotalPrice'] = np.log1p(df['TotalPrice'])
		
		# Store enhanced data
		state["data"] = df.to_dict()
		state["engineered_features"] = {
			"new_features": [col for col in df.columns if col not in pd.DataFrame(state.get("data", {})).columns],
			"total_features": len(df.columns)
		}
		
		return state

	def analyze_data_node(self, state: AgentState) -> AgentState:
		"""
		Node 5: XGBoost Analysis
		
		Algorithm: XGBoost Gradient Boosting Regression
		- Model: XGBRegressor (eXtreme Gradient Boosting)
		- Input: Enhanced DataFrame with features
		- Processing:
		  * Train/test split (80/20)
		  * XGBoost model training with hyperparameters
		  * Prediction and evaluation
		  * Feature importance extraction
		- Output: Model performance metrics, feature importances, predictions
		
		Rating Principle:
		- Model Performance Metrics:
		  * R² Score: >0.9 (excellent), 0.7-0.9 (good), 0.5-0.7 (fair), <0.5 (poor)
		  * RMSE: Lower is better (relative to target variable scale)
		  * MAE: Lower is better (absolute error)
		- Feature Importance: Features ranked by gain (importance to prediction)
		- Model Quality Score: Weighted combination of R², RMSE, and MAE
		"""
		print("---ANALYZING DATA WITH XGBOOST---")
		
		# Check if data exists and is valid
		if not state.get("data") or len(state["data"]) == 0:
			raise ValueError("No data available for analysis. Please upload a file first.")
		
		try:
			df = pd.DataFrame(state["data"])
			if df.empty:
				raise ValueError("Data frame is empty. Please upload a valid file.")
			
			# Use settings for XGBoost parameters
			results = perform_xgboost_analysis(
				df,
				n_estimators=self.settings.xgboost_n_estimators,
				learning_rate=self.settings.xgboost_learning_rate,
				max_depth=self.settings.xgboost_max_depth,
				random_state=self.settings.xgboost_random_state
			)
			state["analysis_results"] = results
			
			# Calculate model quality score
			r2 = results.get("model_performance", {}).get("r2_score", 0.0)
			rmse = results.get("model_performance", {}).get("rmse", float('inf'))
			mae = results.get("model_performance", {}).get("mae", float('inf'))
			
			# Normalize RMSE and MAE (assuming max target value for scaling)
			target_values = df.get('TotalPrice', pd.Series([1]))
			max_target = target_values.max() if hasattr(target_values, 'max') else 1.0
			normalized_rmse = 1.0 - min(rmse / max_target, 1.0) if max_target > 0 else 0.0
			normalized_mae = 1.0 - min(mae / max_target, 1.0) if max_target > 0 else 0.0
			
			# Weighted quality score
			quality_score = (r2 * 0.5) + (normalized_rmse * 0.3) + (normalized_mae * 0.2)
			state["analysis_results"]["model_quality_score"] = float(quality_score)
			
		except Exception as e:
			raise Exception(f"Error during data analysis: {str(e)}")
		
		return state
	
	def generate_visualizations_node(self, state: AgentState) -> AgentState:
		"""
		Node 6: Generate Visualizations
		
		Algorithm: Plotly-based data visualization
		- Input: Analysis results and data
		- Processing:
		  * Actual vs Predicted scatter plots
		  * Feature importance bar charts
		  * Residual plots
		  * Distribution histograms
		  * Correlation heatmaps
		- Output: Visualization data (JSON-serializable format)
		
		Rating Principle:
		- Visualization Completeness: All expected visualizations generated
		- Data Quality: Visualizations accurately represent underlying data
		- Completeness Score: 1.0 if all visualizations successfully created
		"""
		print("---GENERATING VISUALIZATIONS---")
		
		analysis_results = state.get("analysis_results", {})
		df = pd.DataFrame(state["data"])
		
		# Visualizations are already included in analysis_results from perform_xgboost_analysis
		# But we can enhance them here
		if "visualizations" not in analysis_results:
			from langgraph_xgboost_agent.analysis import create_retail_visualizations
			
			# Re-extract visualization data if needed
			features = analysis_results.get("data_statistics", {}).get("features_used", [])
			target = analysis_results.get("data_statistics", {}).get("target_variable", "TotalPrice")
			feature_importances = analysis_results.get("feature_importances", {})
			
			# This would require predictions, so we'll use the existing visualizations
			state["visualizations"] = analysis_results.get("visualizations", {})
		else:
			state["visualizations"] = analysis_results["visualizations"]
		
		state["visualization_status"] = {
			"generated": len(state.get("visualizations", {})) > 0,
			"count": len(state.get("visualizations", {}))
		}
		
		return state

	def summarize_results_node(self, state: AgentState) -> AgentState:
		"""
		Node 7: Generate Comprehensive Summary
		
		Algorithm: LLM-based natural language generation
		- Model: DeepSeek v3.1 via NVIDIA API
		- Input: Analysis results, data exploration, visualizations
		- Processing: Synthesize all insights into actionable business recommendations
		- Output: Natural language summary with key insights and recommendations
		
		Rating Principle: N/A (summary generation only)
		"""
		print("---GENERATING COMPREHENSIVE SUMMARY---")
		
		analysis_results = state.get("analysis_results", {})
		data_exploration = state.get("data_exploration", {})
		validation_results = state.get("validation_results", {})
		
		prompt = ChatPromptTemplate.from_template(
			"""
			You are an expert data analyst and business revenue consultant. Based on the following comprehensive retail data analysis,
			provide a detailed summary with actionable insights for revenue generation and optimization.
			
			Data Validation:
			{validation_results}
			
			Data Exploration:
			{data_exploration}
			
			XGBoost Analysis Results:
			{analysis_results}
			
			Provide a comprehensive summary that includes:
			1. **Executive Summary**: Overall assessment of data quality and model performance
			2. **Key Insights**: What the feature importances reveal about revenue drivers
			3. **Business Recommendations**: Specific actions to optimize revenue based on the analysis
			4. **Risk Factors**: Potential issues or limitations identified
			5. **Next Steps**: Suggested follow-up analyses or data collection
			
			Format the response clearly with sections and bullet points where appropriate.
			"""
		)
		
		chain = prompt | self.llm | StrOutputParser()
		summary = chain.invoke({
			"analysis_results": str(analysis_results),
			"data_exploration": str(data_exploration),
			"validation_results": str(validation_results)
		})
		state["summary"] = summary
		return state

	def fetch_emails_node(self, state: AgentState) -> AgentState:
		"""
		Fetches emails from Gmail API. Requires proper Gmail authentication.
		"""
		print("---FETCHING EMAILS---")
		
		# Initialize email lists
		state["emails"] = []
		state["email_analysis"] = []
		state["drafts"] = []
		
		# Get Gmail service - this will raise an exception if authentication fails
		if not self.gmail_service:
			user_id = state.get("user_id")
			self.gmail_service = self.get_gmail_service(user_id=user_id)
		
		if not self.gmail_service:
			raise Exception("Gmail authentication failed. Please ensure credentials.json is properly configured.")
		
		# Fetch real emails from Gmail API
		try:
			results = self.gmail_service.users().messages().list(userId='me', maxResults=50).execute()
			messages = results.get('messages', [])
			
			for message in messages:
				msg = self.gmail_service.users().messages().get(userId='me', id=message['id']).execute()
				email_data = self._parse_email_message(msg)
				state["emails"].append(email_data)
		except Exception as e:
			raise Exception(f"Error fetching emails from Gmail API: {e}")
		
		return state

	def preprocess_emails_node(self, state: AgentState) -> AgentState:
		"""
		Preprocessing node: Clean and extract metadata from emails.
		"""
		print("---PREPROCESSING EMAILS---")
		
		preprocessed = []
		for email_data in state["emails"]:
			# Clean and extract metadata
			cleaned = {
				'id': email_data.get('id'),
				'subject': email_data.get('subject', '').strip(),
				'body': email_data.get('body', '').strip(),
				'from': email_data.get('from', ''),
				'date': email_data.get('date', ''),
				'to': email_data.get('to', ''),
				'body_length': len(email_data.get('body', '')),
				'word_count': len(email_data.get('body', '').split()),
			}
			preprocessed.append(cleaned)
		
		state["preprocessed_emails"] = preprocessed
		return state
	
	def analyze_clarity_node(self, state: AgentState) -> AgentState:
		"""
		Analyzes clarity and conciseness of emails.
		
		Algorithm: LLM-based qualitative analysis (DeepSeek v3.1 via NVIDIA API)
		- Model: deepseek-ai/deepseek-v3.1-terminus
		- Input: Email subject + body text
		- Processing: Zero-shot prompt-based evaluation
		- Output: JSON with clarity_score (0.0-1.0) and reasoning
		
		Rating Principle:
		- Score Range: 0.0 (very unclear) to 1.0 (extremely clear)
		- Factors Evaluated:
		  * Readability: Sentence structure, vocabulary complexity
		  * Directness: Absence of unnecessary words, direct communication
		  * Jargon: Technical terms explained or avoided appropriately
		  * Brevity: Concise without losing essential information
		- Thresholds:
		  * Excellent (0.8-1.0): Clear, direct, no jargon issues
		  * Good (0.6-0.8): Mostly clear, minor improvements needed
		  * Fair (0.4-0.6): Some clarity issues, needs revision
		  * Poor (0.0-0.4): Unclear, confusing, requires significant revision
		"""
		print("---ANALYZING CLARITY & CONCISENESS---")
		
		if "communication_health_scores" not in state:
			state["communication_health_scores"] = {}
		
		scores = []
		for email in state["preprocessed_emails"]:
			prompt = ChatPromptTemplate.from_template(
				"""
				Evaluate the clarity and conciseness of this email on a scale of 0.0 to 1.0.
				Consider: readability, directness, absence of jargon, brevity.
				
				Subject: {subject}
				Body: {body}
				
				Respond with JSON: {{"clarity_score": 0.0-1.0, "reasoning": "brief explanation"}}
				"""
			)
			
			chain = prompt | self.llm | StrOutputParser()
			result = chain.invoke({
				"subject": email.get('subject', ''),
				"body": email.get('body', '')
			})
			
			try:
				analysis = json.loads(result)
				scores.append({
					'email_id': email.get('id'),
					'clarity_score': float(analysis.get('clarity_score', 0.5)),
					'reasoning': analysis.get('reasoning', '')
				})
			except:
				scores.append({
					'email_id': email.get('id'),
					'clarity_score': 0.5,
					'reasoning': 'Analysis failed'
				})
		
		state["communication_health_scores"]["clarity"] = scores
		return state
	
	def analyze_completeness_node(self, state: AgentState) -> AgentState:
		"""
		Analyzes completeness of emails.
		
		Algorithm: LLM-based qualitative analysis (DeepSeek v3.1 via NVIDIA API)
		- Model: deepseek-ai/deepseek-v3.1-terminus
		- Input: Email subject + body text
		- Processing: Structured prompt evaluating information sufficiency
		- Output: JSON with completeness_score (0.0-1.0) and reasoning
		
		Rating Principle:
		- Score Range: 0.0 (very incomplete) to 1.0 (completely comprehensive)
		- Factors Evaluated:
		  * Sufficient Information: All necessary details present
		  * Actionable Details: Clear instructions or requests
		  * Next Steps: Explicit call-to-action or follow-up instructions
		  * Question Prevention: Answers likely questions without requiring follow-up
		- Thresholds:
		  * Excellent (0.8-1.0): All information present, no follow-up needed
		  * Good (0.6-0.8): Most information present, minor gaps
		  * Fair (0.4-0.6): Missing some important information
		  * Poor (0.0-0.4): Critical information missing, requires follow-up
		"""
		print("---ANALYZING COMPLETENESS---")
		
		if "communication_health_scores" not in state:
			state["communication_health_scores"] = {}
		
		scores = []
		for email in state["preprocessed_emails"]:
			prompt = ChatPromptTemplate.from_template(
				"""
				Evaluate the completeness of this email on a scale of 0.0 to 1.0.
				Consider: sufficient information, actionable details, clear next steps, answers potential questions.
				
				Subject: {subject}
				Body: {body}
				
				Respond with JSON: {{"completeness_score": 0.0-1.0, "reasoning": "brief explanation"}}
				"""
			)
			
			chain = prompt | self.llm | StrOutputParser()
			result = chain.invoke({
				"subject": email.get('subject', ''),
				"body": email.get('body', '')
			})
			
			try:
				analysis = json.loads(result)
				scores.append({
					'email_id': email.get('id'),
					'completeness_score': float(analysis.get('completeness_score', 0.5)),
					'reasoning': analysis.get('reasoning', '')
				})
			except:
				scores.append({
					'email_id': email.get('id'),
					'completeness_score': 0.5,
					'reasoning': 'Analysis failed'
				})
		
		state["communication_health_scores"]["completeness"] = scores
		return state
	
	def analyze_correctness_node(self, state: AgentState) -> AgentState:
		"""
		Analyzes correctness and coherence of emails.
		
		Algorithm: LLM-based qualitative analysis (DeepSeek v3.1 via NVIDIA API)
		- Model: deepseek-ai/deepseek-v3.1-terminus
		- Input: Email subject + body text
		- Processing: Factual accuracy and linguistic correctness evaluation
		- Output: JSON with correctness_score (0.0-1.0) and reasoning
		
		Rating Principle:
		- Score Range: 0.0 (many errors) to 1.0 (perfectly correct)
		- Factors Evaluated:
		  * Factual Accuracy: Information is correct and verifiable
		  * Grammar/Spelling: No grammatical or spelling errors
		  * Logical Flow: Ideas connect coherently, no contradictions
		  * Consistent Tone: Tone remains consistent throughout
		- Thresholds:
		  * Excellent (0.8-1.0): No errors, perfect coherence
		  * Good (0.6-0.8): Minor errors, mostly coherent
		  * Fair (0.4-0.6): Some errors or coherence issues
		  * Poor (0.0-0.4): Multiple errors, confusing flow
		"""
		print("---ANALYZING CORRECTNESS & COHERENCE---")
		
		if "communication_health_scores" not in state:
			state["communication_health_scores"] = {}
		
		scores = []
		for email in state["preprocessed_emails"]:
			prompt = ChatPromptTemplate.from_template(
				"""
				Evaluate the correctness and coherence of this email on a scale of 0.0 to 1.0.
				Consider: factual accuracy, grammar/spelling, logical flow, consistent tone.
				
				Subject: {subject}
				Body: {body}
				
				Respond with JSON: {{"correctness_score": 0.0-1.0, "reasoning": "brief explanation"}}
				"""
			)
			
			chain = prompt | self.llm | StrOutputParser()
			result = chain.invoke({
				"subject": email.get('subject', ''),
				"body": email.get('body', '')
			})
			
			try:
				analysis = json.loads(result)
				scores.append({
					'email_id': email.get('id'),
					'correctness_score': float(analysis.get('correctness_score', 0.5)),
					'reasoning': analysis.get('reasoning', '')
				})
			except:
				scores.append({
					'email_id': email.get('id'),
					'correctness_score': 0.5,
					'reasoning': 'Analysis failed'
				})
		
		state["communication_health_scores"]["correctness"] = scores
		return state
	
	def analyze_courtesy_node(self, state: AgentState) -> AgentState:
		"""
		Analyzes courtesy and tone of emails.
		
		Algorithm: LLM-based qualitative analysis (DeepSeek v3.1 via NVIDIA API)
		- Model: deepseek-ai/deepseek-v3.1-terminus
		- Input: Email subject + body text
		- Processing: Sentiment and politeness evaluation
		- Output: JSON with courtesy_score (0.0-1.0) and reasoning
		
		Rating Principle:
		- Score Range: 0.0 (very discourteous) to 1.0 (extremely courteous)
		- Factors Evaluated:
		  * Politeness: Use of polite language (please, thank you, etc.)
		  * Respect: Respectful tone, no condescension
		  * Empathy: Acknowledgment of recipient's perspective
		  * Professionalism: Appropriate for business context
		- Thresholds:
		  * Excellent (0.8-1.0): Highly courteous, professional, empathetic
		  * Good (0.6-0.8): Polite and professional
		  * Fair (0.4-0.6): Adequate but could be more courteous
		  * Poor (0.0-0.4): Discourteous, unprofessional, or lacking empathy
		"""
		print("---ANALYZING COURTESY & TONE---")
		
		if "communication_health_scores" not in state:
			state["communication_health_scores"] = {}
		
		scores = []
		for email in state["preprocessed_emails"]:
			prompt = ChatPromptTemplate.from_template(
				"""
				Evaluate the courtesy and tone of this email on a scale of 0.0 to 1.0.
				Consider: politeness, respect, empathy, professionalism.
				
				Subject: {subject}
				Body: {body}
				
				Respond with JSON: {{"courtesy_score": 0.0-1.0, "reasoning": "brief explanation"}}
				"""
			)
			
			chain = prompt | self.llm | StrOutputParser()
			result = chain.invoke({
				"subject": email.get('subject', ''),
				"body": email.get('body', '')
			})
			
			try:
				analysis = json.loads(result)
				scores.append({
					'email_id': email.get('id'),
					'courtesy_score': float(analysis.get('courtesy_score', 0.5)),
					'reasoning': analysis.get('reasoning', '')
				})
			except:
				scores.append({
					'email_id': email.get('id'),
					'courtesy_score': 0.5,
					'reasoning': 'Analysis failed'
				})
		
		state["communication_health_scores"]["courtesy"] = scores
		return state
	
	def analyze_audience_node(self, state: AgentState) -> AgentState:
		"""
		Analyzes audience-centricity of emails.
		
		Algorithm: LLM-based qualitative analysis (DeepSeek v3.1 via NVIDIA API)
		- Model: deepseek-ai/deepseek-v3.1-terminus
		- Input: Email subject + body + sender information
		- Processing: Recipient-relevance and personalization evaluation
		- Output: JSON with audience_score (0.0-1.0) and reasoning
		
		Rating Principle:
		- Score Range: 0.0 (not tailored) to 1.0 (perfectly tailored)
		- Factors Evaluated:
		  * Relevance: Content relevant to recipient's role/needs
		  * Knowledge Level: Appropriate technical depth
		  * Personalization: Specific to recipient, not generic
		  * Context Awareness: Acknowledges recipient's situation
		- Thresholds:
		  * Excellent (0.8-1.0): Highly personalized, perfectly relevant
		  * Good (0.6-0.8): Relevant and appropriately tailored
		  * Fair (0.4-0.6): Somewhat relevant but generic
		  * Poor (0.0-0.4): Not relevant or completely generic
		"""
		print("---ANALYZING AUDIENCE-CENTRICITY---")
		
		if "communication_health_scores" not in state:
			state["communication_health_scores"] = {}
		
		scores = []
		for email in state["preprocessed_emails"]:
			prompt = ChatPromptTemplate.from_template(
				"""
				Evaluate how well this email is tailored to its audience on a scale of 0.0 to 1.0.
				Consider: relevance to recipient, appropriate knowledge level, personalized content.
				
				Subject: {subject}
				Body: {body}
				From: {sender}
				
				Respond with JSON: {{"audience_score": 0.0-1.0, "reasoning": "brief explanation"}}
				"""
			)
			
			chain = prompt | self.llm | StrOutputParser()
			result = chain.invoke({
				"subject": email.get('subject', ''),
				"body": email.get('body', ''),
				"sender": email.get('from', '')
			})
			
			try:
				analysis = json.loads(result)
				scores.append({
					'email_id': email.get('id'),
					'audience_score': float(analysis.get('audience_score', 0.5)),
					'reasoning': analysis.get('reasoning', '')
				})
			except:
				scores.append({
					'email_id': email.get('id'),
					'audience_score': 0.5,
					'reasoning': 'Analysis failed'
				})
		
		state["communication_health_scores"]["audience"] = scores
		return state
	
	def analyze_timeliness_node(self, state: AgentState) -> AgentState:
		"""
		Analyzes timeliness and responsiveness of emails.
		
		Algorithm: LLM-based qualitative analysis + Heuristic timing analysis
		- Model: deepseek-ai/deepseek-v3.1-terminus (for content-based evaluation)
		- Input: Email subject + body + date/timestamp
		- Processing: 
		  * LLM evaluates urgency indicators in content
		  * Heuristic analysis of send time appropriateness
		  * Response pattern analysis (if thread context available)
		- Output: JSON with timeliness_score (0.0-1.0) and reasoning
		
		Rating Principle:
		- Score Range: 0.0 (very untimely) to 1.0 (perfectly timely)
		- Factors Evaluated:
		  * Appropriate Timing: Sent at appropriate business hours
		  * Response Delays: Reasonable time to respond (if reply)
		  * Urgency Handling: Appropriate urgency level for content
		  * Follow-up Frequency: Not excessive or insufficient
		- Thresholds:
		  * Excellent (0.8-1.0): Perfect timing, appropriate urgency
		  * Good (0.6-0.8): Generally timely, minor timing issues
		  * Fair (0.4-0.6): Some timing problems or urgency mismatch
		  * Poor (0.0-0.4): Untimely, inappropriate urgency, or excessive delays
		"""
		print("---ANALYZING TIMELINESS & RESPONSIVENESS---")
		
		if "communication_health_scores" not in state:
			state["communication_health_scores"] = {}
		
		scores = []
		for email in state["preprocessed_emails"]:
			# For timeliness, we need to analyze response patterns
			# This is simplified - would need thread analysis in production
			prompt = ChatPromptTemplate.from_template(
				"""
				Evaluate the timeliness and responsiveness indicated by this email on a scale of 0.0 to 1.0.
				Consider: appropriate timing, response delays, frequency of follow-ups.
				
				Subject: {subject}
				Body: {body}
				Date: {date}
				
				Respond with JSON: {{"timeliness_score": 0.0-1.0, "reasoning": "brief explanation"}}
				"""
			)
			
			chain = prompt | self.llm | StrOutputParser()
			result = chain.invoke({
				"subject": email.get('subject', ''),
				"body": email.get('body', ''),
				"date": email.get('date', '')
			})
			
			try:
				analysis = json.loads(result)
				scores.append({
					'email_id': email.get('id'),
					'timeliness_score': float(analysis.get('timeliness_score', 0.5)),
					'reasoning': analysis.get('reasoning', '')
				})
			except:
				scores.append({
					'email_id': email.get('id'),
					'timeliness_score': 0.5,
					'reasoning': 'Analysis failed'
				})
		
		state["communication_health_scores"]["timeliness"] = scores
		return state
	
	def aggregate_health_scores_node(self, state: AgentState) -> AgentState:
		"""
		Aggregation node: Consolidate all communication health results.
		This node is idempotent - can be called multiple times safely.
		
		Algorithm: Weighted Average Aggregation
		- Input: Individual scores from 6 analysis dimensions
		- Processing:
		  * Per-email aggregation: Simple average of all 6 dimension scores
		  * Cross-email aggregation: Average scores across all emails
		  * Overall health: Mean of all dimension averages
		- Output: Structured JSON with per-email and average scores
		
		Rating Principle:
		- Overall Health Score: Unweighted mean of 6 dimensions
		  * Formula: (clarity + completeness + correctness + courtesy + audience + timeliness) / 6
		- Individual Dimension Averages: Mean across all emails
		- Health Classification:
		  * Excellent (0.8-1.0): High scores across all dimensions
		  * Good (0.6-0.8): Solid performance, minor improvements possible
		  * Fair (0.4-0.6): Mixed performance, several areas need improvement
		  * Poor (0.0-0.4): Low scores, significant improvements needed
		- No weighting: All dimensions treated equally (can be customized)
		"""
		# Check if already aggregated (idempotent check)
		if "aggregated_health" in state and state.get("aggregated_health"):
			existing = state["aggregated_health"]
			# Check if we have all 6 dimensions
			health_scores = state.get("communication_health_scores", {})
			expected_dims = {'clarity', 'completeness', 'correctness', 'courtesy', 'audience', 'timeliness'}
			available_dims = set(health_scores.keys())
			if expected_dims.issubset(available_dims) and existing.get('average_scores', {}).get('overall'):
				# Already complete, return early
				return state
		
		print("---AGGREGATING HEALTH SCORES---")
		
		health_scores = state.get("communication_health_scores", {})
		
		# Wait for all 6 dimensions to be available
		expected_dims = {'clarity', 'completeness', 'correctness', 'courtesy', 'audience', 'timeliness'}
		available_dims = set(health_scores.keys())
		
		if not expected_dims.issubset(available_dims):
			# Not all dimensions analyzed yet, return state as-is (will be called again)
			print(f"Waiting for all dimensions. Available: {available_dims}, Expected: {expected_dims}")
			return state
		
		# Aggregate scores per email
		aggregated = {}
		email_ids = set()
		
		# Map dimension names to their score keys
		dimension_map = {
			'clarity': 'clarity_score',
			'completeness': 'completeness_score',
			'correctness': 'correctness_score',
			'courtesy': 'courtesy_score',
			'audience': 'audience_score',
			'timeliness': 'timeliness_score'
		}
		
		for dimension, scores in health_scores.items():
			score_key = dimension_map.get(dimension, f'{dimension}_score')
			for score_entry in scores:
				email_id = score_entry.get('email_id')
				email_ids.add(email_id)
				if email_id not in aggregated:
					aggregated[email_id] = {}
				# Store score using dimension name (without _score suffix)
				dimension_key = dimension.replace('_score', '') if dimension.endswith('_score') else dimension
				aggregated[email_id][dimension_key] = float(score_entry.get(score_key, 0.5))
		
		# Calculate overall health score per email
		for email_id in email_ids:
			scores = [aggregated[email_id].get(dim, 0.5) for dim in ['clarity', 'completeness', 'correctness', 'courtesy', 'audience', 'timeliness']]
			aggregated[email_id]['overall_health'] = sum(scores) / len(scores) if scores else 0.5
		
		# Calculate average scores across all emails
		avg_scores = {}
		for dimension in ['clarity', 'completeness', 'correctness', 'courtesy', 'audience', 'timeliness']:
			dimension_scores = [aggregated[email_id].get(dimension, 0.5) for email_id in email_ids if email_id in aggregated]
			avg_scores[dimension] = sum(dimension_scores) / len(dimension_scores) if dimension_scores else 0.5
		
		avg_scores['overall'] = sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0.5
		
		state["aggregated_health"] = {
			'per_email': aggregated,
			'average_scores': avg_scores,
			'total_emails': len(email_ids)
		}
		
		return state
	
	def explain_health_results_node(self, state: AgentState) -> AgentState:
		"""
		Explanation node: Generate natural language summary of communication health.
		"""
		print("---GENERATING HEALTH EXPLANATION---")
		
		aggregated = state.get("aggregated_health", {})
		health_scores = state.get("communication_health_scores", {})
		
		prompt = ChatPromptTemplate.from_template(
			"""
			Based on the communication health analysis results, provide a concise natural language explanation
			summarizing the main findings and reasoning.
			
			Average Scores:
			{avg_scores}
			
			Key findings from each dimension:
			- Clarity: {clarity_findings}
			- Completeness: {completeness_findings}
			- Correctness: {correctness_findings}
			- Courtesy: {courtesy_findings}
			- Audience-Centricity: {audience_findings}
			- Timeliness: {timeliness_findings}
			
			Provide a 2-3 paragraph summary explaining:
			1. Overall communication health assessment
			2. Key strengths and weaknesses
			3. Actionable recommendations for improvement
			"""
		)
		
		# Extract sample reasoning from each dimension
		dimension_findings = {}
		for dim in ['clarity', 'completeness', 'correctness', 'courtesy', 'audience', 'timeliness']:
			scores = health_scores.get(dim, [])
			if scores:
				dimension_findings[dim] = scores[0].get('reasoning', 'No findings')
			else:
				dimension_findings[dim] = 'No data available'
		
		chain = prompt | self.llm | StrOutputParser()
		explanation = chain.invoke({
			"avg_scores": aggregated.get('average_scores', {}),
			"clarity_findings": dimension_findings.get('clarity', ''),
			"completeness_findings": dimension_findings.get('completeness', ''),
			"correctness_findings": dimension_findings.get('correctness', ''),
			"courtesy_findings": dimension_findings.get('courtesy', ''),
			"audience_findings": dimension_findings.get('audience', ''),
			"timeliness_findings": dimension_findings.get('timeliness', '')
		})
		
		state["health_explanation"] = explanation
		return state

	def generate_drafts_node(self, state: AgentState) -> AgentState:
		"""
		Generates reply drafts for emails with low communication health.
		Emails that need improvement are prioritized for draft generation.
		"""
		print("---GENERATING DRAFTS---")
		
		drafts = []
		health_threshold = 0.4  # Low health emails need attention
		
		# Use aggregated health scores if available
		aggregated = state.get("aggregated_health", {})
		per_email = aggregated.get('per_email', {})
		
		for email_id, health_data in per_email.items():
			overall_health = health_data.get('overall_health', 0.5)
			
			if overall_health < health_threshold:
				# Find the original email data
				email_data = None
				for email in state.get("preprocessed_emails", []):
					if email.get('id') == email_id:
						email_data = email
						break
				
				if email_data:
					draft = self._generate_health_improvement_draft(email_data, health_data)
					drafts.append({
						"email_id": email_id,
						"email_data": email_data,
						"health_scores": health_data,
						"draft": draft
					})
		
		state["drafts"] = drafts
		return state

	def create_email_database_node(self, state: AgentState) -> AgentState:
		"""
		Creates a structured database from email analysis results.
		"""
		print("---CREATING EMAIL DATABASE---")
		
		if not state["email_analysis"]:
			raise Exception("No email analysis data available. Run analyze_emails_node first.")
		
		# Create structured database
		email_df = create_email_database(state["email_analysis"])
		state["email_database"] = email_df.to_dict()
		
		# Save to CSV
		csv_filename = save_email_database(email_df)
		print(f"Email database saved to: {csv_filename}")
		
		return state

	def analyze_email_database_node(self, state: AgentState) -> AgentState:
		"""
		Performs comprehensive XGBoost analysis on the email database.
		"""
		print("---ANALYZING EMAIL DATABASE---")
		
		if not state["email_database"]:
			raise Exception("No email database available. Run create_email_database_node first.")
		
		# Convert back to DataFrame
		email_df = pd.DataFrame(state["email_database"])
		
		# Perform comprehensive analysis
		analysis_results = perform_email_xgboost_analysis(
			email_df,
			n_estimators=self.settings.xgboost_n_estimators,
			learning_rate=self.settings.xgboost_learning_rate,
			max_depth=self.settings.xgboost_max_depth,
			random_state=self.settings.xgboost_random_state
		)
		state["email_analysis_results"] = analysis_results
		
		return state

	def generate_email_visualizations_node(self, state: AgentState) -> AgentState:
		"""
		Generates comprehensive visualizations for email analysis.
		"""
		print("---GENERATING EMAIL VISUALIZATIONS---")
		
		if not state["email_database"] or not state["email_analysis_results"]:
			raise Exception("Missing email database or analysis results.")
		
		# Convert back to DataFrame
		email_df = pd.DataFrame(state["email_database"])
		
		# Generate visualizations
		visualizations = create_email_visualizations(email_df, state["email_analysis_results"])
		state["email_visualizations"] = visualizations
		
		return state

	def summarize_email_results_node(self, state: AgentState) -> AgentState:
		"""
		Generates comprehensive summary of email analysis results using LLM.
		"""
		print("---SUMMARIZING EMAIL RESULTS---")
		
		if not state["email_database"] or not state["email_analysis_results"]:
			raise Exception("Missing email database or analysis results.")
		
		# Generate automated summary
		email_df = pd.DataFrame(state["email_database"])
		automated_summary = generate_email_summary(email_df, state["email_analysis_results"])
		
		# Enhance with LLM analysis
		prompt = ChatPromptTemplate.from_template(
			"""
			You are an expert email analyst. Based on the following comprehensive email analysis results,
			provide a detailed summary with actionable insights.

			Email Analysis Results:
			{analysis_results}

			Automated Summary:
			{automated_summary}

			Please provide:
			1. An executive summary of the most critical communication health insights.
			2. A breakdown of the key drivers of communication health, based on the feature importance scores and the 6 dimensions (clarity, completeness, correctness, courtesy, audience-centricity, timeliness).
			3. Actionable recommendations for improving email communication health. What should the user do differently based on this data?
			4. Identification of any surprising or unexpected patterns in the email communication health data.

			Focus on providing concrete, data-driven advice for improving communication effectiveness.
			"""
		)
		
		chain = prompt | self.llm | StrOutputParser()
		enhanced_summary = chain.invoke({
			"analysis_results": state["email_analysis_results"],
			"automated_summary": automated_summary
		})
		
		state["email_summary"] = enhanced_summary
		return state

	def _parse_email_message(self, msg: dict) -> dict:
		"""Parse Gmail message into structured data."""
		headers = msg['payload'].get('headers', [])
		subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
		from_header = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
		date_header = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
		
		# Extract body text
		body = ""
		if 'parts' in msg['payload']:
			for part in msg['payload']['parts']:
				if part['mimeType'] == 'text/plain':
					data = part['body']['data']
					body = base64.urlsafe_b64decode(data).decode('utf-8')
					break
		
		return {
			'id': msg['id'],
			'subject': subject,
			'from': from_header,
			'date': date_header,
			'body': body
		}

	def _extract_email_features(self, email_data: dict) -> List[float]:
		"""
		Extract features from email data for XGBoost model.
		Now focused on communication health indicators.
		"""
		features_dict = self._calculate_communication_health_features(email_data)
		# Return as list in consistent order
		return [
			features_dict['word_count'],
			features_dict['avg_sentence_length'],
			features_dict['has_clear_subject'],
			features_dict['has_structure'],
			features_dict['has_question_marks'],
			features_dict['has_action_items'],
			features_dict['has_contact_info'],
			features_dict['has_typos'],
			features_dict['has_caps_lock'],
			features_dict['polite_words'],
			features_dict['has_greeting'],
			features_dict['has_closing'],
			features_dict['personalization_score'],
			features_dict['has_recipient_name'],
			features_dict['has_timestamp']
		]

	def _analyze_email_with_llm(self, email_data: dict) -> dict:
		"""
		Analyze email content using LLM for qualitative insights.
		Now focuses on communication health categorization.
		"""
		prompt = ChatPromptTemplate.from_template(
			"""
			Analyze the following email and provide a structured JSON response with:
			- category: Classify the email into one of the following: "Inquiry", "Marketing", "Transactional", "Support Request", "Internal Communication", "Personal", "Security Alert", or "Spam".
			- sentiment: Analyze the sentiment and classify as "positive", "negative", or "neutral".
			- communication_health_level: Assess overall communication health as "excellent", "good", "fair", or "poor" based on clarity, completeness, correctness, courtesy, audience-fit, and timeliness.
			- key_points: Provide a brief, bulleted summary of the main points or actions required.

			Email Subject: {subject}
			Email Body: {body}

			Respond with valid JSON only.
			"""
		)
		
		chain = prompt | self.llm | StrOutputParser()
		analysis_text = chain.invoke({
			"subject": email_data.get('subject', ''),
			"body": email_data.get('body', '')
		})
		
		try:
			return json.loads(analysis_text)
		except json.JSONDecodeError:
			return {"category": "normal", "sentiment": "neutral", "communication_health_level": "fair", "key_points": "Analysis failed"}

	def _generate_health_improvement_draft(self, email_data: dict, health_data: dict) -> str:
		"""Generate a draft reply that improves communication health."""
		prompt = ChatPromptTemplate.from_template(
			"""
			Generate a professional reply draft for this email that demonstrates improved communication health.
			The original email had low scores in: {low_dimensions}
			
			Improve the reply by:
			- Ensuring clarity and conciseness
			- Including all necessary information and next steps
			- Using correct grammar and coherent structure
			- Maintaining a courteous and professional tone
			- Tailoring the message to the recipient
			- Being timely and responsive
			
			Original Email Subject: {subject}
			Original Email Body: {body}
			
			Health Scores:
			- Clarity: {clarity}
			- Completeness: {completeness}
			- Correctness: {correctness}
			- Courtesy: {courtesy}
			- Audience-fit: {audience}
			- Timeliness: {timeliness}
			
			Draft an improved professional response:
			"""
		)
		
		# Identify low-scoring dimensions
		low_dimensions = []
		for dim in ['clarity', 'completeness', 'correctness', 'courtesy', 'audience', 'timeliness']:
			score = health_data.get(dim, 0.5)
			if score < 0.5:
				low_dimensions.append(dim)
		
		chain = prompt | self.llm | StrOutputParser()
		draft = chain.invoke({
			"subject": email_data.get('subject', ''),
			"body": email_data.get('body', ''),
			"low_dimensions": ", ".join(low_dimensions) if low_dimensions else "none",
			"clarity": health_data.get('clarity', 0.5),
			"completeness": health_data.get('completeness', 0.5),
			"correctness": health_data.get('correctness', 0.5),
			"courtesy": health_data.get('courtesy', 0.5),
			"audience": health_data.get('audience', 0.5),
			"timeliness": health_data.get('timeliness', 0.5)
		})
		
		return draft


def create_agent_workflow(mode: str = "retail"):
	"""
	Creates and configures the LangGraph agent workflow.
	
	Args:
		mode: "retail" for retail data analysis, "email" for email analysis
	"""
	agent = Agent()

	workflow = StateGraph(AgentState)
	
	if mode == "retail":
		# Enhanced Retail Data Analysis Workflow
		# 1. Validate -> 2. Load -> 3. Explore -> 4. Engineer Features -> 5. Analyze -> 6. Visualize -> 7. Summarize
		workflow.add_node("validate_data", agent.validate_data_node)
		workflow.add_node("load_data", agent.load_data_node)
		workflow.add_node("explore_data", agent.explore_data_node)
		workflow.add_node("engineer_features", agent.engineer_features_node)
		workflow.add_node("analyze_data", agent.analyze_data_node)
		workflow.add_node("generate_visualizations", agent.generate_visualizations_node)
		workflow.add_node("summarize_results", agent.summarize_results_node)

		workflow.set_entry_point("validate_data")
		workflow.add_edge("validate_data", "load_data")
		workflow.add_edge("load_data", "explore_data")
		workflow.add_edge("explore_data", "engineer_features")
		workflow.add_edge("engineer_features", "analyze_data")
		workflow.add_edge("analyze_data", "generate_visualizations")
		workflow.add_edge("generate_visualizations", "summarize_results")
		workflow.add_edge("summarize_results", END)
	
	elif mode == "email":
		# Communication Health Analysis Workflow (as per diagram)
		# Input -> Preprocessing -> 6 Parallel Analysis Nodes -> Aggregation -> Explanation -> Output
		workflow.add_node("fetch_emails", agent.fetch_emails_node)
		workflow.add_node("preprocess_emails", agent.preprocess_emails_node)
		
		# Parallel analysis nodes (6 dimensions of communication health)
		workflow.add_node("analyze_clarity", agent.analyze_clarity_node)
		workflow.add_node("analyze_completeness", agent.analyze_completeness_node)
		workflow.add_node("analyze_correctness", agent.analyze_correctness_node)
		workflow.add_node("analyze_courtesy", agent.analyze_courtesy_node)
		workflow.add_node("analyze_audience", agent.analyze_audience_node)
		workflow.add_node("analyze_timeliness", agent.analyze_timeliness_node)
		
		# Aggregation and explanation
		workflow.add_node("aggregate_health", agent.aggregate_health_scores_node)
		workflow.add_node("explain_health", agent.explain_health_results_node)

		workflow.set_entry_point("fetch_emails")
		workflow.add_edge("fetch_emails", "preprocess_emails")
		
		# Preprocessing feeds into all 6 parallel analysis nodes
		workflow.add_edge("preprocess_emails", "analyze_clarity")
		workflow.add_edge("preprocess_emails", "analyze_completeness")
		workflow.add_edge("preprocess_emails", "analyze_correctness")
		workflow.add_edge("preprocess_emails", "analyze_courtesy")
		workflow.add_edge("preprocess_emails", "analyze_audience")
		workflow.add_edge("preprocess_emails", "analyze_timeliness")
		
		# All parallel nodes feed into aggregation
		workflow.add_edge("analyze_clarity", "aggregate_health")
		workflow.add_edge("analyze_completeness", "aggregate_health")
		workflow.add_edge("analyze_correctness", "aggregate_health")
		workflow.add_edge("analyze_courtesy", "aggregate_health")
		workflow.add_edge("analyze_audience", "aggregate_health")
		workflow.add_edge("analyze_timeliness", "aggregate_health")
		
		# Aggregation -> Explanation -> End
		workflow.add_edge("aggregate_health", "explain_health")
		workflow.add_edge("explain_health", END)

	return workflow


# For LangGraph Studio, export the compiled workflows
def get_workflow():
	"""Export retail workflow for LangGraph Studio."""
	workflow = create_agent_workflow(mode="retail")
	return workflow.compile()

def get_email_workflow():
	"""Export email communication health workflow for LangGraph Studio."""
	workflow = create_agent_workflow(mode="email")
	return workflow.compile()

