import os

file_path = "COMPANY_sentiment.csv"

if os.path.exists(file_path):
    os.remove(file_path)
    print("CSV file deleted.")
else:
    print("File does not exist.")