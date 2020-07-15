import gspread
from oauth2client.service_account import ServiceAccountCredentials
import csv
import pandas as pd

STUD_SLOTS_WORKED_CAP = 2 #default cap on work shifts

def unflip(dict):
    # swap keys and values to unflip
    unflipped_dict = {}
    for key in dict:
        unflipped_dict[dict[key]] = key

    return(unflipped_dict)

def get_exp(exp_file, students):
    '''returns a list of given students' semesters of past labTA experience'''
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

    exp_list = []
    for student in students:
        exp_list.append(exp_dict[student])

    return(exp_list)

#this function can be used if a new column is added to the historical data.csv
#file called "Cap" which has the student's cap on shifts they would work (2) if not given
def get_cap(cap_file, students):
    '''returns list of given students' caps on shifts'''
    cap_dict = {}
    for student in students:
        cap_dict[student] = STUD_SLOTS_WORKED_CAP
    with open(str(cap_file), newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            firstname = row['First Name']
            lastname = row['Last Name']
            position = row['Position']
            student = firstname + " " + lastname
            #if student is in dict and if their position was 'labta', increase their exp count
            if ((student in cap_dict.keys()) and (position == 'Lab TA')):
                 cap_dict[student] = row['Cap']

    cap_list = []
    for student in students:
        cap_list.append(cap_dict[student])
    return(cap_list)

#function will be replaced by get_cap above
def get_stud_cap(students):
    cap_dict = {}
    for student in students:
        cap_dict[student] = STUD_SLOTS_WORKED_CAP # for now all students work max of 2 shifts

    cap_dict['Uri Schwartz'] = 15
    cap_list = []
    for student in students:
        cap_list.append(cap_dict[student])
    return(cap_list)

def get_df():
    '''gets the dataframe from google sheet'''
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('labTA-match-secret.json', scope)
    client = gspread.authorize(creds)

    # Find workbook and open the first sheet
    sheet = client.open('LabTA_test2').sheet1
    df = pd.DataFrame(sheet.get_all_records())

    students = list(df['name'])
    stud_shift_cap = get_stud_cap(students)
    df['cap'] = stud_shift_cap #add cap column to df
    #get exp dict
    exp_dict = get_exp('historical_data.csv', students) #dict of students (keys) and number of semesters experience (values)
    df['experience'] = exp_dict #add experience column to df

    return(df)
