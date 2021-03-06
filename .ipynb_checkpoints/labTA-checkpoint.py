import gspread
import math
import json
import subprocess
import random
from schedule import Schedule
import swap
import stats
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import numpy as np


HOURS_LIMIT = 4 #limit of hours a TA can work
MAX_VALUE = 10
MIN_VALUE = 0
OVERLAPS = {'Sa_4': 'Sa_3', 'Sa_5':'Sa_4', 'Su_6':'Su_5', 'Su_7':'Su_6', 'Su_8':'Su_7', 'Su_9':'Su_8'} #dict of slots to check as keys, and overlapping slots as values
# slots and num of TA's desired
slotdict = {"M_7" : 8, "M_9" : 6,"Tu_7" : 5, "Tu_9" : 4,"W_7" : 4, "W_9" : 4,"Th_7" : 4, "Th_9" : 4,"F_7" : 4, "F_9" : 4,"Sa_3" : 5, "Sa_4" : 6,"Sa_5" : 5,"Su_5" : 4,"Su_6" : 3,"Su_7" : 6,"Su_8" : 4, "Su_9" : 6}
NUM_SLOTS = 16.0 #number of slots
NUM_STUDENTS = 45
MAX_HAP = 258.0
score = 3


def viable_cand(df, slot, score):
    """check for candidates who reported score on slot"""
    candidates = []
    #check that the student isn't working an overlapping shift
    overlap_slots = OVERLAPS.keys()
    if slot in overlap_slots:
        #get list of students working less than hour cap
        available = df.loc[df['hours'] < HOURS_LIMIT, ['name', str(OVERLAPS[slot]),str(slot)]]
        #remove students already working in the overlapping slot (their slot will be negative int)
        available = available.loc[available[OVERLAPS[slot]] > 0,['name', str(slot)]]
    else:
        #get list of students working less than hour cap
        available = df.loc[df['hours'] < HOURS_LIMIT, ['name', str(slot)]]

    #get students who reported correct score
    cand_rows = available.loc[(available[slot] >= score)].index
    candidates = list(cand_rows)
    return(candidates) # candidates are their row number, not name!

def equalize(df, slot_candidates):
    """equalize the order of candidates based on how happy they already are"""
    #initial equalDict
    cand_dict = {}
    # randomize candidate list
    random.shuffle(slot_candidates)
    # order by their happiness score
    for cand in slot_candidates:
        cand_dict[cand] = df.at[cand, 'happiness']
    # order equalDict by values
    sorted_cand = sorted(cand_dict.items(), key=lambda x: x[1])
    # create list of sorted candidates
    candidates = []
    for i in sorted_cand:
        candidates.append(i[0])

    return(candidates)

def update_schedule(df, schedule, slot, student, score):
    """put students into schedule, update their slot to -1, update hours col, update happiness"""
    # if (score == 1):
    #     print('a 1 was given')
    # set slot to -score
    df.at[student, slot] = -(score)
    #put student into schedule
    name = df.at[student, 'name']
    schedule.add_student(slot, name)

    # add hours worked (2hrs)
    temp = 2 + df.at[student, 'hours']
    df.at[student,  'hours'] = temp

    # add to happiness
    temp = score + df.at[student, 'happiness']
    # temp = float(score + df.at[student, 'happiness']) / float (df.at[student, 'availability'])
    df.at[student, 'happiness'] = temp

def scheduler(df, score, slotdict, schedule):
    """creates a schedule"""
    # set limit on how low score can be
    while(score > 0):
        for slot in slotdict:
            slot_candidates = viable_cand(df, slot, score)
            curr_count = schedule.num_students(slot) # get current num of students on that slot
            cap = slotdict[slot]

            # reorder based on current happiness
            slot_candidates = equalize(df, slot_candidates)

            # cap num of students put into schedule
            if (len(slot_candidates) + curr_count > cap):
                slot_candidates = slot_candidates[: (cap - curr_count)]

            # put students into schedule
            for cand in slot_candidates:
                update_schedule(df, schedule, slot, cand, score)

        #decrement score
        score -= 1

    return(schedule)

