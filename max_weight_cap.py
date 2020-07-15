from pulp import *
import matplotlib.pyplot as plt
import gspread
import pandas as pd
from schedule import Schedule
import stats
import swap
# import re
# import json
import input_creator
# import output_creator
from oauth2client.service_account import ServiceAccountCredentials

OVERLAPS = {'Sa_4': ['Sa_3'], 'Sa_5':['Sa_4'], 'Su_6':['Su_5'], 'Su_7':['Su_6'], 'Su_8':['Su_7'], 'Su_9':['Su_8']} #dict of slots to check as keys, and overlapping slots as values
PREV_SLOT = {'M_9': 'M_7', 'Tu_9': 'Tu_7', 'W_9': 'W_7', 'Th_9': 'Th_7', 'F_9': 'F_7', 'Sa_5': 'Sa_3', 'Su_7': 'Su_5', 'Su_8': 'Su_6', 'Su_9': 'Su_7'} #dict of slots and their prev slots
slotdict = {"M_7" : 8, "M_9" : 6,"Tu_7" : 5, "Tu_9" : 4,"W_7" : 4, "W_9" : 4,"Th_7" : 4, "Th_9" : 4,"F_7" : 4, "F_9" : 4,"Sa_3" : 5, "Sa_4" : 6,"Sa_5" : 5,"Su_5" : 4,"Su_6" : 3,"Su_7" : 6,"Su_8" : 4, "Su_9" : 6}
NUM_SLOTS = 0 #gets number of slots
for slot in slotdict:
    NUM_SLOTS += slotdict[slot]

def schedule_to_df(df, schedule):
    """given a schedule, this updates the starting dataframe of preferences"""
    for slot in schedule:
        if (len(slot) == 0):
            print('empty slot in schedule ERROR!')
        for student in schedule[slot]:
            swap.update_df(df, student, slot)

def get_student_nodes(name, student_nodes):
    '''gets a student's nodes given their name'''
    name_nodes = []
    for node in student_nodes:
        if (node.split("_")[:1][0] == name):
            name_nodes.append(node)
    return name_nodes

def get_slot(slot_node):
    slot = slot_node[:-2]
    return(slot)

def get_hours(slot_node):
    slot_type = slot_node[-1]
    if int(slot_type) == 1:
        return(4)
    else:
        return(2)

def get_tier_emph(weight_dict):
    tier_dict = {}
    emph_dict = {}
    for weight in weight_dict:
        if int(weight_dict[weight]) > 5:
            tier_dict[weight] = weight_dict[weight]
            emph_dict[weight] = 0
        else:
            tier_dict[weight] = 0
            emph_dict[weight] = weight_dict[weight]
    return [tier_dict, emph_dict]

def weight_edge(df, student_node, slot_node, weight_dict):
    #returns the student-slot edge weight

    student = student_node.split("_")[0]
    slot = get_slot(slot_node)
    slot_hours = get_hours(slot_node)
    j = student_node.split("_")[1]
    student_index = df.loc[df['name'] == student].index[0]
    weight = 0

    tier_dict = get_tier_emph(weight_dict)[0]
    emph_dict = get_tier_emph(weight_dict)[1]

    #collect tier information
    slot_type_tier = 100 ** int(tier_dict['slot_type'])
    no_1_tier = 100 ** int(tier_dict['no_1'])
    guarantee_shift_tier = 100 ** int(tier_dict['guarantee_shift'])
    avail_tier = 100 ** int(tier_dict['avail'])
    shift_cap_tier = 100 ** int(tier_dict['shift_cap'])
    equality_tier = 100 ** int(tier_dict['equality'])
    pref_tier = 1000000

    #collect emphasis information
    slot_type_emph = 10 * int(emph_dict['slot_type'])
    no_1_emph = 10 * int(emph_dict['no_1'])
    guarantee_shift_emph = 10 * int(emph_dict['guarantee_shift'])
    avail_emph = 10 * int(emph_dict['avail'])
    shift_cap_emph = 10 * int(emph_dict['shift_cap'])
    equality_emph = 10 * int(emph_dict['equality'])

    # wants a 2hr vs 4hr?
    hour_pref = df.at[student_index, "slot_type"]
    if int(slot_hours) == int(hour_pref):
        weight += slot_type_tier
        weight += slot_type_emph

    # is pref a 2 or 3?
    pref = abs(df.at[student_index, slot])
    if pref == 2 or pref == 3:
        weight += no_1_tier
        weight += no_1_emph

    # is it their first shift?
    if int(j) == 0:
        weight += guarantee_shift_tier
        weight += guarantee_shift_emph

    # rewards availability
    avail = 1 + float(df.at[student_index, "availability"]) / float(3 * NUM_SLOTS) #num in range [1, 2]
    weight += (avail * avail_tier)
    weight += (avail * avail_emph)

    #reward shift num caps
    shift_cap = df.at[student_index, "cap"] #num in range [2, 10]
    weight += (shift_cap * shift_cap_tier)
    weight += (shift_cap * shift_cap_emph)

    # equality of shifts
    jth_shift = float(11 - int(j)) #num in range [1, 11]
    weight += (jth_shift * equality_tier)
    weight += (jth_shift * equality_emph)

    # weight based on preference
    weight += (pref *  pref_tier)

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

