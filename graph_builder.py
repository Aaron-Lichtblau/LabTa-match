import networkx as nx
import gspread
import pandas as pd
from schedule import Schedule
import re
from oauth2client.service_account import ServiceAccountCredentials

# slots and num of TA's desired
slotdict = {"M_7" : 8, "M_9" : 6,"Tu_7" : 5, "Tu_9" : 4,"W_7" : 4, "W_9" : 4,"Th_7" : 4, "Th_9" : 4,"F_7" : 4, "F_9" : 4,"Sa_3" : 5, "Sa_4" : 6,"Sa_5" : 5,"Su_5" : 4,"Su_6" : 3,"Su_7" : 6,"Su_8" : 4, "Su_9" : 6}
NUM_SLOTS = 16.0 #number of slots
NUM_STUDENTS = 45
HOURS_LIMIT = 4 #limit of hours a TA can work

# give the student-slot edge a weight
#add edges between (max_weight) if student put a 0
#rank weight edges based on 1. preference 2. availability 3. happiness
def weight_edge(df, student, slot):
    """returns the student-slot edge weight"""
    weight = 0
    return (weight)

# build an unconnect graph
def unconnected_graph():
    """builds an unconnected graph representing the matching problem"""
    # build graph
    G = nx.Graph()
    #add each student as 2 nodes
    for student in range(NUM_STUDENTS):
        for i in range(int(HOURS_LIMIT / 2)):
            ta_node = str(student) + "." + str(i)
            G.add_node(ta_node)

    #add slots as nodes the number of times as their cap for ta's
    for slot in slotdict.keys():
        for i in range(slotdict[slot]):
            slot_node = str(slot) + "." + str(i)
            G.add_node(slot_node)
    #return the unconnect graph
    return(G)

# convert from graph to schedule
def graph_to_sched(df, graph):
    """converts a graph into a schedule"""
    nodes = list(graph.nodes)
    schedule = {"M_7" : [], "M_9" : [],"Tu_7" : [], "Tu_9" : [],"W_7" : [], "W_9" : [],"Th_7" : [], "Th_9" : [],"F_7" : [], "F_9" : [],"Sa_3" : [], "Sa_4" : [],"Sa_5" : [],"Su_5" : [],"Su_6" : [],"Su_7" : [],"Su_8" : [], "Su_9" : []}

    for slot in schedule.keys():
        search = str(slot) + ".*"
        r = re.compile(search)
        slot_nodes = list(filter(r.match, nodes))
        for nodes in slot_nodes:
            #get the student node that is neighbors with this slot
            ta_node = list(graph.neighbors(nodes))
            if (len(ta_node) > 0):
                ta_num = STUD_NODES_TO_NUMS[ta_node[0]]
                ta_name = df.at[ta_num, "name"]
                schedule[slot].append(ta_name)
    #convert to schdeule
    max_weight_sched = Schedule(schedule)
    return(max_weight_sched)

#-------------------------------------------------------------------------------
# Testing area
#-------------------------------------------------------------------------------

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('labTA-match-secret.json', scope)
client = gspread.authorize(creds)

# Find workbook and open the first sheet
sheet = client.open('LabTA_test2').sheet1
df_original = pd.DataFrame(sheet.get_all_records())

#create a dict to convert student nodes to student nums
STUD_NODES_TO_NUMS = {}
for student in range(NUM_STUDENTS):
    node1 = str(student) + "." + "1"
    node2 = str(student) + "." + "2"
    STUD_NODES_TO_NUMS[node1] = student
    STUD_NODES_TO_NUMS[node2] = student

#create a dict to convert slot to slot nodes
SLOT_NODES = {}
for slot in slotdict.keys():
    SLOT_NODES[slot] = []
    for i in range(slotdict[slot]):
        slot_node = str(slot) + "." + str(i)
        SLOT_NODES[slot].append(slot_node)
print(SLOT_NODES)
# make an unconnected graph
G = unconnected_graph()

# get edge weights and add edges
# weight all edges
for student in range(NUM_STUDENTS):
    for slot in slotdict.keys():
        edge_weight = weight_edge(df_original, student, slot)
        #for all nodes of student and slot, add edges of the edge weight
        for stud_node in STUD_NODES_TO_NUMS.keys():
            for slot_node in SLOT_NODES[slot]:
                G.add_weighted_edges_from([(stud_node, slot_node, edge_weight)])

#get max weight matching
max_weight_graph =

#convert to schedule
max_weight_sched = graph_to_sched(df_original, max_weight_graph)
Schedule.print_sched(max_weight_sched)
Evaluate happiness stats of schedule
post_hap = stats.sched_happiness(df_original, max_weight_sched)
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
