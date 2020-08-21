import csv
import pandas as pd
import helpers

#-------------------------------------------------------------------------------
# Input Creation and Processing
#-------------------------------------------------------------------------------

def get_slots(df):
    '''gets the slot names from the df'''
    slots = df.columns.tolist()
    non_slots = ['name', 'slot_type', 'availability', 'cap', 'experience', 'skill', 'hours', 'happiness', 'gap']
    for val in non_slots:
        try:
            slots.remove(val)
        except:
            continue
    return(slots)

def get_overlaps(slots, min_gap, duration):
    '''gets the dict of form: {slot: [overlapping slot1, overlapping slot2, ...], etc.}'''
    OVERLAPS = {}
    for i_slot in slots:
        i_start_time = helpers.get_start_time(i_slot)
        i_end_time = helpers.add_time(i_start_time, duration)
        i_day = i_slot[:2]
        for j_slot in slots:
            j_start_time = helpers.get_start_time(j_slot)
            j_day = j_slot[:2]
            if (i_start_time < j_start_time) and (i_day == j_day) and ((i_end_time != j_start_time) and (j_start_time < helpers.add_time(i_end_time, min_gap))):
                if j_slot not in OVERLAPS.keys():
                    OVERLAPS[j_slot] = [i_slot]
                else:
                    OVERLAPS[j_slot].append(i_slot)
    return(OVERLAPS)

def get_prev_slots(df, duration):
    '''gets the dict of form: {slot : previous slot, ...}'''
    slots = get_slots(df)
    prev_slot = {}
    for i_slot in slots:
        i_start_time = helpers.get_start_time(i_slot)
        i_end_time = helpers.add_time(i_start_time, duration)
        i_day = i_slot[:2]
        for j_slot in slots:
            j_start_time = helpers.get_start_time(j_slot)
            j_day = j_slot[:2]
            if (i_start_time < j_start_time) and (i_day == j_day) and (i_end_time == j_start_time):
                prev_slot[j_slot] = i_slot

    return(prev_slot)


def make_col(students, value):
    '''makes default columns'''
    cap_list = []
    for student in students:
        cap_list.append(value)
    return(cap_list)


def get_df(csv_file):
    '''gets the dataframe from csv file'''

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

    #add hours and happiness col (initialized to all 0's)
    hours_col = [0] * row_nums
    df['hours'] = hours_col
    happiness_col = [0] * row_nums
    df['happiness'] = happiness_col

    return(df)

def check_col(df, gap, cap, exp, skill):
    '''checks whether advanced columns have been added to the input csv file. If they aren't this fills in default values
    returns [bool, bool] of whether or not to make exp and skill displays for stats output'''
    students = list(df['name'])
    exp_display = True
    skill_display = True
    #check if gap, cap, exp, skill cols are in df
    if 'gap' not in list(df.columns):
        #add gap col
        gap_list = make_col(students, gap)
        df['gap'] = gap_list
    else:
        df.fillna(180, inplace=True)
    if 'cap' not in list(df.columns):
        #add cap col
        shift_cap_list = make_col(students, cap)
        df['cap'] = shift_cap_list #add cap column to df
    else:
        df.fillna(2, inplace=True)
    if 'experience' not in list(df.columns):
        #add experience col
        exp_list = make_col(students, exp)
        df['experience'] = exp_list #add experience column to df
        exp_display = False #if using default exp, don't make a display
    else:
        df.fillna(0, inplace=True)
    if 'skill' not in list(df.columns):
        skill_list = make_col(students, skill)
        df['skill'] = skill_list
        skill_display = False #if using default skill, don't make a display
    else:
        df.fillna(0, inplace=True)

    return [exp_display, skill_display]


# TO BE USED IF HISTORICAL DATA CAN BE PULLED FROM SOMEWHERE
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
