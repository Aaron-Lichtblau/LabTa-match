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

# check for candidates who reported score on slot
def viableCand(slot, score):
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
    candRows = available.loc[(available[slot] >= score)].index
    candidates = list(candRows)
    return(candidates) # candidates are their row number, not name!

# swap out a TA for a different TA with the desired experience
# not working yet
def swapTA(slot, oldSched, oldTA, newExp):
    #find students to swap check
    #min reduces happiness
    newSched.expStats()
    print("the new schdule's total happiness score is: ", newSched.schedHappiness())
    return(newSched)

# equalize the order of candidates based on how happy they already are
def equalize(slotCandidates):
    #initial equalDict
    candDict = {}
    # randomize candidate list
    random.shuffle(slotCandidates)
    # order by their happiness score
    for cand in slotCandidates:
        candDict[cand] = df.at[cand, 'happiness']
    # order equalDict by values
    sortedCand = sorted(candDict.items(), key=lambda x: x[1])
    # create list of sorted candidates
    candidates = []
    for i in sortedCand:
        candidates.append(i[0])

    return(candidates)

# put students into schedule, update their slot to -1, update hours col, update happiness
def updateSchedule(schedule, slot, student, score):
    # set slot to -1
    df.at[student, slot] = -(score)
    #put student into schedule
    name = df.at[student, 'name']
    schedule.addStudent(slot, name)

    # add hours worked (2hrs)
    temp = 2 + df.at[student, 'hours']
    df.at[student,  'hours'] = temp

    # add to happiness
    temp = score + df.at[student, 'happiness']
    df.at[student, 'happiness'] = temp


def scheduler(score, slotdict, schedule):
    # set limit on how low score can be
    while(score > 0):
        for slot in slotdict:
            slotCandidates = viableCand(slot, score)
            currCount = schedule.numStudents(slot) # get current num of students on that slot
            cap = slotdict[slot]

            # reorder based on current happiness
            slotCandidates = equalize(slotCandidates)

            # cap num of students put into schedule
            if (len(slotCandidates) + currCount > cap):
                slotCandidates = slotCandidates[: (cap - currCount)]

            # put students into schedule
            for cand in slotCandidates:
                updateSchedule(schedule, slot, cand, score)

        #decrement score
        score -= 1

    return(schedule)

# prints stats on experience per slot
def expStats(schedule):
    # get and print average exp of each slot
    lowest = MAX_VALUE
    highest = MIN_VALUE
    aveTotal = MIN_VALUE
    for slot in schedule:
        slotExp = 0
        for student in schedule[slot]:
            index = df.loc[df['name'] == student].index[0]
            studentExp = df.at[index, 'experience']
            slotExp += studentExp
        aveExp = float(slotExp) / float(len(schedule[slot]))
        aveTotal += float(aveExp) / NUM_SLOTS
        if (aveExp < lowest):
            lowest = aveExp
        if (aveExp > highest):
            highest = aveExp
        print(slot, " has average experience: ", aveExp)
    print("Summary of exp stats: ")
    # print lowest exp slot
    print("lowest average experience in a slot was: ", lowest)
    # print average slot exp
    print("average experience of each slot was: ", aveTotal)
    # print highest exp slot
    print("highest average experience in a slot was: ", highest)

# returns the total happiness score of the given schedule
def schedHappiness(schedule):
    #sum happiness of every TA
    totalHappiness = 0
    length = len(df.index)
    studhap = [0] * length #list of student happiness
    studslot = [[] for _ in range(length)] #list of lists of student's slots

    for slot in schedule:
        for student in schedule[slot]:
            index = df.loc[df['name'] == student].index[0]
            hap = math.fabs(df.at[index, slot])
            studslot[index].append(slot)
            if hap == 1: print('gave out a 1')
            totalHappiness += hap #update total happiness
            studhap[index] += hap #update each students' happiness
    #create a df from student happiness
    dfHap = pd.DataFrame(studhap, columns =['happiness'])
    print('student availability to happiness correlation coef: ', df['availability'].corr(dfHap['happiness']))
    print('total happiness: ', totalHappiness)
    # get variance of happiness
    var = dfHap.var()
    print('variance of happiness is: ', var[0])

    envy = 0
    incorrect = 0
    # check for envy-free
    for iStudent in range(NUM_STUDENTS):
        #get student's own Happiness
        iHap = studhap[iStudent]
        #loop through other students slots
        for jStudent in range(NUM_STUDENTS):
            iValuei = studhap[iStudent]
            iValuej = 0
            jValuej = studhap[jStudent]
            #calc student's value of other student's slots
            for slot in studslot[jStudent]:
                iValuej += math.fabs(df.at[iStudent, slot])
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
jsonBefore = df.to_json(orient='index')

