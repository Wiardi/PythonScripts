import camelot
import pandas as pd
import os
import glob

def check_for_single_letters(df):
    for column in df.columns:
        for cell in df[column]:
            if str(cell) in ['R', 'I', 'A', 'C']:
                return True
    return False

try:
    pdf_folder_path = '/Users/ward/Documents/Extract RACIs/PDFs/'
    combined_csv_path = '/Users/ward/Documents/Extract RACIs/combined_RACIs.csv'

    pdf_files = glob.glob(f"{pdf_folder_path}*.pdf")
    print(f"Found {len(pdf_files)} PDF files.")

    dfs_to_concat = []

    for pdf_file_path in pdf_files:
        print(f"Processing {pdf_file_path}...")
        tables = camelot.read_pdf(pdf_file_path, flavor='lattice', pages='all')
        pdf_name = os.path.splitext(os.path.basename(pdf_file_path))[0]
        
        for i, table in enumerate(tables):
            print(f"  Processing table {i+1}...")
            temp_csv_path = f'temp_table_{i}.csv'
            table.to_csv(temp_csv_path)
            
            df = pd.read_csv(temp_csv_path)
            has_single_letter = check_for_single_letters(df)
            
            if has_single_letter:
                print(f"    Table {i+1} has single letters. Appending to list.")
                df['Source_PDF'] = pdf_name
                df['Table_Index'] = i
                                
                # Rearrange the columns to put 'Source_PDF' and 'Table_Index' at the beginning
                cols = ['Source_PDF', 'Table_Index'] + [col for col in df.columns if col not in ['Source_PDF', 'Table_Index']]
                df = df[cols]
                
                dfs_to_concat.append(df)

            os.remove(temp_csv_path)

    if dfs_to_concat:
        print("Concatenating and saving DataFrame...")
        master_df = pd.concat(dfs_to_concat, ignore_index=True)
        master_df.to_csv(combined_csv_path, index=False)
        print(f"Combined and saved all tables to {combined_csv_path}")
    else:
        print("No tables with single letters found.")
        
except Exception as e:
    print(f"An error occurred: {e}")