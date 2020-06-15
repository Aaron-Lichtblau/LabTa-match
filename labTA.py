import gspread
import math
import json
import random
from schedule import Schedule
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
# import matplotlib.pyplot as plt

HOURS_LIMIT = 4 #limit of hours a TA can work
MAX_VALUE = 10
MIN_VALUE = 0
OVERLAPS = {'Sa_4': 'Sa_3', 'Sa_5':'Sa_4', 'Su_6':'Su_5', 'Su_7':'Su_6', 'Su_8':'Su_7', 'Su_9':'Su_8'} #dict of slots to check as keys, and overlapping slots as values
NUM_SLOTS = 16.0 #number of slots
NUM_STUDENTS = 45


def viable_cand(slot, score):
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

def swap_TA(slot, old_sched, old_TA, new_exp):
    """swap out a TA for a different TA with the desired experience, (not working yet) """
    #find students to swap check
    #min reduces happiness
    new_sched.exp_stats()
    print("the new schdule's total happiness score is: ", new_sched.sched_happiness())
    return(new_sched)

def equalize(slot_candidates):
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

def update_schedule(schedule, slot, student, score):
    """put students into schedule, update their slot to -1, update hours col, update happiness"""
    # set slot to -1
    df.at[student, slot] = -(score)
    #put student into schedule
    name = df.at[student, 'name']
    schedule.add_student(slot, name)

    # add hours worked (2hrs)
    temp = 2 + df.at[student, 'hours']
    df.at[student,  'hours'] = temp

    # add to happiness
    temp = score + df.at[student, 'happiness']
    df.at[student, 'happiness'] = temp


def scheduler(score, slotdict, schedule):
    """creates a schedule"""
    # set limit on how low score can be
    while(score > 0):
        for slot in slotdict:
            slot_candidates = viable_cand(slot, score)
            curr_count = schedule.num_students(slot) # get current num of students on that slot
            cap = slotdict[slot]

            # reorder based on current happiness
            slot_candidates = equalize(slot_candidates)

            # cap num of students put into schedule
            if (len(slot_candidates) + curr_count > cap):
                slot_candidates = slot_candidates[: (cap - curr_count)]

            # put students into schedule
            for cand in slot_candidates:
                update_schedule(schedule, slot, cand, score)

        #decrement score
        score -= 1

    return(schedule)

def exp_stats(schedule):
    """prints stats on experience per slot"""
    # get and print average exp of each slot
    lowest = MAX_VALUE
    highest = MIN_VALUE
    ave_total = MIN_VALUE
    for slot in schedule:
        slot_exp = 0
        for student in schedule[slot]:
            index = df.loc[df['name'] == student].index[0]
            student_exp = df.at[index, 'experience']
            slot_exp += student_exp
        ave_exp = float(slot_exp) / float(len(schedule[slot]))
        ave_total += float(ave_exp) / NUM_SLOTS
        if (ave_exp < lowest):
            lowest = ave_exp
        if (ave_exp > highest):
            highest = ave_exp
        print(slot, " has average experience: ", ave_exp)
    print("Summary of exp stats: ")
    # print lowest exp slot
    print("lowest average experience in a slot was: ", lowest)
    # print average slot exp
    print("average experience of each slot was: ", ave_total)
    # print highest exp slot
    print("highest average experience in a slot was: ", highest)

def sched_happiness(schedule):
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
            if hap == 1: print('gave out a 1')
            total_happiness += hap #update total happiness
            studhap[index] += hap #update each students' happiness
    #create a df from student happiness
    df_hap = pd.DataFrame(studhap, columns =['happiness'])
    print('student availability to happiness correlation coef: ', df['availability'].corr(df_hap['happiness']))
    print('total happiness: ', total_happiness)
    # get variance of happiness
    var = df_hap.var()
    print('variance of happiness is: ', var[0])

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

    print('envy score: ', envy)
    print('number incorrect: ', incorrect)
    # plt.hist(studhap, density=True, bins=30)  # `density=False` would make counts
    # plt.ylabel('Probability')
    # plt.xlabel('Happiness');
    # plt.show()


# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('labTA-match-secret.json', scope)
client = gspread.authorize(creds)

# Find workbook and open the first sheet
sheet = client.open('LabTA_test2').sheet1
df = pd.DataFrame(sheet.get_all_records())
json_before = df.to_json(orient='index')

# Testing area
score = 3
# slots and num of TA's desired
slotdict = {"M_7" : 8, "M_9" : 6,"Tu_7" : 5, "Tu_9" : 4,"W_7" : 4, "W_9" : 4,"Th_7" : 4, "Th_9" : 4,"F_7" : 4, "F_9" : 4,"Sa_3" : 5, "Sa_4" : 6,"Sa_5" : 5,"Su_5" : 4,"Su_6" : 3,"Su_7" : 6,"Su_8" : 4, "Su_9" : 6}
blank_sched = Schedule()
schedule = scheduler(score, slotdict, blank_sched)

#shirley's schedule
real_data = {"M_7" : ['Tajreen Ahmed', 'Urvashi Uberoy', 'Ze-Xin Koh', 'Kyle Johnson', 'Ariel Rakovitsky', 'Caroline di Vittorio', 'Khyati Agrawal', 'Annie Zhou'], "M_9" : ['Cathleen Kong', 'HJ Suh', 'Ze-Xin Koh', 'Akash Pattnaik', 'Ariel Rakovitsky', 'Caroline di Vittorio'],"Tu_7" : ['Uri Schwartz','Alan Ding','Urvashi Uberoy','Akash Pattnaik','Bobby Morck'], "Tu_9" : ['Justin Chang','Alan Ding','Caio Costa','Bobby Morck'],"W_7" : ['Michelle Woo','Avi Bendory','Kawin Tiyawattanaroj','Tajreen Ahmed'], "W_9" : ['Michelle Woo','Avi Bendory','Kawin Tiyawattanaroj','Khyati Agrawal'],"Th_7" : ['Charlie Smith','Niranjan Shankar','Caio Costa','Ryan Golant'], "Th_9" : ['Charlie Smith','Arjun Devraj','Somya Arora','Jason Xu'],"F_7" : ['Annie Zhou','Nathan Alam','Sahan Paliskara','Connie Miao'], "F_9" : ['Somya Arora','Nathan Alam','Sahan Paliskara','Ryan Golant'],"Sa_3" : ['Anu Vellore','Ibrahim Ali Hashmi','Aditya Kohli','Lily Zhang','Ezra Zinberg'], "Sa_4" : ['Jackson Deitelzweig','Donovan Coronado','Jason Xu','Uri Schwartz','Ally Dalman','Catherine Yu'],"Sa_5" : ['Anu Vellore','Ibrahim Ali Hashmi','Connie Miao','Lily Zhang','Ezra Zinberg'],"Su_5" : ['Nala Sharadjaya','Arjun Devraj','Donovan Coronado','Niranjan Shankar'],"Su_6" : ['Kyle Johnson','Sandun Bambarandage','Jackson Deitelzweig'],"Su_7" : ['Yashodhar Govil','Shirley Z.','Aniela Macek','Chuk Uzoegwu','Nala Sharadjaya','Aditya Kohli'],"Su_8" : ['Cathleen Kong','Sandun Bambarandage','HJ Suh','Ally Dalman'], "Su_9" : ['Yashodhar Govil','Shirley Z.','Aniela Macek','Chuk Uzoegwu','Justin Chang','Catherine Yu']}
real_sched = Schedule(real_data)
print("real schedule stats:")
exp_stats(real_sched)
sched_happiness(real_sched)
print(df)
# print("LabTA Schedule:")
# schedule.printSched()
print("my schedule stats:")
exp_stats(schedule)
sched_happiness(schedule)
json_after = df.to_json(orient='index')