# Testing area
score = 3
# slots and num of TA's desired
slotdict = {"M_7" : 8, "M_9" : 6,"Tu_7" : 5, "Tu_9" : 4,"W_7" : 4, "W_9" : 4,"Th_7" : 4, "Th_9" : 4,"F_7" : 4, "F_9" : 4,"Sa_3" : 5, "Sa_4" : 6,"Sa_5" : 5,"Su_5" : 4,"Su_6" : 3,"Su_7" : 6,"Su_8" : 4, "Su_9" : 6}
blankSched = Schedule()
schedule = scheduler(score, slotdict, blankSched)

#shirley's schedule
realData = {"M_7" : ['Tajreen Ahmed', 'Urvashi Uberoy', 'Ze-Xin Koh', 'Kyle Johnson', 'Ariel Rakovitsky', 'Caroline di Vittorio', 'Khyati Agrawal', 'Annie Zhou'], "M_9" : ['Cathleen Kong', 'HJ Suh', 'Ze-Xin Koh', 'Akash Pattnaik', 'Ariel Rakovitsky', 'Caroline di Vittorio'],"Tu_7" : ['Uri Schwartz','Alan Ding','Urvashi Uberoy','Akash Pattnaik','Bobby Morck'], "Tu_9" : ['Justin Chang','Alan Ding','Caio Costa','Bobby Morck'],"W_7" : ['Michelle Woo','Avi Bendory','Kawin Tiyawattanaroj','Tajreen Ahmed'], "W_9" : ['Michelle Woo','Avi Bendory','Kawin Tiyawattanaroj','Khyati Agrawal'],"Th_7" : ['Charlie Smith','Niranjan Shankar','Caio Costa','Ryan Golant'], "Th_9" : ['Charlie Smith','Arjun Devraj','Somya Arora','Jason Xu'],"F_7" : ['Annie Zhou','Nathan Alam','Sahan Paliskara','Connie Miao'], "F_9" : ['Somya Arora','Nathan Alam','Sahan Paliskara','Ryan Golant'],"Sa_3" : ['Anu Vellore','Ibrahim Ali Hashmi','Aditya Kohli','Lily Zhang','Ezra Zinberg'], "Sa_4" : ['Jackson Deitelzweig','Donovan Coronado','Jason Xu','Uri Schwartz','Ally Dalman','Catherine Yu'],"Sa_5" : ['Anu Vellore','Ibrahim Ali Hashmi','Connie Miao','Lily Zhang','Ezra Zinberg'],"Su_5" : ['Nala Sharadjaya','Arjun Devraj','Donovan Coronado','Niranjan Shankar'],"Su_6" : ['Kyle Johnson','Sandun Bambarandage','Jackson Deitelzweig'],"Su_7" : ['Yashodhar Govil','Shirley Z.','Aniela Macek','Chuk Uzoegwu','Nala Sharadjaya','Aditya Kohli'],"Su_8" : ['Cathleen Kong','Sandun Bambarandage','HJ Suh','Ally Dalman'], "Su_9" : ['Yashodhar Govil','Shirley Z.','Aniela Macek','Chuk Uzoegwu','Justin Chang','Catherine Yu']}
realSched = Schedule(realData)
print("real schedule stats:")
expStats(realSched)
schedHappiness(realSched)
print(df)
# print("LabTA Schedule:")
# schedule.printSched()
print("my schedule stats:")
expStats(schedule)
schedHappiness(schedule)
jsonAfter = df.to_json(orient='index')
