# Excel Data Transform Tool

Workshop code to combine data from different Excel files into nice, clean CSV files. It's perfect if you have data in different formats (Coke, Alibaba, or Pepsi style) and want to merge them together.

## 📥 Installing uv

First, you'll need to install the uv package manager. You can do this in one of these ways:

Using curl:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Start

1. Clone Report and move into folder
   ```bash
   git clone https://github.com/vinodismyname/excel-transform-excercise.git
   ```
2. Install Python stuff you need:
   ```bash
   uv  sync
   ```

3. Update a config file (see `config.yaml`) that tells the script where your Excel files are. Here's an example:
   ```yaml
   output_dir: "my_output_folder"
   files:
     - path: "data/file1.xlsx"
       sheets:
         - name: "Sheet1"
           format: "Coke"
         - name: "Sheet2"
           format: "Alibaba"
     - path: "data/file2.xlsx"
       sheets:
         - name: "Monthly Data"
           format: "Pepsi"
   ```

4. Run the script:
   ```bash
   python data_transform.py --config config.yaml
   ```

 The script will create CSV files in your output folder.

## 📝 What You Need in Your Config File

- `output_dir`: Where you want your CSV files to go
- `files`: List of your Excel files
  - `path`: Where each Excel file is
  - `sheets`: The Excel sheets you want to process
    - `name`: The name of the sheet
    - `format`: What kind of data it is ("Coke", "Alibaba", or "Pepsi")

## 🎯 What This Script Does

1. Reads your Excel files
2. Fixes up the data to be nice and clean
3. Makes three CSV files:
   - `coke_consolidated.csv`
   - `alibaba_consolidated.csv`
   - `pepsi_consolidated.csv`

## ⚠️ Common Problems and How to Fix Them

- **"File not found" error**: Double-check your file paths in the config file
- **"Sheet not found" error**: Make sure the sheet names in your config match exactly with the names in your Excel files
- **Empty output**: Check if your Excel files have data in them
- **Script crashes**: Make sure you installed all the required Python packages

## Need Help?

If you see error messages in red text:
1. Check if your config file is set up right
2. Make sure all your Excel files exist where you said they would be
3. Verify your Excel sheets have the right names
4. Make sure you installed all the Python packages needed

## Data Format Types

This script handles three types of data:

- **Coke**: Simple data that's already in the right format
- **Alibaba**: Data with categories and monthly values
- **Pepsi**: Data with multiple levels and monthly columns

Pick the right format for each sheet in your config file!