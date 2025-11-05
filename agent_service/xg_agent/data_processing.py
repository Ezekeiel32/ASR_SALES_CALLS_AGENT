"""Data preprocessing for retail analysis."""

from __future__ import annotations

import pandas as pd
import numpy as np


def load_and_preprocess_data(file_path: str = "online_retail_II.xlsx") -> pd.DataFrame:
	"""
	Loads and preprocesses retail data from various file formats.

	Args:
		file_path (str): The path to the data file (Excel, CSV, etc.).

	Returns:
		pd.DataFrame: The preprocessed DataFrame.
	"""
	# Load the data based on file extension
	if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
		df = pd.read_excel(file_path, sheet_name=None)
		df = pd.concat(df.values(), ignore_index=True)
	elif file_path.endswith('.csv'):
		df = pd.read_csv(file_path)
	else:
		raise ValueError(f"Unsupported file format: {file_path}. Please use Excel (.xlsx/.xls) or CSV (.csv) files.")

	# Handle column name variations
	customer_id_col = 'Customer ID' if 'Customer ID' in df.columns else 'CustomerID'
	invoice_col = 'Invoice' if 'Invoice' in df.columns else 'InvoiceNo'
	
	# Drop rows with missing Customer ID
	if customer_id_col in df.columns:
		df.dropna(subset=[customer_id_col], inplace=True)

	# Remove canceled orders
	if invoice_col in df.columns:
		df = df[~df[invoice_col].astype(str).str.startswith('C')]

	# Handle column name variations for Quantity and Price
	quantity_col = 'Quantity' if 'Quantity' in df.columns else 'Qty'
	price_col = 'Price' if 'Price' in df.columns else 'UnitPrice'
	
	# Ensure Quantity and Price are positive
	if quantity_col in df.columns and price_col in df.columns:
		df = df[(df[quantity_col] > 0) & (df[price_col] > 0)]
		
		# Feature Engineering
		df['TotalPrice'] = df[quantity_col] * df[price_col]
	
	# Handle date column variations
	date_col = 'InvoiceDate' if 'InvoiceDate' in df.columns else 'InvoiceDate'
	if date_col in df.columns:
		df['InvoiceDate'] = pd.to_datetime(df[date_col])
		df['Year'] = df['InvoiceDate'].dt.year
		df['Month'] = df['InvoiceDate'].dt.month
		df['Day'] = df['InvoiceDate'].dt.day
	else:
		# If no date column exists, create dummy date columns
		print("Warning: No date column found. Creating dummy date columns.")
		df['Year'] = 2023
		df['Month'] = 1
		df['Day'] = 1

	return df