def create_graph(df, weight_dict):
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
        slot_0 = str(slot) + "_0"
        slot_nodes.append(slot_0)
        #check if slot is potential 4 hr
        if is_4hr(slot):
            slot_1 = str(slot) + "_1"
            slot_nodes.append(slot_1)

    weights = {}
    for student in student_nodes:
        for slot in slot_nodes:
            weights[(student, slot)] = weight_edge(df, student, slot, weight_dict)

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

# For all s, j, \sum_k x(s,k,j,1) + x(s,k,j,0) \leq 1. Guarantees that each slot is used at most once.
    for u in from_nodes:
        for v in get_slot_type(to_nodes, 0):
            x = get_alt_slot(v) #sees if slot is potential 4hr (has alternate node)
            if x != None:
                prob += lpSum([choices[u][v] + choices[u][x]]) <= 1, ""
            else:
                prob += lpSum([choices[u][v]]) <= 1, ""

# For all s,k, \sum_j x(s,k,j,1) + x(s,k,j,0)+ x(s,k-1,j,1) + x(s,k-1,j,0) \leq 1. Guarantees that each slot is used at most once, and also no overlapping slots.
    for u in from_nodes:
        name = u.split('_')[:1][0]
        j_nodes = get_student_nodes(name, from_nodes)
        for v in get_slot_type(to_nodes, 0):
            x = get_alt_slot(v) #sees if slot is potential 4hr (has alternate node)
            k = get_slot(v)
            if x != None and k in OVERLAPS.keys():
                overlap_slots = OVERLAPS[k] #get overlap nodes as list
                overlap_nodes = []
                for slot in overlap_slots:
                    node_0 = str(slot)+"_0"
                    overlap_nodes.append(node_0)
                    if is_4hr(slot):
                        node_1 = str(slot)+"_1"
                        overlap_nodes.append(node_1)
                for k in overlap_nodes:
                    k_x = get_alt_slot(k)
                    if k_x != None:
                        prob += lpSum([choices[u][v] + choices[u][x] + choices[u][k] + choices[u][k_x] for u in j_nodes]) <= 1, ""
                    else:
                        prob += lpSum([choices[u][v] + choices[u][x] + choices[u][k] for u in j_nodes]) <= 1, ""
            if x != None:
                prob += lpSum([choices[u][v] + choices[u][x] for u in j_nodes]) <= 1, ""
            if k in OVERLAPS.keys():
                overlap_slots = OVERLAPS[k] #get overlap nodes as list
                overlap_nodes = []
                for slot in overlap_slots:
                    node_0 = str(slot)+"_0"
                    overlap_nodes.append(node_0)
                    if is_4hr(slot):
                        node_1 = str(slot)+"_1"
                        overlap_nodes.append(node_1)
                for l in overlap_nodes:
                    prob += lpSum([choices[u][v] + choices[u][l] for u in j_nodes]) <= 1, ""


