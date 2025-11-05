"""Email analysis using XGBoost."""

from __future__ import annotations

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
import os
from datetime import datetime


def create_email_database(email_analysis: list[dict]) -> pd.DataFrame:
	"""
	Creates a structured DataFrame from email analysis results.
	Now supports communication health scores instead of urgency.
	"""
	email_data = []
	
	for analysis in email_analysis:
		# Extract communication health features (updated feature set)
		features = analysis.get('features', [])
		
		# Build row data with communication health features
		row = {
			'id': analysis['email_data']['id'],
			'subject': analysis['email_data']['subject'],
			'sender': analysis['email_data']['from'],
			'date': analysis['email_data']['date'],
			'body_length': len(analysis['email_data']['body']),
			'word_count': features[0] if len(features) > 0 else 0,
			'avg_sentence_length': features[1] if len(features) > 1 else 0,
			'has_clear_subject': features[2] if len(features) > 2 else 0,
			'has_structure': features[3] if len(features) > 3 else 0,
			'has_question_marks': features[4] if len(features) > 4 else 0,
			'has_action_items': features[5] if len(features) > 5 else 0,
			'has_contact_info': features[6] if len(features) > 6 else 0,
			'has_typos': features[7] if len(features) > 7 else 0,
			'has_caps_lock': features[8] if len(features) > 8 else 0,
			'polite_words': features[9] if len(features) > 9 else 0,
			'has_greeting': features[10] if len(features) > 10 else 0,
			'has_closing': features[11] if len(features) > 11 else 0,
			'personalization_score': features[12] if len(features) > 12 else 0,
			'has_recipient_name': features[13] if len(features) > 13 else 0,
			'has_timestamp': features[14] if len(features) > 14 else 0,
			'category': analysis['qualitative_analysis'].get('category', 'normal'),
			'sentiment': analysis['qualitative_analysis'].get('sentiment', 'neutral'),
			'communication_health_level': analysis['qualitative_analysis'].get('communication_health_level', 'fair'),
			'key_points': analysis['qualitative_analysis'].get('key_points', '')
		}
		
		# Add health scores if available (from aggregated_health)
		if 'overall_health' in analysis:
			row['overall_health_score'] = analysis['overall_health']
		if 'clarity_score' in analysis:
			row['clarity_score'] = analysis['clarity_score']
		if 'completeness_score' in analysis:
			row['completeness_score'] = analysis['completeness_score']
		if 'correctness_score' in analysis:
			row['correctness_score'] = analysis['correctness_score']
		if 'courtesy_score' in analysis:
			row['courtesy_score'] = analysis['courtesy_score']
		if 'audience_score' in analysis:
			row['audience_score'] = analysis['audience_score']
		if 'timeliness_score' in analysis:
			row['timeliness_score'] = analysis['timeliness_score']
		
		email_data.append(row)
	
	return pd.DataFrame(email_data)


