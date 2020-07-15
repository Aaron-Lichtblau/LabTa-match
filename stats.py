import math
# import json
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

def exp_stats(exp_dict, schedule):
    """prints stats on experience per slot"""
    slot_exp_dict = {} #dict of slots and their avg exp

    for slot in schedule:
        slot_exp = 0
        for student in schedule[slot]:
            student_exp = exp_dict[student]
            slot_exp += student_exp
        ave_exp = float(slot_exp) / float(len(schedule[slot]))
        slot_exp_dict[str(slot)] = ave_exp
    plt.figure(figsize=(10, 3))
    plt.bar(list(slot_exp_dict.keys()), slot_exp_dict.values(), color='b', align='edge', width=0.3)
    plt.title('Avg Experience of TAs per Slot')
    plt.ylabel('Past Semesters Worked')
    plt.xlabel('Slot')
    plt.show()

def boxplot_stats(data):
    data = np.array(data)
    print('median: ', np.median(data))
    upper_quartile = np.percentile(data, 75)
    print('upper quartile: ', upper_quartile)
    lower_quartile = np.percentile(data, 25)
    print('lower quartile: ', lower_quartile)
    iqr = upper_quartile - lower_quartile
    print('iqr: ', iqr)
    upper_whisker = data[data<=upper_quartile+1.5*iqr].max()
    print('upper whisker: ', upper_whisker)
    lower_whisker = data[data>=lower_quartile-1.5*iqr].min()
    print('lower whisker: ', lower_whisker)

def sched_happiness(df, schedule, prev_slot):
    """returns the total happiness score of the given schedule"""
    #sum happiness of every TA
    total_happiness = 0
    length = len(df.index)
    studhap = [0] * length #list of student happiness
    studslot = [[] for _ in range(length)] #list of lists of student's slots
    stud_1s = [] #list of students who got 1's
    wrong_type = [False] * length #get students who got wrong slot_type
    for slot in schedule:
        for student in schedule[slot]:
            index = df.loc[df['name'] == student].index[0]
            score = float(math.fabs(df.at[index, slot]))
            slot_type = int(df.at[index, 'slot_type'])
            if score == 1:
                stud_1s.append(df.at[index, 'name'])

            #check for matching slot_type and what they got in sched
            if slot_type == 4:
                wrong_type[index] = True
                for i_slot in prev_slot.keys():
                    if student in schedule[i_slot] and student in schedule[prev_slot[i_slot]]:
                        wrong_type[index] = False
                        break

            if slot_type == 2:
                if slot in prev_slot.keys():
                    if student in schedule[prev_slot[slot]]:
                        wrong_type[index] = True

            hap = float(score / (3 * float(df.at[index, 'cap'])))
            studslot[index].append(slot)
            # if hap == 1: print('gave out a 1')
            total_happiness += hap #update total happiness
            studhap[index] += hap #update each students' happiness

    avg_hap = float(total_happiness) * 100 / float(length)
    #create a df from student happiness
    df_hap = pd.DataFrame(studhap, columns =['happiness'])
    #get correlation of availability and Happiness
    corr = df['availability'].corr(df_hap['happiness'])
    # get variance of happiness
    var = df_hap.var()
    # get min and max happiness outlier students using z-value
    z = stats.zscore(df_hap)
    min_hap_df = df_hap[(z < (-3)).all(axis=1)]
    max_hap_df = df_hap[(z > 3).all(axis=1)]
    min_ids = min_hap_df.index
    max_ids = max_hap_df.index
    min_students = []
    for id in min_ids:
        min_students.append(df.at[id, 'name'])
    max_students = []
    for id in max_ids:
        max_students.append(df.at[id, 'name'])

    #get number of students without shift
    shiftless = []
    for id in range(len(studhap)):
        if float(studhap[id]) == 0.0:
            shiftless.append(df.at[id, 'name'])

    #get students who got wrong type from their ids
    wrong_type_studs = []
    for id in range(len(wrong_type)):
        if wrong_type[id] == True:
            wrong_type_studs.append(df.at[id, 'name'])

    hap_stats = [avg_hap, corr, var[0], min_students, max_students, stud_1s, shiftless, wrong_type_studs]
    return(hap_stats)
