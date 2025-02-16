import os
import pandas as pd

# Specify the root folder containing year folders
folder_path = "C:/Users/asare/Documents/NSMQ Past Questions-20240529T175000Z-001/NSMQ Past Questions/NSMQ QUESTIONS SPREADSHEETS/"
# Initialize an empty dictionary to store DataFrames for each round

# Get the list of year folders
year_folders = ["2009", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021"]

# Loop through each year folder
for year_folder in year_folders:
    # Get the list of Excel files in the year folder
    excel_files = [f for f in os.listdir(os.path.join(folder_path, year_folder)) if f.endswith('.xlsx')]

    # Create a directory for the current year if it doesn't exist
    year_output_path = os.path.join(folder_path, year_folder + "_output")
    os.makedirs(year_output_path, exist_ok=True)

    # Loop through each Excel file
    for excel_file in excel_files:
        # Read all sheets from the Excel file into a dictionary of DataFrames
        file_path = os.path.join(folder_path, year_folder, excel_file)
        df_dict = pd.read_excel(file_path, sheet_name=None)

        # Loop through each round (sheet) in the Excel file
        for round_name, df in df_dict.items():
            # Add a column specifying the round of the question
            df['Round'] = round_name

            # Create a new workbook for each round
            round_file_name = f"{round_name}_{year_folder}.xlsx"
            round_file_path = os.path.join(year_output_path, round_file_name)

            # Write the DataFrame to a new Excel file for the current round
            with pd.ExcelWriter(round_file_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)

df.head
print("All files have been successfully processed!")