# For all k, \sum_{s,j} x(s,k,j,1) + x(s,k,j,0) \leq c_k. Guarantees that each slot has at most c_k students.
    for v in get_slot_type(to_nodes, 0):
        slot = get_slot(v)
        x = get_alt_slot(v) #sees if slot is potential 4hr (has alternate node) and returns node if yes
        if x != None:
            prob += lpSum([choices[u][v] + choices[u][x] for u in from_nodes]) <= slotdict[slot], ""
        else:
            prob += lpSum([choices[u][v] for u in from_nodes]) <= slotdict[slot], ""

# For all s,k,j x(s,k,j,1) \leq \sum_\ell x(s,k-2,\ell,0)+x(s,k-2,\ell,1). Guarantees that you get to be the end of a 4-hour slot only if you're actually part of the slot before it.
    for u in from_nodes:
        #make list of student nodes
        name = u.split('_')[:1][0]
        j_nodes = get_student_nodes(name, from_nodes)
        for x in get_slot_type(to_nodes, 1):
            prev = get_prev_slot(x)
            prev_x = get_alt_slot(prev)
            if prev_x != None:
                prob += lpSum([choices[j][x] - choices[j][prev] - choices[j][prev_x] for j in j_nodes]) <= 0, ""
            else:
                prob += lpSum([choices[j][x] - choices[j][prev] for j in j_nodes]) <= 0, ""

# For all s,k, j x(s,k,j,0) \leq 1-\sum_\ell x(s,k-2,\ell,0)+x(s,k-2,\ell,1). Guarantees that you only get an isolated 2-hour slot if you're not part of the slot before it.
    for u in from_nodes:
        #make list of student nodes
        name = u.split('_')[:1][0]
        j_nodes = get_student_nodes(name, from_nodes)
        for v in get_slot_type(to_nodes, 0):
            prev = get_prev_slot(v)
            if prev != None:
                prev_x = get_alt_slot(prev)
                if prev_x != None:
                    prob += lpSum([choices[j][v] + choices[j][prev] + choices[j][prev_x] for j in j_nodes]) <= 1, ""
                else:
                    prob += lpSum([choices[j][v] + choices[j][prev] for j in j_nodes]) <= 1, ""


    # make sure each student's shift is used once
    for u in from_nodes:
        prob += lpSum([choices[u][v] for v in to_nodes]) <= 1, ""

    # # constraint on overlaps
    # for u in from_nodes:
    #     #make list of student nodes
    #     name = u.split('_')[:1][0]
    #     j_nodes = get_student_nodes(name, from_nodes)
    #     for v in to_nodes:
    #         # D) For all i, and all k, k' which are overlapping, \sum_j x(i,j,k) + x(i,j,k') \leq 1 (student cannot take overlapping shifts).
    #         if v in OVERLAPS.keys():
    #             overlap_nodes = OVERLAPS[v] #get overlap nodes as list
    #             for k in overlap_nodes:
    #                 prob += lpSum([choices[u][v] for u in j_nodes] + [choices[u][k] for u in j_nodes]) <= 1, ""

    # for v in to_nodes:
    #    #A) For all k, \sum_{i,j} x(i,j,k) \leq c_k (for each slot, have at most c_k students in that slot).
    #    prob += lpSum([choices[u][v] for u in from_nodes]) <= slotdict[v], ""
    # for u in from_nodes:
    #     #B) For all i, j, \sum_k x(i,j,k) \leq 1 (a student can only use their jth shift once)
    #     prob += lpSum([choices[u][v] for v in to_nodes]) <= 1, ""





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
            slot = stud_slot[length - 3] + "_" + stud_slot[length - 2]
            stud = ''
            for i in range(int(length - 4)):
                stud += (stud_slot[i] + " ")
            stud = stud[:-1]

            if slot in sched_dict:
                sched_dict[slot].append(stud)
            else:
                sched_dict[slot] = [stud]
            # print(f'{v.name} = {v.varValue}')
    # print(f"Sum of wts of selected edges = {round(value(prob.objective), 4)}")
    return(sched_dict)

#gets all slots of a given type
def get_slot_type(to_nodes, slot_type):
    all_slot_type = []
    for slot_node in to_nodes:
        if int(slot_node[-1]) == int(slot_type):
            all_slot_type.append(slot_node)
    return(all_slot_type)

