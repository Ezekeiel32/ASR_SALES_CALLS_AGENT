"""XGBoost analysis for retail data."""

from __future__ import annotations

import pandas as pd
import xgboost as xgb
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import plotly.express as px


def perform_xgboost_analysis(df: pd.DataFrame, n_estimators: int = 100, learning_rate: float = 0.1, max_depth: int = 3, random_state: int = 42) -> dict:
	"""
	Performs XGBoost regression analysis to predict revenue with comprehensive metrics and visualizations.

	Args:
		df (pd.DataFrame): The input DataFrame with customer data.
		n_estimators (int): Number of XGBoost estimators
		learning_rate (float): Learning rate
		max_depth (int): Max depth
		random_state (int): Random state

	Returns:
		dict: A dictionary containing model performance, feature importances, and visualization data.
	"""
	# Handle column name variations and check for required columns
	quantity_col = 'Quantity' if 'Quantity' in df.columns else ('Qty' if 'Qty' in df.columns else None)
	price_col = 'Price' if 'Price' in df.columns else ('UnitPrice' if 'UnitPrice' in df.columns else None)
	year_col = 'Year' if 'Year' in df.columns else None
	month_col = 'Month' if 'Month' in df.columns else None
	day_col = 'Day' if 'Day' in df.columns else None
	total_price_col = 'TotalPrice' if 'TotalPrice' in df.columns else None
	
	# Check for required columns
	missing_cols = []
	if quantity_col is None:
		missing_cols.append('Quantity/Qty')
	if price_col is None:
		missing_cols.append('Price/UnitPrice')
	if year_col is None:
		missing_cols.append('Year')
	if month_col is None:
		missing_cols.append('Month')
	if day_col is None:
		missing_cols.append('Day')
	if total_price_col is None:
		missing_cols.append('TotalPrice')
	
	if missing_cols:
		available_cols = list(df.columns)
		raise ValueError(f"Missing required columns: {missing_cols}. Available columns: {available_cols}")
	
	# Define features (X) and target (y) using the mapped column names
	features = [quantity_col, price_col, year_col, month_col, day_col]
	target = total_price_col

	X = df[features]
	y = df[target]

	# Split the data into training and testing sets
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

	# Initialize and train the XGBoost regressor
	xgb_regressor = xgb.XGBRegressor(
		objective='reg:squarederror',
		n_estimators=n_estimators,
		learning_rate=learning_rate,
		max_depth=max_depth,
		random_state=random_state
	)
	
	xgb_regressor.fit(X_train, y_train)

	# Make predictions and evaluate the model
	y_pred = xgb_regressor.predict(X_test)
	mse = mean_squared_error(y_test, y_pred)
	rmse = np.sqrt(mse)
	mae = mean_absolute_error(y_test, y_pred)
	r2 = r2_score(y_test, y_pred)

	# Get feature importances
	feature_importances = dict(zip(features, xgb_regressor.feature_importances_))

	# Create visualizations
	visualizations = create_retail_visualizations(X_test, y_test, y_pred, feature_importances, df, features, target)

	# Prepare the results
	analysis_results = {
		"model_performance": {
			"rmse": float(rmse),
			"mae": float(mae),
			"r2_score": float(r2),
			"mse": float(mse)
		},
		"feature_importances": {k: float(v) for k, v in feature_importances.items()},
		"visualizations": visualizations,
		"data_statistics": {
			"total_records": len(df),
			"features_used": features,
			"target_variable": target,
			"data_shape": list(df.shape),
			"feature_correlations": {k: float(v) for k, v in df[features + [target]].corr()[target].to_dict().items()}
		}
	}

	return analysis_results


def create_retail_visualizations(X_test, y_test, y_pred, feature_importances, df, features, target) -> dict:
	"""
	Creates comprehensive visualizations for retail data analysis.
	Returns dict with visualization data (not Plotly objects for JSON serialization).
	"""
	visualizations = {}
	
	# Convert to JSON-serializable format
	# 1. Actual vs Predicted scatter plot data
	visualizations['actual_vs_predicted'] = {
		"x": [float(x) for x in y_test],
		"y": [float(y) for y in y_pred],
		"type": "scatter"
	}
	
	# 2. Feature importance data
	feature_names = list(feature_importances.keys())
	importance_values = list(feature_importances.values())
	visualizations['feature_importance'] = {
		"features": feature_names,
		"importance": [float(v) for v in importance_values]
	}
	
	# 3. Residual plot data
	residuals = y_test - y_pred
	visualizations['residual_plot'] = {
		"x": [float(x) for x in y_pred],
		"y": [float(y) for y in residuals],
		"type": "scatter"
	}
	
	# 4. Target distribution data
	visualizations['target_distribution'] = {
		"values": [float(v) for v in df[target].tolist()],
		"type": "histogram"
	}
	
	# 5. Correlation matrix data
	corr_matrix = df[features + [target]].corr()
	visualizations['correlation_heatmap'] = {
		"matrix": corr_matrix.to_dict(),
		"labels": list(corr_matrix.columns)
	}
	
	# 6. Prediction error distribution
	error_dist = y_test - y_pred
	visualizations['error_distribution'] = {
		"values": [float(v) for v in error_dist.tolist()],
		"type": "histogram"
	}
	
	return visualizations


def generate_retail_summary(analysis_results: dict) -> str:
	"""
	Generates a comprehensive summary of retail analysis results.
	"""
	perf = analysis_results['model_performance']
	stats = analysis_results['data_statistics']
	feature_imp = analysis_results['feature_importances']
	
	summary = f"""
# Retail Data Analysis Summary

## Model Performance Metrics
- **Root Mean Squared Error (RMSE)**: {perf['rmse']:.2f}
- **Mean Absolute Error (MAE)**: {perf['mae']:.2f}
- **R² Score**: {perf['r2_score']:.2%}
- **Mean Squared Error (MSE)**: {perf['mse']:.2f}

## Dataset Statistics
- **Total Records**: {stats['total_records']}
- **Data Shape**: {stats['data_shape'][0]} rows × {stats['data_shape'][1]} columns
- **Target Variable**: {stats['target_variable']}
- **Features Used**: {', '.join(stats['features_used'])}

## Feature Importance Ranking
{chr(10).join([f"- {feature}: {importance:.3f}" for feature, importance in sorted(feature_imp.items(), key=lambda x: x[1], reverse=True)])}

## Key Insights
1. **Most Predictive Features**: {', '.join([f"{k}: {v:.3f}" for k, v in sorted(feature_imp.items(), key=lambda x: x[1], reverse=True)[:2]])}
2. **Model Performance**: The model explains {perf['r2_score']:.2%} of the variance in revenue.
3. **Average Prediction Error**: ±{perf['mae']:.2f} units of currency.
4. **Feature Correlations**: {chr(10).join([f'   - {feat}: {corr:.3f}' for feat, corr in stats['feature_correlations'].items() if feat != 'TotalPrice'])}

## Recommendations
- Focus on optimizing the most influential features: {', '.join([k for k, v in sorted(feature_imp.items(), key=lambda x: x[1], reverse=True)[:2]])}
- Consider seasonal patterns based on Month/Day features
- Monitor quantity and pricing strategies as key revenue drivers
	"""
	
	return summary



