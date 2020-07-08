import math
import json
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

NUM_SLOTS = 16.0 #number of slots
NUM_STUDENTS = 45
MAX_HAP = 258.0

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

def sched_happiness(df, schedule):
    """returns the total happiness score of the given schedule"""
    #sum happiness of every TA
    total_happiness = 0
    length = len(df.index)
    studhap = [0] * length #list of student happiness
    studslot = [[] for _ in range(length)] #list of lists of student's slots

    for slot in schedule:
        for student in schedule[slot]:
            index = df.loc[df['name'] == student].index[0]
            hap = math.fabs(df.at[index, slot])
            studslot[index].append(slot)
            # if hap == 1: print('gave out a 1')
            total_happiness += hap #update total happiness
            studhap[index] += hap #update each students' happiness

    avg_hap = float(total_happiness) / float(NUM_STUDENTS)
    #normalize total happiness score
    total_happiness = float(total_happiness) / MAX_HAP
    #create a df from student happiness
    df_hap = pd.DataFrame(studhap, columns =['happiness'])
    # print('student availability to happiness correlation coef: ', df['availability'].corr(df_hap['happiness']))
    # print('total happiness: ', total_happiness)
    # get variance of happiness
    var = df_hap.var()
    # print('variance of happiness is: ', var[0])

    envy = 0
    incorrect = 0
    # check for envy-free
    for i_student in range(NUM_STUDENTS):
        #get student's own Happiness
        i_hap = studhap[i_student]
        #loop through other students slots
        for j_student in range(NUM_STUDENTS):
            iValuei = studhap[i_student]
            iValuej = 0
            jValuej = studhap[j_student]
            #calc student's value of other student's slots
            for slot in studslot[j_student]:
                iValuej += math.fabs(df.at[i_student, slot])
            # if they value another greater, print out i envies j
            if (iValuei < iValuej):
                # print("student ", iStudent, " envies ", jStudent)
                envy += 1
            # see if a student values another's slots more than the other student
            if (iValuej > jValuej):
                # print("student ", iStudent, " values ", jStudent,"'s slots more than ", jStudent)
                incorrect += 1

    # print('envy score: ', envy)
    # print('number incorrect: ', incorrect)
    corr = df['availability'].corr(df_hap['happiness'])
    hap_stats = [total_happiness, avg_hap, corr, var[0], envy, incorrect]
    return(hap_stats)
    # plt.hist(studhap, density=True, bins=30)  # `density=False` would make counts
    # plt.ylabel('Probability')
    # plt.xlabel('Happiness');
    # plt.show()
