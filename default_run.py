from schedule import Schedule
import input_creator
import output_creator
import stats
import graph
import solver


# a full run of the program
def run():
#-------------------------------------------------------------------------------
# Default input values

    #Default csv file
    csv_file = 'default_input.csv'

    #dict of target number of students in each slot
    slotdict = {"Mo_1900" : 8, "Mo_2100" : 6,"Tu_1900" : 5, "Tu_2100" : 4,"We_1900" : 4, "We_2100" : 4,"Th_1900" : 4, "Th_2100" : 4,"Fr_1900" : 4, "Fr_2100" : 4,"Sa_1500" : 5, "Sa_1600" : 6,"Sa_1700" : 5,"Su_1700" : 4,"Su_1800" : 3,"Su_1900" : 6,"Su_2000" : 4, "Su_2100" : 6}

    duration = 120 #length of slots (in minutes)

    #default column values
    gap = 180
    cap = 2
    exp = 3
    skill = 4

    #list of slots that need more skilled TA's
    stress_slots = []

    #numeric value indicating how many TAs the scheduler can hire above the targeted value for any given slot
    target_delta = 1

    #number of shifts the scheduler can assign in addition to the slotdict shift numbers
    flex_shifts = 4

    #sets minimum number of experienced TA's per slot
    min_exp = 0

    #sets minimum number of skilled TA's per stress slot
    min_skill = 0

    #gets number of slots
    num_slots = 0
    for slot in slotdict:
        num_slots += slotdict[slot]

    #Default weights
    weight_dict = {}
    weight_dict['slot_type'] = 4
    weight_dict['no_1'] = 3
    weight_dict['guarantee_shift'] = 5
    weight_dict['avail'] = 7
    weight_dict['shift_cap'] = 5
    weight_dict['equality'] = 3
#-------------------------------------------------------------------------------

    df = input_creator.get_df(csv_file)
    students = list(df['name'])
    input_creator.check_col(df, gap, cap, exp, skill)

    #dict of slots to check as keys, and overlapping slots as values (student won't be placed in overlap)
    slots = input_creator.get_slots(df)

    #dict of slots and their prev slots
    prev_slot = input_creator.get_prev_slots(df, duration)

    #create graph nodes and weight edges
    graph_data = graph.create_graph(df, weight_dict, slotdict, prev_slot, num_slots, duration)
    student_nodes = graph_data[0]
    slot_nodes = graph_data[1]
    wt = graph_data[2]

    #solve the problem, get the ordered schedule, updated df
    results = solver.run_solver(student_nodes, slot_nodes, wt, df, slotdict, min_exp, min_skill, stress_slots, target_delta, flex_shifts, duration)
    schedule = results[0]
    df = results[1]

    #get stats
    happiness_stats = stats.hap_stats(df, schedule)
    corr_stats = stats.corr_stats(df, schedule)
    student_stats = stats.stud_stats(df, schedule, prev_slot)
    slot_stats = stats.slotsize_stats(schedule, slotdict)
    #format output
    format_weights = {'weights used': weight_dict}
    sched_stats = {'avg hap': happiness_stats[0], 'std dev of hap': happiness_stats[1], 'min hap stud outliers': happiness_stats[2], 'avail to hap corr': corr_stats[0], 'skill to hap corr': corr_stats[1], 'experience to hap corr': corr_stats[2], 'studs who got 1s': student_stats[0], 'studs without shift': student_stats[2], 'wrong shift type studs': student_stats[1]}
    output_data = [format_weights, schedule, sched_stats, df]

    return(output_data)


def main():

    output_data = run()

    weights = output_data[0]
    schedule = output_data[1]
    sched_stats = output_data[2]
    df = output_data[3]

    print(schedule)
    print(df)
    print(sched_stats)

    # file = output_creator.new_file()
    # output_creator.add_output(file, weights, schedule, sched_stats)

if __name__ == "__main__":
    main()