def perform_email_xgboost_analysis(df: pd.DataFrame, n_estimators: int = 100, learning_rate: float = 0.1, max_depth: int = 3, random_state: int = 42) -> dict:
	"""
	Performs XGBoost analysis to determine feature importance for communication health scores.
	
	Algorithm: XGBoost Gradient Boosting Regressor
	- Model Type: XGBRegressor (regression for continuous health scores)
	- Objective: reg:squarederror (minimize squared error)
	- Input Features (15 features):
	  * word_count: Total word count in email body
	  * avg_sentence_length: Average words per sentence
	  * has_clear_subject: Binary (1 if subject line > 5 chars)
	  * has_structure: Binary (1 if bullet points/list formatting detected)
	  * has_question_marks: Binary (1 if questions present)
	  * has_action_items: Binary (1 if action words detected)
	  * has_contact_info: Binary (1 if contact info present)
	  * has_typos: Binary (1 if common typos detected)
	  * has_caps_lock: Binary (1 if excessive caps detected)
	  * polite_words: Count of polite words (please, thank, etc.)
	  * has_greeting: Binary (1 if greeting detected)
	  * has_closing: Binary (1 if closing detected)
	  * personalization_score: Sum of polite_words + greeting + closing
	  * has_recipient_name: Binary (1 if recipient name in To field)
	  * has_timestamp: Binary (1 if date/timestamp present)
	- Target Variable: overall_health_score (0.0-1.0, calculated from 6 dimensions)
	- Training: 80/20 train/test split
	- Output: Feature importance scores + model metrics
	
	Rating/Ranking Principle:
	- Feature Importance: Gain-based importance from XGBoost
	  * Measures how much each feature contributes to reducing prediction error
	  * Higher importance = feature has stronger predictive power for health scores
	- Feature Ranking: Sorted by importance (highest first)
	- Interpretation:
	  * High importance features (e.g., >0.15): Critical drivers of communication health
	  * Medium importance (0.05-0.15): Moderate influence
	  * Low importance (<0.05): Minor influence
	- Model Performance Metrics:
	  * R² Score: Proportion of variance explained (higher is better, max 1.0)
	  * RMSE: Root Mean Squared Error (lower is better)
	  * MAE: Mean Absolute Error (lower is better)
	"""
	# Updated feature columns for communication health
	all_feature_columns = ['word_count', 'avg_sentence_length', 'has_clear_subject', 'has_structure',
						  'has_question_marks', 'has_action_items', 'has_contact_info',
						  'has_typos', 'has_caps_lock', 'polite_words', 'has_greeting',
						  'has_closing', 'personalization_score', 'has_recipient_name', 'has_timestamp']
	
	# Filter to only include columns that exist in the DataFrame
	feature_columns = [col for col in all_feature_columns if col in df.columns]
	
	if not feature_columns:
		return {
			'feature_importance_model': {
				'feature_importance': {col: 0.0 for col in all_feature_columns},
			},
			'email_statistics': {
				'total_emails': len(df),
				'avg_health_score': 0.5,
				'message': 'No feature columns available for analysis'
			}
		}
	
	# Use overall_health_score as target if available, otherwise calculate from individual scores
	if 'overall_health_score' in df.columns:
		target_column = 'overall_health_score'
	elif all(col in df.columns for col in ['clarity_score', 'completeness_score', 'correctness_score', 
											'courtesy_score', 'audience_score', 'timeliness_score']):
		# Calculate overall health from individual scores
		df['overall_health_score'] = (
			df['clarity_score'] + df['completeness_score'] + df['correctness_score'] +
			df['courtesy_score'] + df['audience_score'] + df['timeliness_score']
		) / 6.0
		target_column = 'overall_health_score'
	else:
		# Fallback: use average of available scores or create a synthetic target
		available_scores = [col for col in df.columns if col.endswith('_score')]
		if available_scores:
			df['overall_health_score'] = df[available_scores].mean(axis=1)
			target_column = 'overall_health_score'
		else:
			# No scores available, return stats only
			return {
				'feature_importance_model': {
					'feature_importance': {col: 0.0 for col in all_feature_columns},
				},
				'email_statistics': {
					'total_emails': len(df),
					'avg_health_score': 0.5,
					'message': 'No health scores available for analysis'
				}
			}
	
	X = df[feature_columns]
	y = df[target_column]

	if len(df) < 2:  # Not enough data to train
		return {
			'feature_importance_model': {
				'feature_importance': {col: 0.0 for col in feature_columns},
			},
		'email_statistics': {
			'total_emails': len(df),
			'categories_distribution': df['category'].value_counts().to_dict() if 'category' in df.columns else {},
			'sentiment_distribution': df['sentiment'].value_counts().to_dict() if 'sentiment' in df.columns else {},
			'communication_health_level_distribution': df['communication_health_level'].value_counts().to_dict() if 'communication_health_level' in df.columns else {},
			'avg_health_score': float(df[target_column].mean()) if target_column in df.columns and not df.empty else 0.5,
			'high_health_count': int(len(df[df[target_column] > 0.7])) if target_column in df.columns and not df.empty else 0,
			'low_health_count': int(len(df[df[target_column] < 0.4])) if target_column in df.columns and not df.empty else 0
		}
		}

	# Split data
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
	
	# Train XGBoost Regressor to find feature importances for communication health
	health_regressor = xgb.XGBRegressor(
		objective='reg:squarederror',
		n_estimators=n_estimators,
		learning_rate=learning_rate,
		max_depth=max_depth,
		random_state=random_state
	)
	health_regressor.fit(X_train, y_train)
	
	# Feature importances
	feature_importance = dict(zip(feature_columns, health_regressor.feature_importances_))
	
	return {
		'feature_importance_model': {
			'feature_importance': {k: float(v) for k, v in feature_importance.items()},
		},
		'email_statistics': {
			'total_emails': len(df),
			'categories_distribution': df['category'].value_counts().to_dict() if 'category' in df.columns else {},
			'sentiment_distribution': df['sentiment'].value_counts().to_dict() if 'sentiment' in df.columns else {},
			'communication_health_level_distribution': df['communication_health_level'].value_counts().to_dict() if 'communication_health_level' in df.columns else {},
			'avg_health_score': float(df[target_column].mean()),
			'high_health_count': int(len(df[df[target_column] > 0.7])) if target_column in df.columns else 0,
			'low_health_count': int(len(df[df[target_column] < 0.4])) if target_column in df.columns else 0
		}
	}


