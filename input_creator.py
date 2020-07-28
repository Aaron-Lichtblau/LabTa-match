import gspread
from oauth2client.service_account import ServiceAccountCredentials
import csv
import pandas as pd
from random import choice
from random import randint

STUD_SLOTS_WORKED_CAP = 2 #default cap on work shifts
SLOTS = ["M_7", "M_9","Tu_7", "Tu_9","W_7", "W_9","Th_7", "Th_9","F_7", "F_9","Sa_3", "Sa_4","Sa_5","Su_5","Su_6","Su_7","Su_8", "Su_9"]

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

def make_exp(students):
    exp_dist = [0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
    exp_list = []
    for student in students:
        exp_list.append(choice(exp_dist))

    return(exp_list)

def make_skill(df):
    #get experience dict
    exp_dict = {}
    students = list(df['name'])
    for index in range(len(df['name'])):
        exp_dict[str(df.at[index, 'name'])] = int(df.at[index, 'experience'])
    skill_list = []
    for stud in exp_dict:
        skill_list.append(randint(0, exp_dict[stud] + 1))
    return(skill_list)

#get list of slots from df
def get_slots(df):
    slots = df.columns.tolist()
    non_slots = ['name', 'slot_type', 'availability', 'cap', 'experience', 'skill', 'hours', 'happiness']
    for val in non_slots:
        try:
            slots.remove(val)
        except:
            continue
    return(slots)

#get a dict of days (keys) and slots on those days (values as lists)
def get_days(slotdict):
    day_dict = {'M':[], 'Tu':[], 'W':[], 'Th':[], 'F':[], 'Sa':[], "Su":[]}
    for slot in slotdict:
        day = slot[:-2]
        day_dict[day].append(slot)
    return day_dict

#gets overlaps dict
def get_overlaps(slots, min_gap, duration):
    OVERLAPS = {}
    for i_slot in slots:
        i_start_time = int(i_slot[-1])
        i_day = i_slot[:2]
        for j_slot in slots:
            j_start_time = int(j_slot[-1])
            j_day = j_slot[:2]
            if (i_start_time < j_start_time) and (i_day == j_day) and ((i_start_time + duration != j_start_time) and (j_start_time - i_start_time < min_gap + duration)):
                if j_slot not in OVERLAPS.keys():
                    OVERLAPS[j_slot] = [i_slot]
                else:
                    OVERLAPS[j_slot].append(i_slot)
    return(OVERLAPS)

#get prev slot dict
def get_prev_slots(df, duration):
    slots = get_slots(df)
    PREV_SLOT = {}
    for i_slot in slots:
        i_start_time = int(i_slot[-1])
        i_day = i_slot[:2]
        for j_slot in slots:
            j_start_time = int(j_slot[-1])
            j_day = j_slot[:2]
            if (i_start_time < j_start_time) and (i_day == j_day) and (i_start_time + duration == j_start_time):
                PREV_SLOT[j_slot] = i_slot

    return(PREV_SLOT)

#function will be replaced by get_cap above
def make_cap(students):
    cap_dist = [2, 2, 2, 2, 3, 3, 3, 4, 4, 5] # dist of sample caps
    cap_dict = {}
    for student in students:
        cap_dict[student] = 2

    cap_list = []
    for student in students:
        cap_list.append(cap_dict[student])
    return(cap_list)

def make_df():
    df = pd.DataFrame()


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

    exp_list = make_exp(STUDENTS) #list of made up exp
    df['experience'] = exp_list #add experience column to df

    return(df)

def get_df(csv_file):
    '''gets the dataframe from google sheet'''

    # # use creds to create a client to interact with the Google Drive API
    # scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    # creds = ServiceAccountCredentials.from_json_keyfile_name('labTA-match-secret.json', scope)
    # client = gspread.authorize(creds)
    #
    # # Find workbook and open the first sheet
    # sheet = client.open('LabTA_test2').sheet1
    # df = pd.DataFrame(sheet.get_all_records())

    df = pd.read_csv(csv_file) #df should have cols: name, slots, slot_type, cap
    row_nums = len(df['name'])
    students = list(df['name'])
    slots = get_slots(df)


    #add availability col (sum of prefs)
    availability_col = []
    for student in df['name']:
        student_id = df.loc[df['name'] == student].index[0]
        stud_avail = 0
        for slot in slots:
            stud_avail += df.at[student_id, slot]
        availability_col.append(stud_avail)
    df['availability'] = availability_col

    #add cap col
    shift_cap_list = make_cap(students)
    df['cap'] = shift_cap_list #add cap column to df

    #add experience col
    exp_list = get_exp('historical_data.csv', students) #list of exps in order of students
    df['experience'] = exp_list #add experience column to df

    skill_list = make_skill(df)
    df['skill'] = skill_list

    #add hours and happiness col (initialized to all 0's)
    hours_col = [0] * row_nums
    df['hours'] = hours_col
    happiness_col = [0] * row_nums
    df['happiness'] = happiness_col



    return(df)