def schedule_to_df(df, schedule):
    """given a schedule, this updates the starting dataframe of preferences"""
    for slot in schedule:
        for student in schedule[slot]:
            index = df.loc[df['name'] == student].index[0]
            swap.update_df(df, index, slot)

def get_order(df):
    """returns order of slots to fill in for creation of schedule"""
    ordered_slots = {}
    # smart ordering of slots
    for slot in slotdict.keys():
        #get each slots sum of preferences over all students
        ordered_slots[slot] = df[slot].sum(axis = 0)

    ordered_slotdict = {k: v for k, v in sorted(ordered_slots.items(), key=lambda item: item[1])}
    for slot in ordered_slotdict:
        ordered_slotdict[slot] = slotdict[slot]
    return(ordered_slots)
#-------------------------------------------------------------------------------
# Testing area
#-------------------------------------------------------------------------------
def main():
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('labTA-match-secret.json', scope)
    client = gspread.authorize(creds)

    # Find workbook and open the first sheet
    sheet = client.open('LabTA_test2').sheet1
    df_original = pd.DataFrame(sheet.get_all_records())
    json_before = df_original.to_json(orient='index')
    df_copy = df_original

    #get experience dict
    students = []
    for stud_num in range(NUM_STUDENTS):
        name = df.at[int(stud_num), "name"]
        students.append(name)

    exp_dict = past_exp_reader.get_exp('historical_data.csv', students)
    print(exp_dict)

    ordered_slotdict = get_order(df_original)
    print(ordered_slotdict)
    #shirley's schedule
    real_data = {"M_7" : ['Tajreen Ahmed', 'Urvashi Uberoy', 'Ze-Xin Koh', 'Kyle Johnson', 'Ariel Rakovitsky', 'Caroline di Vittorio', 'Khyati Agrawal', 'Annie Zhou'], "M_9" : ['Cathleen Kong', 'HJ Suh', 'Ze-Xin Koh', 'Akash Pattnaik', 'Ariel Rakovitsky', 'Caroline di Vittorio'],"Tu_7" : ['Uri Schwartz','Alan Ding','Urvashi Uberoy','Akash Pattnaik','Bobby Morck'], "Tu_9" : ['Justin Chang','Alan Ding','Caio Costa','Bobby Morck'],"W_7" : ['Michelle Woo','Avi Bendory','Kawin Tiyawattanaroj','Tajreen Ahmed'], "W_9" : ['Michelle Woo','Avi Bendory','Kawin Tiyawattanaroj','Khyati Agrawal'],"Th_7" : ['Charlie Smith','Niranjan Shankar','Caio Costa','Ryan Golant'], "Th_9" : ['Charlie Smith','Arjun Devraj','Somya Arora','Jason Xu'],"F_7" : ['Annie Zhou','Nathan Alam','Sahan Paliskara','Connie Miao'], "F_9" : ['Somya Arora','Nathan Alam','Sahan Paliskara','Ryan Golant'],"Sa_3" : ['Anu Vellore','Ibrahim Ali Hashmi','Aditya Kohli','Lily Zhang','Ezra Zinberg'], "Sa_4" : ['Jackson Deitelzweig','Donovan Coronado','Jason Xu','Uri Schwartz','Ally Dalman','Catherine Yu'],"Sa_5" : ['Anu Vellore','Ibrahim Ali Hashmi','Connie Miao','Lily Zhang','Ezra Zinberg'],"Su_5" : ['Nala Sharadjaya','Arjun Devraj','Donovan Coronado','Niranjan Shankar'],"Su_6" : ['Kyle Johnson','Sandun Bambarandage','Jackson Deitelzweig'],"Su_7" : ['Yashodhar Govil','Shirley Z.','Aniela Macek','Chuk Uzoegwu','Nala Sharadjaya','Aditya Kohli'],"Su_8" : ['Cathleen Kong','Sandun Bambarandage','HJ Suh','Ally Dalman'], "Su_9" : ['Yashodhar Govil','Shirley Z.','Aniela Macek','Chuk Uzoegwu','Justin Chang','Catherine Yu']}
    real_sched = Schedule(real_data)
    print("real schedule stats:")
    stats.exp_stats(df_copy, real_sched)
    real_hap = stats.sched_happiness(df_copy, real_sched)
    print('Total Happiness: ', real_hap[0])
    print()
    print('Availability to happiness correlation: ', real_hap[1])
    print()
    print('Variance of happiness: ', real_hap[2])
    print()
    print('Envy stats: ', real_hap[3])
    print()
    print('Incorrect stats: ', real_hap[4])
    print()

    # total_hap = []
    # corr = []
    # var = []
    # envy = []
    # incorrect = []
    # for i in range(20):
    #     sheet = client.open('LabTA_test2').sheet1
    #     df_original = pd.DataFrame(sheet.get_all_records())
    #     df_copy = df_original
    #     blank_sched = Schedule()
    #     schedule = scheduler(df_copy, score, slotdict, blank_sched)
    #     hap_stats = sched_happiness(df_copy, schedule)
    #
    #     total_hap.append(hap_stats[0]) # total happiness scores
    #
    #     corr.append(hap_stats[1]) # avail to happiness correlation
    #
    #     var.append(hap_stats[2]) # variance of happiness
    #
    #     envy.append(hap_stats[3])# envy score
    #
    #     incorrect.append(hap_stats[4]) # incorrect score
    #
    # print('Total Happiness: ')
    # print()
    # boxplot_stats(total_hap)
    # print()
    # print('Availability to happiness correlation: ')
    # print()
    # boxplot_stats(corr)
    # print()
    # print('Variance of happiness: ')
    # print()
    # boxplot_stats(var)
    # print()
    # print('Envy stats: ')
    # print()
    # boxplot_stats(envy)
    # print()
    # print('Incorrect stats: ')
    # print()
    # boxplot_stats(incorrect)


    sheet = client.open('LabTA_test2').sheet1
    df_original = pd.DataFrame(sheet.get_all_records())
    blank_sched = Schedule()
    schedule = scheduler(df_original, score, ordered_slotdict, blank_sched)

    unhap_studs = swap.get_unhappy(df_original)
    swap_dict = swap.check_swap(df_original, schedule, unhap_studs)
    swap.correct_swap(df_original, schedule, unhap_studs, swap_dict)
    print(df_original)
    #Evaluate happiness stats of schedule
    post_hap = stats.sched_happiness(df_original, schedule)
    print('Total Happiness: ', post_hap[0])
    print()
    print('Availability to happiness correlation: ', post_hap[1])
    print()
    print('Variance of happiness: ', post_hap[2])
    print()
    print('Envy stats: ', post_hap[3])
    print()
    print('Incorrect stats: ', post_hap[4])
    print()

    #Evaluate experience stats of schedule
    stats.exp_stats(df_original, schedule)
    response = True
    while (response == True):
        response = str(input("Want to swap a student out? (y/n): "))
        if response == "y":
            student = int(input("Enter student num to swap: "))
            slot = str(input("Enter their slot to swap them out of: "))
            swap.suggest(df_original, schedule, slot, student)
            response = True
        else:
            reponse = False
    # unhap_studs = get_unhappy(df_original)
    # check_swap(df_original, schedule, unhap_studs)
    # post_hap = sched_happiness(df_original, schedule)
    # print('Total Happiness: ', post_hap[0])
    # print()
    # print('Availability to happiness correlation: ', post_hap[1])
    # print()
    # print('Variance of happiness: ', post_hap[2])
    # print()
    # print('Envy stats: ', post_hap[3])
    # print()
    # print('Incorrect stats: ', post_hap[4])
    # print()

    # print("LabTA Schedule:")
    # schedule.print_sched()
    # print("my schedule stats:")
    # exp_stats(schedule)
    # sched_happiness(schedule)
    # json_after = df.to_json(orient='index')