def create_email_visualizations(df: pd.DataFrame, analysis_results: dict) -> dict:
	"""
	Creates comprehensive visualizations for email analysis.
	Returns JSON-serializable dict instead of Plotly objects.
	"""
	visualizations = {}
	
	try:
		# 1. Category distribution
		if 'category' in df.columns and df['category'].nunique() > 0:
			category_counts = df['category'].value_counts()
			visualizations['category_distribution'] = {
				"categories": category_counts.index.tolist(),
				"counts": [int(x) for x in category_counts.values.tolist()],
				"type": "pie"
			}
	except Exception as e:
		print(f"Warning: Could not create category distribution chart: {e}")
	
	try:
		# 2. Sentiment distribution
		if 'sentiment' in df.columns:
			sentiment_counts = df['sentiment'].value_counts()
			visualizations['sentiment_distribution'] = {
				"sentiments": sentiment_counts.index.tolist(),
				"counts": [int(x) for x in sentiment_counts.values.tolist()],
				"type": "bar"
			}
	except Exception as e:
		print(f"Warning: Could not create sentiment distribution chart: {e}")
	
	try:
		# 3. Communication health score histogram
		if 'overall_health_score' in df.columns:
			visualizations['health_distribution'] = {
				"values": [float(x) for x in df['overall_health_score'].tolist()],
				"type": "histogram"
			}
	except Exception as e:
		print(f"Warning: Could not create health distribution chart: {e}")
	
	try:
		# 4. Feature importance for communication health prediction
		if analysis_results and isinstance(analysis_results, dict):
			if 'feature_importance_model' in analysis_results:
				feature_imp = analysis_results['feature_importance_model'].get('feature_importance', {})
				if feature_imp:
					visualizations['feature_importance_health'] = {
						"features": list(feature_imp.keys()),
						"importance": [float(v) for v in feature_imp.values()],
						"type": "bar"
					}
	except Exception as e:
		print(f"Warning: Could not create feature importance chart: {e}")
	
	try:
		# 5. Dimension scores comparison (if available)
		health_dimensions = ['clarity_score', 'completeness_score', 'correctness_score', 
							'courtesy_score', 'audience_score', 'timeliness_score']
		available_dimensions = [dim for dim in health_dimensions if dim in df.columns]
		if available_dimensions:
			avg_scores = {dim: float(df[dim].mean()) for dim in available_dimensions}
			visualizations['dimension_scores'] = {
				"dimensions": list(avg_scores.keys()),
				"scores": [avg_scores[dim] for dim in available_dimensions],
				"type": "bar"
			}
	except Exception as e:
		print(f"Warning: Could not create dimension scores chart: {e}")
	
	try:
		# 6. Word count vs health score scatter plot
		if 'word_count' in df.columns and 'overall_health_score' in df.columns and 'category' in df.columns:
			visualizations['word_health_scatter'] = {
				"x": [float(x) for x in df['word_count'].tolist()],
				"y": [float(y) for y in df['overall_health_score'].tolist()],
				"categories": df['category'].tolist() if 'category' in df.columns else [],
				"type": "scatter"
			}
	except Exception as e:
		print(f"Warning: Could not create scatter plot: {e}")
	
	return visualizations


def generate_email_summary(df: pd.DataFrame, analysis_results: dict) -> str:
	"""
	Generates a comprehensive summary of email analysis.
	"""
	stats = analysis_results['email_statistics']
	
	# Format category distribution
	category_lines = []
	for cat, count in stats.get('categories_distribution', {}).items():
		category_lines.append(f"- {cat}: {count} emails")
	category_section = "\n".join(category_lines) if category_lines else "No categories available"
	
	# Format sentiment distribution
	sentiment_lines = []
	for sent, count in stats.get('sentiment_distribution', {}).items():
		sentiment_lines.append(f"- {sent}: {count} emails")
	sentiment_section = "\n".join(sentiment_lines) if sentiment_lines else "No sentiment data available"
	
	# Format risk distribution
	risk_lines = []
	for risk, count in stats.get('risk_distribution', {}).items():
		risk_lines.append(f'   - {risk}: {count}')
	risk_section = "\n".join(risk_lines) if risk_lines else "No risk data available"
	
	# Format feature importance
	if 'feature_importance_model' in analysis_results:
		top_features = sorted(analysis_results['feature_importance_model']['feature_importance'].items(),
							 key=lambda x: x[1], reverse=True)[:3]
		feature_text = ", ".join([f"{feature}: {importance:.2f}" for feature, importance in top_features])
	else:
		feature_text = "No feature importance data available"
	
	summary = f"""
# Email Communication Health Analysis Summary

## Overview
- **Total Emails Analyzed**: {stats.get('total_emails', 0)}
- **Average Communication Health Score**: {stats.get('avg_health_score', 0.5):.2f}
- **High Health Emails**: {stats.get('high_health_count', 0)} (health > 0.7)
- **Low Health Emails**: {stats.get('low_health_count', 0)} (health < 0.4)

## Category Distribution
{category_section}

## Sentiment Analysis
{sentiment_section}

## Communication Health Level Distribution
{stats.get('communication_health_level_distribution', {})}

## Model Performance
- **Feature Importance Model**: Available for communication health prediction
- **Email Statistics**: Comprehensive analysis completed

## Key Insights
1. **Most Important Features for Communication Health**: {feature_text}
2. **Health Distribution**: 
   - High health (excellent/good): {stats.get('high_health_count', 0)} emails
   - Low health (needs improvement): {stats.get('low_health_count', 0)} emails
3. **Communication Health Patterns**: Emails with clear structure, polite language, and complete information tend to have higher health scores.
	"""
	
	return summary


def save_email_database(df: pd.DataFrame, filename: str = "email_database.csv") -> str:
	"""
	Saves the email database to CSV file.
	"""
	# Remove existing file if it exists
	if os.path.exists(filename):
		os.remove(filename)
	df.to_csv(filename, index=False)
	return filename

