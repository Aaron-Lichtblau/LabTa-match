import gspread
from oauth2client.service_account import ServiceAccountCredentials
import csv
import pandas as pd

def get_exp(exp_file, students):
    '''returns a dict of given students and their semesters of past labTA experience'''
    exp_dict = {}
    for student in students:
        exp_dict[student] = 0
    with open(str(exp_file), newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            firstname = row['First Name']
            lastname = row['Last Name']
            position = row['Position']
            student = firstname + " " + lastname
            #if student is in dict and if their position was 'labta', increase their exp count
            if ((student in exp_dict.keys()) and (position == 'Lab TA')):
                 exp_dict[student] += 1
    return(exp_dict)

def get_df():
    '''gets the dataframe from google sheet and makes a dict of dicts'''
        # use creds to create a client to interact with the Google Drive API
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('labTA-match-secret.json', scope)
        client = gspread.authorize(creds)

        # Find workbook and open the first sheet
        sheet = client.open('LabTA_test2').sheet1
        df = pd.DataFrame(sheet.get_all_records())
        return(df)
