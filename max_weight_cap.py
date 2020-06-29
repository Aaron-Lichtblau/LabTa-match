from pulp import *
import matplotlib.pyplot as plt
import gspread
import pandas as pd
from schedule import Schedule
import stats
import labTA
import swap
import re
import json
import past_exp_reader
from oauth2client.service_account import ServiceAccountCredentials


STUD_SLOTS_WORKED_CAP = 2
NUM_STUDENTS = 45
OVERLAPS = {'Sa_4': 'Sa_3', 'Sa_5':'Sa_4', 'Su_6':'Su_5', 'Su_7':'Su_6', 'Su_8':'Su_7', 'Su_9':'Su_8'} #dict of slots to check as keys, and overlapping slots as values
slotdict = {"M_7" : 8, "M_9" : 6,"Tu_7" : 5, "Tu_9" : 4,"W_7" : 4, "W_9" : 4,"Th_7" : 4, "Th_9" : 4,"F_7" : 4, "F_9" : 4,"Sa_3" : 5, "Sa_4" : 6,"Sa_5" : 5,"Su_5" : 4,"Su_6" : 3,"Su_7" : 6,"Su_8" : 4, "Su_9" : 6}

def get_overlaps(df, schedule):
    '''returns a dict of {overlapping students: their time slot}'''
    overlap_dict = {}
    #find students that are working in both key and value of overlaps
    for slot in OVERLAPS.keys():
        for student in range(NUM_STUDENTS):
            name = df.at[student, "name"]
            if (name in schedule[OVERLAPS[slot]]) and (name in schedule[slot]):
                overlap_dict[name] = slot
    return(overlap_dict)

def resolve_overlaps(df, max_weight_sched, overlaps):
    '''resolves all overlaps in schedule'''
    infinite_loop = 0
    while(len(overlaps.keys()) > 0):
        infinite_loop += 1
        student = next(iter(overlaps))
        old_slot = overlaps[student]
        old_ta = df.loc[df['name'] == student].index[0]
        #get top suggestion
        if infinite_loop < 20:
            swap_pair = swap.suggest(df, max_weight_sched, old_slot, old_ta)[0]
        else:
            swap_pair = swap.suggest(df, max_weight_sched, old_slot, old_ta)[1]
            infinite_loop = 0
        new_ta = swap_pair[0]
        new_slot = swap_pair[1]
        #swap student with top suggestion
        swap.swap_TA(df, max_weight_sched, old_ta, old_slot, new_ta, new_slot)
        overlaps = get_overlaps(df, max_weight_sched)

#rank weight edges based on 1. preference 2. availability 3. happiness
def weight_edge(df, student, slot):
    """returns the student-slot edge weight"""
    weight = 0
    pref_coef = 100
    #get their preference score * 100
    pref_score = (df.at[student, slot] * pref_coef)
    #add their availability score
    avail_score = df.at[student, "availability"]
    weight = pref_score + avail_score
    return (weight)

def order_sched(df, unordered_sched_dict):
    '''takes unordered sched dict and returns an ordered Schedule object'''
    ordered_sched = {k: unordered_sched_dict[k] for k in slotdict.keys()}
    max_weight_dict = {}
    for slot in ordered_sched:
        max_weight_dict[slot] = []
        for student in ordered_sched[slot]:
            name = df.at[int(student), "name"]
            max_weight_dict[slot].append(name)

    max_weight_sched = Schedule(max_weight_dict)
    return(max_weight_sched)

def create_graph(df):
    ''''returns student nodes, slot nodes and dict of weights'''
    student_nodes = []
    for student in range(NUM_STUDENTS):
        student_nodes.append(student)

    slot_nodes = []
    for slot in slotdict.keys():
            slot_nodes.append(slot)

    student_cap = {}
    for student in student_nodes:
        student_cap[student] = STUD_SLOTS_WORKED_CAP

    slot_cap = {}
    for slot in slot_nodes:
        slot_cap[slot] = slotdict[slot]

    weights = {}
    for student in student_nodes:
        for slot in slot_nodes:
            weights[(student, slot)] = weight_edge(df, student, slot)

    wt = create_wt_doubledict(student_nodes, slot_nodes, weights)
    return(student_nodes, slot_nodes, wt, student_cap, slot_cap)

