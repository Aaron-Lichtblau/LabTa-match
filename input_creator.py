import gspread
from oauth2client.service_account import ServiceAccountCredentials
import csv
import pandas as pd

STUD_SLOTS_WORKED_CAP = 2 #default cap on work shifts

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

#this function can be used if a new column is added to the historical data.csv
#file called "Cap" which has the student's cap on shifts they would work
def get_cap(cap_file, students):
    '''returns dict of given students and their cap on shifts'''
    cap_dict = {}
    for student in students:
        exp_dict[student] = STUD_SLOTS_WORKED_CAP
    with open(str(cap_file), newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            firstname = row['First Name']
            lastname = row['Last Name']
            position = row['Position']
            student = firstname + " " + lastname
            #if student is in dict and if their position was 'labta', increase their exp count
            if ((student in exp_dict.keys()) and (position == 'Lab TA')):
                 cap_dict[student] = row['Cap']
    return(cap_dict)


def get_df():
    '''gets the dataframe from google sheet'''
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('labTA-match-secret.json', scope)
    client = gspread.authorize(creds)

    # Find workbook and open the first sheet
    sheet = client.open('LabTA_test2').sheet1
    df = pd.DataFrame(sheet.get_all_records())

    return(df)
