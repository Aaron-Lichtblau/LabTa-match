from schedule import Schedule
import pandas as pd



OVERLAPS = {'Sa_4': 'Sa_3', 'Sa_5':'Sa_4', 'Su_6':'Su_5', 'Su_7':'Su_6', 'Su_8':'Su_7', 'Su_9':'Su_8'} #dict of slots to check as keys, and overlapping slots as values
SLOTS = ["M_7", "M_9","Tu_7", "Tu_9","W_7", "W_9","Th_7", "Th_9","F_7", "F_9","Sa_3", "Sa_4","Sa_5","Su_5","Su_6","Su_7","Su_8", "Su_9"]
NUM_SLOTS = 16.0 #number of slots
NUM_STUDENTS = 45

def suggest(df, schedule, slot, student):
    """suggests a swap given student in a slot with too little or too much experience"""

    #get experience of slot and make student exp dict
    stud_exp_dict = {}
    slot_exp = 0
    for stud in schedule[slot]:
        #get students index
        stud_id = df[df['name'] == stud].index[0]
        #get experience of student
        stud_exp = df.at[stud_id, 'experience']
        #put in dict and update slot exp
        stud_exp_dict[stud_id] = stud_exp
        slot_exp += stud_exp
    avg_exp = float(slot_exp) / float(len(schedule[slot]))

    swap_stud = {}
    swap_stud[student] = slot

    #find candidates for swapping
    swap_cands_dict = check_swap(df, schedule, swap_stud)
    print("An ordered list of possible swaps denoted as [student, slot] for : [", student, ", ", slot, "] is: ", swap_cands_dict[student])


        #minimize loss of happiness subject to getting exp right
        #make sure swapped slot has good exp
    #print out the swap that was made

def check_swap(df, old_sched, unhap_studs):
    """find possible swaps for different TAs to resolve incorrectness """
    swap_dict = {}
    for student in unhap_studs.keys():
        bad_slot = unhap_studs[student]
        swap_dict[student] = []

        # get other students who had unused 3's and 2's on this slot
        swap_candidates = list(df.loc[df[bad_slot] == 3].index)
        swap2_candidates = list(df.loc[df[bad_slot] == 2].index)
        swap_candidates.extend(swap2_candidates)


        # get the student's unused 3's and 2's slots
        unused_slots = []
        unused2_slots = []
        for slot in SLOTS:
            if df.at[student, slot] == 3:
                unused_slots.append(slot)
            if df.at[student, slot] == 2:
                unused2_slots.append(slot)
        unused_slots.extend(unused2_slots)

        # for each swap candidate get their used slots of 3's and 2's
        for cand in swap_candidates:
            swap_slots = []
            swap2_slots = []
            for slot in SLOTS:
                if df.at[cand, slot] == -3:
                    swap_slots.append(slot)
                if df.at[cand, slot] == -2:
                    swap2_slots.append(slot)
            swap_slots.extend(swap2_slots)

            # compare lists of slots if theres a match, add to list of students to swap
            for i_slot in unused_slots:
                for j_slot in swap_slots:
                    if i_slot == j_slot:
                        swap_dict[student].append([cand, i_slot])
    return(swap_dict)

def correct_swap(df, schedule, unhap_studs, swap_dict):
    """use the swap dict from check_swap to do the swap"""
    used = []
    # swap them and update schedule/df
    for student in swap_dict:
        bad_slot = unhap_studs[student]
        #make sure slot hasn't been swapped for yet
        i = 0
        swapped = False
        while(swapped == False):
            new_ta = swap_dict[student][i][0]
            new_slot = swap_dict[student][i][1]
            if [new_ta, new_slot] not in used:
                swap_TA(df, schedule, student, bad_slot, new_ta, new_slot)
                used.append([new_ta, new_slot])
                swapped = True
            else:
                i += 1

def get_unhappy(df):
    unhap_studs = {}
    for student in range(NUM_STUDENTS):
        for slot in SLOTS:
            if df.at[student, slot] == -1:
                unhap_studs[student] = slot
    return(unhap_studs)

def swap_TA(df, schedule, old_ta, old_slot, new_ta, new_slot):
    """swap ta's in the schedule at the given slots and update the dataframe"""
    old_name = df.at[old_ta, 'name']
    new_name = df.at[new_ta, 'name']
    schedule.remove_student(old_slot, old_name)
    schedule.remove_student(new_slot, new_name)
    schedule.add_student(old_slot, new_name)
    schedule.add_student(new_slot, old_name)
    #update df
    update_df(df, old_ta, old_slot)
    update_df(df, old_ta, new_slot)
    update_df(df, new_ta, new_slot)
    update_df(df, new_ta, old_slot)

def update_df(df, student, slot):
    #update preference table
    score = df.at[student, slot]

    df.at[student, slot] = -(score)
    #update hours worked and happiness
    temp_work = df.at[student, 'hours']
    temp_hap = df.at[student, 'happiness']
    if df.at[student, slot] < 0: #shows they added slot
        df.at[student, 'hours'] = (temp_work + 2)
        df.at[student, 'happiness'] = (temp_hap + score)
    else:
        df.at[student, 'hours'] = (temp_work - 2)
        df.at[student, 'happiness'] = (temp_hap + score)
