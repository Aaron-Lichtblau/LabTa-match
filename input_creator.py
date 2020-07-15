import gspread
from oauth2client.service_account import ServiceAccountCredentials
# import csv
import pandas as pd
from random import choice
from random import randint

STUD_SLOTS_WORKED_CAP = 2 #default cap on work shifts

def unflip(dict):
    # swap keys and values to unflip
    unflipped_dict = {}
    for key in dict:
        unflipped_dict[dict[key]] = key

    return(unflipped_dict)

# def get_exp(exp_file, students):
#     '''returns a list of given students' semesters of past labTA experience'''
#     exp_dict = {}
#     for student in students:
#         exp_dict[student] = 0
#     with open(str(exp_file), newline='') as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             firstname = row['First Name']
#             lastname = row['Last Name']
#             position = row['Position']
#             student = firstname + " " + lastname
#             #if student is in dict and if their position was 'labta', increase their exp count
#             if ((student in exp_dict.keys()) and (position == 'Lab TA')):
#                  exp_dict[student] += 1
#
#     exp_list = []
#     for student in students:
#         exp_list.append(exp_dict[student])
#
#     return(exp_list)

def make_exp(students):
    exp_dist = [0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
    exp_list = []
    for student in students:
        exp_list.append(choice(exp_dist))

    return(exp_list)

#this function can be used if a new column is added to the historical data.csv
#file called "Cap" which has the student's cap on shifts they would work (2) if not given
# def get_cap(cap_file, students):
#     '''returns list of given students' caps on shifts'''
#     cap_dict = {}
#     for student in students:
#         cap_dict[student] = STUD_SLOTS_WORKED_CAP
#     with open(str(cap_file), newline='') as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             firstname = row['First Name']
#             lastname = row['Last Name']
#             position = row['Position']
#             student = firstname + " " + lastname
#             #if student is in dict and if their position was 'labta', increase their exp count
#             if ((student in cap_dict.keys()) and (position == 'Lab TA')):
#                  cap_dict[student] = row['Cap']
#
#     cap_list = []
#     for student in students:
#         cap_list.append(cap_dict[student])
#     return(cap_list)

#function will be replaced by get_cap above
def make_cap(students):
    cap_dist = [2, 2, 2, 2, 3, 3, 3, 4, 4, 5, 6, 7] # dist of sample caps
    cap_dict = {}
    for student in students:
        cap_dict[student] = choice(cap_dist)

    cap_list = []
    for student in students:
        cap_list.append(cap_dict[student])
    return(cap_list)

def make_df():
    df = pd.DataFrame()

    SLOTS = ["M_7", "M_9","Tu_7", "Tu_9","W_7", "W_9","Th_7", "Th_9","F_7", "F_9","Sa_3", "Sa_4","Sa_5","Su_5","Su_6","Su_7","Su_8", "Su_9"]
    STUDENTS = ['Aaron', 'Alfred', 'Anne Hath','Bob', 'Billy J', 'Charlie', 'Cleopatra','Chet B','Danielle', 'Demetris','Evan', 'Eisgruber','Faris', 'Gandalf','Gordon Ramsay', 'Guy F','Harrold', 'HAL 9000','Immanuel','Indiana J','Jack', 'James B','Jason B', 'Kerry', 'Lucy', 'Marrian', 'MJ', 'Napoleon', 'Nora', 'Nathan Drake','Oswald', 'Oprah', 'Peter', 'Quincy', 'Reese', 'Sandra', 'Theodore', 'Tony T', 'Tom Cruise', 'Uri', 'Val', 'Wally', 'Xerxes', 'Yang', 'Zachariah']
    row_nums = len(STUDENTS)

    df['name'] = STUDENTS #make name column
    avail_col = [0] * row_nums #make availability column
    for slot in SLOTS: #make slot columns
        slot_col = []
        for student in range(row_nums):
            pref = randint(0, 3)
            slot_col.append(pref)
            avail_col[student] += pref
        df[slot] = slot_col
    slot_type_col = [] #make slot type column
    for student in range(row_nums):
        types = [0, 2, 4]
        slot_type_col.append(choice(types))
    df['slot_type'] = slot_type_col
    hours_col = [0] * row_nums #make hours column
    df['hours'] = hours_col
    df['availability'] = avail_col #put in availability column
    hap_col = [0] * row_nums #make happiness column
    df['happiness'] = hap_col
    shift_cap_list = make_cap(STUDENTS)
    df['cap'] = shift_cap_list #add cap column to df
    #get exp dict
    exp_list = make_exp(STUDENTS) #dict of students (keys) and number of semesters experience (values)
    df['experience'] = exp_list #add experience column to df

    return(df)

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
    stud_shift_cap = make_cap(students)
    df['cap'] = stud_shift_cap #add cap column to df
    #get exp dict
    exp_dict = get_exp('historical_data.csv', students) #dict of students (keys) and number of semesters experience (values)
    df['experience'] = exp_dict #add experience column to df

    return(df)
