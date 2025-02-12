#!/usr/bin/env python3
"""
Script Name: data_transform.py

Description:
  Reads a YAML config file to:
    1. Locate and load specific Excel files and sheets.
    2. Identify each sheet's format type ("Coke", "Alibaba", or "Pepsi").
    3. Apply the correct transformation to each sheet.
    4. Consolidate results into one DataFrame per format type.
    5. Export each consolidated DataFrame to a CSV in the configured output directory.

Usage:
  python data_transform.py --config config.yaml
"""

import os
import sys
import argparse
import logging
import pandas as pd

# You will need pyyaml for reading YAML configs:
#    pip install pyyaml
import yaml

# ------------------------------------------------
# 1. Configure Logging
# ------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ------------------------------------------------
# 2. Define Transformation Helper Functions
# ------------------------------------------------

def transform_coke(df: pd.DataFrame) -> pd.DataFrame:
    """
    For the Coke format, we simply take the data “as is.”
    df is already read from the correct sheet.
    Return df unchanged (or do minimal cleanup if needed).
    """
    return df

def transform_alibaba(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform Alibaba-format data based on the sample layout:
    
    Sample raw df (header=None):
    
           0          1         2
    0   category     Create       NaN
    1     orange  Monthly %     value
    2          1   0.343443  0.424048
    3          2   0.427734   0.90146
    4          3    0.08213  0.241209
    5          4   0.628912  0.335099
    ... etc ...
    
    We want to produce:
    Category | Month | Value | Metric_Name
    
    Where 'Category' is e.g. "orange" or "apple",
    'Month' is the integer in column 0 (e.g. 1..12),
    'Value' is the float in column 2,
    'Metric_Name' is "Create" (from row 0 col 1).
    
    Assumes each category line is followed by exactly 12 month rows.
    Adjust if data can vary in structure.
    """
    data = df.values.tolist()
    nrows = len(data)
    
    # Retrieve the metric name from row 0, col 1 (e.g. "Create")
    if nrows == 0 or len(data[0]) < 2 or pd.isna(data[0][1]):
        metric_name = "unknown_metric"
    else:
        metric_name = str(data[0][1]).strip()
    
    # We'll skip row 0 (the "headers") and row 1 (the "orange Monthly% value" line).
    # Actually, row 1's col0 is the first category name: "orange."
    # But let's do a flexible approach:
    
    records = []
    i = 1  # start scanning from row 1
    while i < nrows:
        row = data[i]
        # If col0 is non-empty, treat that as a new category
        # (In example: row 1 => ["orange", "Monthly %", "value"])
        # (In example: row14 => ["apple", NaN, NaN])
        if row and pd.notna(row[0]):
            # This is a new category
            category = str(row[0]).strip()
            
            # Move to the next row, parse the next 12 lines as month/value
            i += 1
            for _ in range(12):
                if i >= nrows:
                    break
                month_row = data[i]
                i += 1
                
                # Attempt to parse month & value from columns 0 and 2
                try:
                    month_val = int(month_row[0])
                    value     = float(month_row[2])
                    records.append([category, month_val, value, metric_name])
                except:
                    # If there's any parsing error or NaN, skip
                    continue
        else:
            # If we don't detect a valid category, just skip this row
            i += 1
    
    # Create the final DataFrame
    df_out = pd.DataFrame(records, columns=["Category","Month","Value","Metric_Name"])
    return df_out


def transform_pepsi(df: pd.DataFrame) -> pd.DataFrame:
    """
    For the Pepsi format:
      - 'Wide' format with columns: [level1, level2, level3, Jan..Dec, metric type]
      - Need to pivot so months become rows:
        final columns: ["level1", "level2", "level3", "Month", "Metric type", "value"]
    """
    
    month_map = {
        "january": 1, "february": 2, "march": 3,  "april": 4,   "may": 5,      "june": 6,
        "july": 7,   "august": 8,   "september": 9,"october": 10,"november": 11,"december": 12
    }
    
    # Lower-case the columns to facilitate matching
    df.columns = [str(c).lower() for c in df.columns]
    
    static_cols = ["level 1", "level 2", "level 3", "metric type"]
    # For safety, keep only columns that actually exist in the DataFrame
    static_cols = [c for c in static_cols if c in df.columns]
    
    # Identify month columns by matching with month_map keys
    month_cols = [c for c in df.columns if c in month_map]
    
    # 'melt' to pivot from wide to tall
    melted = df.melt(
        id_vars=static_cols,
        value_vars=month_cols,
        var_name="MonthName",
        value_name="value"
    )
    
    # Convert textual month name to numeric index
    melted["Month"] = melted["MonthName"].map(month_map)
    
    # Rename columns to final desired
    rename_map = {
        "level 1": "level1",
        "level 2": "level2",
        "level 3": "level3"
    }
    melted.rename(columns=rename_map, inplace=True)
    
    # Reorder columns
    final_cols = ["level1","level2","level3","Month","metric type","value"]
    melted = melted[final_cols]
    
    return melted

# ------------------------------------------------
# 3. Main function with config-driven logic
# ------------------------------------------------

def main(config_path: str):
    # 3A. Read and parse YAML config
    if not os.path.exists(config_path):
        logging.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Where to save output CSVs
    output_dir = config.get("output_dir", "output_data")
    os.makedirs(output_dir, exist_ok=True)
    
    # We will store consolidated data for each format in separate DataFrames
    # Initialize them here
    # If you know the desired columns in advance, you can predefine columns to 
    # keep them consistent, e.g. for Alibaba or Pepsi.
    format_data = {
        "Coke"    : [],
        "Alibaba" : [],
        "Pepsi"   : []
    }
    
    # 3B. Iterate over files specified in the config
    files_list = config.get("files", [])
    if not files_list:
        logging.warning("No files listed in the config. Nothing to process.")
        return
    
    for file_info in files_list:
        file_path = file_info.get("path")
        sheet_specs = file_info.get("sheets", [])
        
        # Check that the file exists
        if not os.path.exists(file_path):
            logging.warning(f"File does not exist, skipping: {file_path}")
            continue
        
        for sheet_spec in sheet_specs:
            sheet_name = sheet_spec.get("name")
            fmt = sheet_spec.get("format")
            
            if not fmt or fmt not in format_data.keys():
                logging.warning(f"Unknown or missing format for sheet {sheet_name} in file {file_path}. Skipping.")
                continue
            
            # Attempt to read the specified sheet. 
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            except Exception as e:
                logging.error(f"Failed to read {file_path}, sheet '{sheet_name}': {e}")
                continue
            
            if df.empty:
                logging.warning(f"Empty data in {file_path}, sheet '{sheet_name}'. Skipping.")
                continue
            
            # 3C. Apply the correct transformation
            try:
                if fmt == "Coke":
                    transformed = transform_coke(df)
                elif fmt == "Alibaba":
                    # Typically read with no header for Alibaba (depending on your layout)
                    # Re-read if needed:
                    df_no_header = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                    transformed = transform_alibaba(df_no_header)
                elif fmt == "Pepsi":
                    transformed = transform_pepsi(df)
                else:
                    # Should not happen because we checked above, but just in case
                    continue
                
                # 3D. Append the transformed data to the aggregator list
                if not transformed.empty:
                    format_data[fmt].append(transformed)
            
            except Exception as e:
                logging.error(f"Transformation failed for {file_path}, sheet '{sheet_name}': {e}")
                continue
    
    # ------------------------------------------------
    # 4. Consolidate and output to CSV
    # ------------------------------------------------
    #   One CSV per format: 
    #   - Coke => coke_consolidated.csv
    #   - Alibaba => alibaba_consolidated.csv
    #   - Pepsi => pepsi_consolidated.csv
    
    # (A) Coke
    if format_data["Coke"]:
        df_coke = pd.concat(format_data["Coke"], ignore_index=True)
        coke_out = os.path.join(output_dir, "coke_consolidated.csv")
        df_coke.to_csv(coke_out, index=False)
        logging.info(f"Coke consolidated data written to: {coke_out}")
    
    # (B) Alibaba
    if format_data["Alibaba"]:
        df_alibaba = pd.concat(format_data["Alibaba"], ignore_index=True)
        alibaba_out = os.path.join(output_dir, "alibaba_consolidated.csv")
        df_alibaba.to_csv(alibaba_out, index=False)
        logging.info(f"Alibaba consolidated data written to: {alibaba_out}")
    
    # (C) Pepsi
    if format_data["Pepsi"]:
        df_pepsi = pd.concat(format_data["Pepsi"], ignore_index=True)
        pepsi_out = os.path.join(output_dir, "pepsi_consolidated.csv")
        df_pepsi.to_csv(pepsi_out, index=False)
        logging.info(f"Pepsi consolidated data written to: {pepsi_out}")

# ------------------------------------------------
# 5. Command-line Entry Point
# ------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data transformation script for Coke, Alibaba, and Pepsi formats with config.")
    parser.add_argument("--config", required=True, help="Path to the YAML config file.")
    args = parser.parse_args()

    main(args.config)