#just a convenience function to generate a dict of dicts
def create_wt_doubledict(from_nodes, to_nodes, weights):
    wt = {}
    for u in from_nodes:
        wt[u] = {}
        for v in to_nodes:
            wt[u][v] = 0

    for k,val in weights.items():
        u,v = k[0], k[1]
        wt[u][v] = val
    return(wt)

def solve_wbm(from_nodes, to_nodes, wt, student_cap, slot_cap):
    ''' A wrapper function that uses pulp to formulate and solve a WBM'''

    prob = LpProblem("WBM Problem", LpMaximize)

    # Create The Decision variables
    choices = LpVariable.dicts("e",(from_nodes, to_nodes), 0, 1, LpInteger)

    # Add the objective function
    prob += lpSum([wt[u][v] * choices[u][v]
                   for u in from_nodes
                   for v in to_nodes]), "Total weights of selected edges"


    # Constraint set ensuring that the total from/to each node
    # is less than its capacity
    for u in from_nodes:
        for v in to_nodes:
            prob += lpSum([choices[u][v] for v in to_nodes]) <= student_cap[u], ""
            prob += lpSum([choices[u][v] for u in from_nodes]) <= slot_cap[v], ""


    # The problem data is written to an .lp file
    prob.writeLP("WBM.lp")

    # The problem is solved using PuLP's choice of Solver
    prob.solve()

 # The status of the solution is printed to the screen
    print( "Status:", LpStatus[prob.status])
    return(prob)


def get_solution(prob):
    # Each of the variables is printed with it's resolved optimum value
    sched_dict = {}
    for v in prob.variables():
        if v.varValue > 1e-3:
            stud_slot = str(v).split('_')[1:]
            slot = stud_slot[1] + "_" + stud_slot[2]
            stud = stud_slot[0]
            if slot in sched_dict:
                sched_dict[slot].append(stud)
            else:
                sched_dict[slot] = [stud]
            # print(f'{v.name} = {v.varValue}')
    # print(f"Sum of wts of selected edges = {round(value(prob.objective), 4)}")
    return(sched_dict)


def get_selected_edges(prob):

    selected_from = [v.name.split("_")[1] for v in prob.variables() if v.value() > 1e-3]
    selected_to   = [v.name.split("_")[2] for v in prob.variables() if v.value() > 1e-3]

    selected_edges = []
    for su, sv in list(zip(selected_from, selected_to)):
        selected_edges.append((su, sv))
    return(selected_edges)


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
    df = pd.DataFrame(sheet.get_all_records())

    #create graph nodes and weight edges
    graph_data = create_graph()
    student_nodes = graph_data[0]
    slot_nodes = graph_data[1]
    wt = graph_data[2]

    #solve the problem and get the ordered schedule
    p = solve_wbm(student_nodes, slot_nodes, wt)
    unordered_sched_dict = get_solution(p)
    max_weight_sched = order_sched(df, unordered_sched_dict)
    Schedule.print_sched(max_weight_sched)
    labTA.schedule_to_df(df, max_weight_sched)

    #make list of overlap students and resolve them
    overlaps = get_overlaps(max_weight_sched)
    resolve_overlaps(overlaps)

    print(df)
    #Evaluate happiness stats of schedule
    post_hap = stats.sched_happiness(df, max_weight_sched)
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

    students = []
    for stud_num in range(NUM_STUDENTS):
        name = df.at[int(stud_num), "name"]
        students.append(name)

    exp_dict = past_exp_reader.get_exp('historical_data.csv', students)
    print(exp_dict)

if __name__ == "__main__":
    main()
