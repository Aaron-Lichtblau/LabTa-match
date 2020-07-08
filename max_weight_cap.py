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
import output_creator
from oauth2client.service_account import ServiceAccountCredentials


STUD_SLOTS_WORKED_CAP = 2

NUM_STUDENTS = 45
OVERLAPS = {'Sa_4': ['Sa_3'], 'Sa_5':['Sa_4'], 'Su_6':['Su_5'], 'Su_7':['Su_6'], 'Su_8':['Su_7'], 'Su_9':['Su_8']} #dict of slots to check as keys, and overlapping slots as values
slotdict = {"M_7" : 8, "M_9" : 6,"Tu_7" : 5, "Tu_9" : 4,"W_7" : 4, "W_9" : 4,"Th_7" : 4, "Th_9" : 4,"F_7" : 4, "F_9" : 4,"Sa_3" : 5, "Sa_4" : 6,"Sa_5" : 5,"Su_5" : 4,"Su_6" : 3,"Su_7" : 6,"Su_8" : 4, "Su_9" : 6}
NUM_SLOTS = 0 #gets number of slots
for slot in slotdict:
    NUM_SLOTS += slotdict[slot]

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
    student_index = df.loc[df['name'] == student].index[0]
    weight = 0
    tier = NUM_SLOTS * 10

    # is pref a 2 or 3?
    pref = df.at[student_index, slot_node]
    if pref == 2 or pref == 3:
        weight += (tier)**4
    # is it their first shift?
    if int(j) == 0:
        weight += (tier)**3
    # weight based on preference
    weight += (pref *  (tier**2))

    #availability/cap/jth shift/student score tier
    avail = (float(df.at[student_index, "availability"]) / float(3 * NUM_SLOTS) * 2.5)
    cap = (float(df.at[student_index, "cap"]) / float(10) * 2.5)
    jth_shift = float(10 - int(j)) * 2.5
    stud_score = 2.5 #to be changed when students get performance scores

    weight += (avail + cap + jth_shift + stud_score) * tier
    weight = int(weight * 100) #make sure there are no decimals
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

def create_graph(df):
    ''''returns student nodes, slot nodes and dict of weights'''
    student_nodes = []
    students = list(df['name'])

    for student in students:
        index = df.loc[df['name'] == student].index[0]
        shift_cap = int(df.at[index, 'cap'])
        for shift in range(shift_cap):
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


    for v in to_nodes:
       #A) For all k, \sum_{i,j} x(i,j,k) \leq c_k (for each slot, have at most c_k students in that slot).
       prob += lpSum([choices[u][v] for u in from_nodes]) <= slotdict[v], ""
    for u in from_nodes:
        #B) For all i, j, \sum_k x(i,j,k) \leq 1 (a student can only use their jth shift once)
        prob += lpSum([choices[u][v] for v in to_nodes]) <= 1, ""

    # Constraint set ensuring that the total from/to each node
    # is less than its capacity
    for u in from_nodes:
        #make list of student nodes
        name = u.split('_')[:1][0]
        j_nodes = get_student_nodes(name, from_nodes)
        for v in to_nodes:
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
            length = len(stud_slot)
            slot = stud_slot[length - 2] + "_" + stud_slot[length - 1]
            stud = ''
            for i in range(int(length - 3)):
                stud += (stud_slot[i] + " ")
            stud = stud[:-1]

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

    #create graph nodes and weight edges
    graph_data = create_graph(df)
    student_nodes = graph_data[0]
    slot_nodes = graph_data[1]
    wt = graph_data[2]

    #solve the problem and get the ordered schedule
    p = solve_wbm(student_nodes, slot_nodes, wt)
    unordered_sched_dict = get_solution(p)
    max_weight_sched = order_sched(df, unordered_sched_dict)
    Schedule.print_sched(max_weight_sched)
    labTA.schedule_to_df(df, max_weight_sched)

    for slot in max_weight_sched:
        if len(max_weight_sched[slot]) < slotdict[slot]:
            diff = slotdict[slot] - len(max_weight_sched[slot])
            print(slot, " not full, needs: ", diff, " ta's")

    # #make list of overlap students and resolve them
    # overlaps = labTA.get_overlaps(df, max_weight_sched)
    # print(overlaps)
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

    #get experience dict
    exp_dict = {}
    students = list(df['name'])
    for index in range(NUM_STUDENTS):
        exp_dict[str(df.at[index, 'name'])] = int(df.at[index, 'experience'])

    #Evaluate experience stats of schedule
    stats.exp_stats(exp_dict, max_weight_sched)
    response = True
    while (response == True):
        response = str(input("Want to swap a student out? (y/n): "))
        if response == "y":
            student = str(input("Enter student to swap: "))
            slot = str(input("Enter their slot to swap them out of: "))

            #check student and slot are good inputs
            if student not in list(df['name']):
                print('student given is not in schedule')
                exit(0)
            if slot not in slotdict.keys():
                print('slot given is not in schedule')
                exit(0)

            swap_cands_dict = swap.max_weight_suggest(max_weight_sched, p, wt, slot, student)
            accept_swap  = False
            while (accept_swap == False):
                for cand in swap_cands_dict.keys():
                    #print out top candidate edge
                    print(cand)
                    #ask to accept or not
                    response = str(input("Want to accept proposed swap? (y/n): "))
                    if response == 'y':
                        accept_swap = True

                        stud_slot = str(cand).split('_')
                        length = len(stud_slot)

                        #get the new ta
                        new_ta = ''
                        for i in range(int(length - 3)):
                            new_ta += (stud_slot[i] + " ")
                        new_ta = new_ta[:-1]

                        #get the new slot
                        new_slot = stud_slot[length - 2] + "_" + stud_slot[length - 1]

                        swap.swap_TA(df, max_weight_sched, student, slot, new_ta, new_slot)
                        break

        else:
            response = False
    #make output schedule in sheet
    # output_creator.make_sheet(max_weight_sched)
if __name__ == "__main__":
    main()
