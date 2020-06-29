import csv

def get_exp(exp_file, students):
    '''returns a dict of given students and their semesters of past labTA experience'''
    exp_dict = {}
    for student in students:
        exp_dict[student] = 0
    with open(str(exp_file), newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            firstname = row['First Name']
            lastname = row['Last Name']
            position = row['Position']
            student = firstname + " " + lastname
            #if student is in dict and if their position was 'labta', increase their exp count
            if ((student in exp_dict.keys()) and (position == 'Lab TA')):
                 exp_dict[student] += 1
    return(exp_dict)