def get_alt_slot(slot_node):
    slot = get_slot(slot_node)
    if is_4hr(slot):
        alt_slot = str(slot) + "_1"
        return(alt_slot)
    else:
        return(None)

def is_4hr(slot):
    if slot in PREV_SLOT.keys():
        return(True)
    else:
        return(False)

def get_prev_slot(slot_node):
    slot = get_slot(slot_node)
    if is_4hr(slot):
        prev_slot = PREV_SLOT[slot]
        prev_slot_node = str(prev_slot) + "_0"
        return(prev_slot_node)
    else:
        return(None)


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
    df = input_creator.make_df()

    #example weights
    weight_dict = {}


    weight_dict['slot_type'] = 7
    weight_dict['no_1'] = 9
    weight_dict['guarantee_shift'] = 6
    weight_dict['avail'] = 4
    weight_dict['shift_cap'] = 3
    weight_dict['equality'] = 3



    #create graph nodes and weight edges
    graph_data = create_graph(df, weight_dict)
    student_nodes = graph_data[0]
    slot_nodes = graph_data[1]
    wt = graph_data[2]

    #solve the problem and get the ordered schedule
    p = solve_wbm(student_nodes, slot_nodes, wt)
    unordered_sched_dict = get_solution(p)
    max_weight_sched = order_sched(df, unordered_sched_dict)
    # Schedule.print_sched(max_weight_sched)
    schedule_to_df(df, max_weight_sched)

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
    post_hap = stats.sched_happiness(df, max_weight_sched, PREV_SLOT)

#[avg_hap, corr, var[0], min_students, max_students, stud_1s, shiftless, wrong_type_studs]

    print('Average Happiness: ', post_hap[0])
    print()
    print('Availability to happiness correlation: ', post_hap[1])
    print()
    print('Variance of happiness: ', post_hap[2])
    print()
    print('Min happy outlier students: ', post_hap[3])
    print()
    print('Max happy outlier students: ', post_hap[4])
    print()
    print('Students who got 1\'s: ', post_hap[5])
    print()
    print('Students without shifts: ', post_hap[6])
    print()
    print('Students who got wrong slot type: ', post_hap[7])
    print()


    # #get experience dict
    # exp_dict = {}
    # students = list(df['name'])
    # for index in range(NUM_STUDENTS):
    #     exp_dict[str(df.at[index, 'name'])] = int(df.at[index, 'experience'])
    #
    # #Evaluate experience stats of schedule
    # stats.exp_stats(exp_dict, max_weight_sched)
    # response = True
    # while (response == True):
    #     response = str(input("Want to swap a student out? (y/n): "))
    #     if response == "y":
    #         student = str(input("Enter student to swap: "))
    #         slot = str(input("Enter their slot to swap them out of: "))
    #
    #         #check student and slot are good inputs
    #         if student not in list(df['name']):
    #             print('student given is not in schedule')
    #             exit(0)
    #         if slot not in slotdict.keys():
    #             print('slot given is not in schedule')
    #             exit(0)
    #
    #         swap_cands_dict = swap.max_weight_suggest(max_weight_sched, p, wt, slot, student)
    #         accept_swap  = False
    #         while (accept_swap == False):
    #             for cand in swap_cands_dict.keys():
    #                 #print out top candidate edge
    #                 print(cand)
    #                 #ask to accept or not
    #                 response = str(input("Want to accept proposed swap? (y/n): "))
    #                 if response == 'y':
    #                     accept_swap = True
    #
    #                     stud_slot = str(cand).split('_')
    #                     length = len(stud_slot)
    #
    #                     #get the new ta
    #                     new_ta = ''
    #                     for i in range(int(length - 3)):
    #                         new_ta += (stud_slot[i] + " ")
    #                     new_ta = new_ta[:-1]
    #
    #                     #get the new slot
    #                     new_slot = stud_slot[length - 2] + "_" + stud_slot[length - 1]
    #
    #                     swap.swap_TA(df, max_weight_sched, student, slot, new_ta, new_slot)
    #                     break
    #
    #     else:
    #         response = False
    #make output schedule in sheet
    # output_creator.make_sheet(max_weight_sched)
if __name__ == "__main__":
    main()
