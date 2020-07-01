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
import input_creator
from oauth2client.service_account import ServiceAccountCredentials


STUD_SLOTS_WORKED_CAP = 2
NUM_STUDENTS = 45
OVERLAPS = {'Sa_4': ['Sa_3'], 'Sa_5':['Sa_4'], 'Su_6':['Su_5'], 'Su_7':['Su_6'], 'Su_8':['Su_7'], 'Su_9':['Su_8']} #dict of slots to check as keys, and overlapping slots as values
slotdict = {"M_7" : 8, "M_9" : 6,"Tu_7" : 5, "Tu_9" : 4,"W_7" : 4, "W_9" : 4,"Th_7" : 4, "Th_9" : 4,"F_7" : 4, "F_9" : 4,"Sa_3" : 5, "Sa_4" : 6,"Sa_5" : 5,"Su_5" : 4,"Su_6" : 3,"Su_7" : 6,"Su_8" : 4, "Su_9" : 6}

def get_student_nodes(name, student_nodes):
    '''gets a student's nodes given their name'''
    name_nodes = []
    for node in student_nodes:
        if (node.split("_")[:1][0] == name):
            name_nodes.append(node)
    return name_nodes

    # weighing:
    #     tiered based on j (so that everyone gets a shift before someone gets multiple)
    #     tiered based on preferences
    #     ordered by availability given (so that it is incentive compatible to give all your preferences)
#rank weight edges based on 1. preference 2. availability 3. happiness
def weight_edge(df, student_node, slot_node):
    """returns the student-slot edge weight"""

    student = student_node.split("_")[0]
    j = student_node.split("_")[1]

    pref_coef = 100
    #get their preference score * 100
    student_index = df.loc[df['name'] == student].index[0]
    pref_score = (df.at[student_index, slot_node] * pref_coef)
    #add their availability score
    avail_score = df.at[student_index, "availability"]
    weight = pref_score + avail_score
    return (weight)

def order_sched(df, unordered_sched_dict):
    '''takes unordered sched dict and returns an ordered Schedule object'''
    ordered_sched = {k: unordered_sched_dict[k] for k in slotdict.keys()}
    max_weight_dict = {}
    for slot in ordered_sched:
        max_weight_dict[slot] = []
        for student in ordered_sched[slot]:
            name = student.split("_")[0]
            max_weight_dict[slot].append(name)

    max_weight_sched = Schedule(max_weight_dict)
    return(max_weight_sched)

def create_graph(df, shift_cap):
    ''''returns student nodes, slot nodes and dict of weights'''
    student_nodes = []
    students = list(df['name'])
    for student in students:
        for shift in range(shift_cap[student]):
            student_nodes.append(str(student) + "_" + str(shift))

    slot_nodes = []
    for slot in slotdict.keys():
            slot_nodes.append(slot)

    weights = {}
    for student in student_nodes:
        for slot in slot_nodes:
            weights[(student, slot)] = weight_edge(df, student, slot)

    wt = create_wt_doubledict(student_nodes, slot_nodes, weights)
    return(student_nodes, slot_nodes, wt)

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

def solve_wbm(from_nodes, to_nodes, wt):
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
        #make list of student nodes
        name = u.split('_')[:1][0]
        j_nodes = get_student_nodes(name, from_nodes)
        for v in to_nodes:
            #A) For all k, \sum_{i,j} x(i,j,k) \leq c_k (for each slot, have at most c_k students in that slot).
            prob += lpSum([choices[u][v] for u in from_nodes]) <= slotdict[v], ""
            #B) For all i, j, \sum_k x(i,j,k) \leq 1 (a student can only use their jth shift once)
            prob += lpSum([choices[u][v] for v in to_nodes]) <= 1, ""
            # C) For all i, k, \sum_j x(i,j,k) \leq 1 (a student can be in a slot only once)
            prob += lpSum([choices[u][v] for u in j_nodes]) <= 1, ""
            # D) For all i, and all k, k' which are overlapping, \sum_j x(i,j,k) + x(i,j,k') \leq 1 (student cannot take overlapping shifts).
            if v in OVERLAPS.keys():
                overlap_nodes = OVERLAPS[v] #get overlap nodes as list
                for k in overlap_nodes:
                    prob += lpSum([choices[u][v] for u in j_nodes] + [choices[u][k] for u in j_nodes]) <= 1, ""


# E) For all i,j,k, x(i,j,k) \in {0,1} (Integer Program)
# E') For all i,j,k, x(i,j,k) \in [0,1] (Linear Program)

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
            slot = stud_slot[3] + "_" + stud_slot[4]
            stud = stud_slot[0] + " " + stud_slot[1]
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
    df = input_creator.get_df()

    stud_shift_cap = {} #dict of students (keys) and max number of shifts they can work (values)
    for student in list(df['name']):
        stud_shift_cap[student] = STUD_SLOTS_WORKED_CAP #for now all students work max of 2 shifts
    exp_dict = input_creator.get_exp('historical_data.csv', stud_shift_cap.keys()) #dict of students (keys) and number of semesters experience (values)

    #create graph nodes and weight edges
    graph_data = create_graph(df, stud_shift_cap)
    student_nodes = graph_data[0]
    slot_nodes = graph_data[1]
    wt = graph_data[2]

    #solve the problem and get the ordered schedule
    p = solve_wbm(student_nodes, slot_nodes, wt)
    unordered_sched_dict = get_solution(p)
    max_weight_sched = order_sched(df, unordered_sched_dict)
    # Schedule.print_sched(max_weight_sched)
    labTA.schedule_to_df(df, max_weight_sched)

    for slot in max_weight_sched:
        if len(max_weight_sched[slot]) < slotdict[slot]:
            diff = slotdict[slot] - len(max_weight_sched[slot])
            print(slot, " not full, needs: ", diff, " ta's")

    # #make list of overlap students and resolve them
    overlaps = labTA.get_overlaps(df, max_weight_sched)
    print(overlaps)
    # resolve_overlaps(df, max_weight_sched, overlaps)

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

if __name__ == "__main__":
    main()
