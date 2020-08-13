import gspread
from oauth2client.service_account import ServiceAccountCredentials
from schedule import Schedule
import yaml

def make_sheet(schedule):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('labTA-match-secret.json', scope)
    client = gspread.authorize(creds)
    #create a new sheet
    sh = client.create('LabTA Schedule example')
    #share it with myself
    sh.share('al27@princeton.edu', perm_type='user', role='writer')
    #add worksheet
    worksheet = sh.add_worksheet(title="LabTA Schedule", rows="100", cols="20")

    j = 1
    #add schedule into sheet
    for slot in schedule:
        i = 1
        worksheet.update_cell(i, j, str(slot))
        for student in schedule[slot]:
            i += 1
            worksheet.update_cell(i, j, str(student))
        j += 1


def new_file():
    f = open(r'E:\data\output_file.yaml', 'a')
    return(f)
def add_output(file, weight_dict, sched, stats):
    #make new proposal section in file
    #dump weight dict into proposal section
    weight_docs = yaml.dump(weight_dict, file)

    #dump schedule
    sched_dict = sched.schedule
    sched_docs = yaml.dump(sched_dict, file)

    #dump stats
    stats_docs = yaml.dump(stats, file)


    file = open("E:\data\output_file.yaml", "r")
    print(file.read())
    return(file)
