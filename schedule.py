import json

class Schedule:

    #initialize schedule from given schedule, default is blank
    def __init__(self, schedule = None):
        if schedule == None:
            schedule = {"M_7" : [], "M_9" : [],"Tu_7" : [], "Tu_9" : [],"W_7" : [], "W_9" : [],"Th_7" : [], "Th_9" : [],"F_7" : [], "F_9" : [],"Sa_3" : [], "Sa_4" : [],"Sa_5" : [],"Su_5" : [],"Su_6" : [],"Su_7" : [],"Su_8" : [], "Su_9" : []}
        self.schedule = schedule

    # allow for iterating over schedule dict
    def __iter__(self):
        return iter(self.schedule)

    # allow for getting slot details
    def __getitem__(self, key):
        return (self.schedule[key])

    #returns number of students in given slot
    def numStudents(self, slot):
        return(len(self.schedule[slot]))

    #adds a student to schedule
    def addStudent(self, slot, student):
        self.schedule[slot].append(student)

    def printSched(self):
        print(json.dumps(self.schedule, indent=3))
