import json
import PySimpleGUI as sg
import datetime as dt

class Assignment:
    def __init__(self, title, due_date):
        self.title = title
        self.properties = {'Due-date' : due_date, 'Status' : 'Pending'}

    # def __del__(self):
    #     return

    def check_status(self, urgent_timedelta):
        if self.properties['Status'] == 'Done':
            return 'Done'
        if isinstance(self.properties['Due-date'], str):
            self.properties['Due-date'] = dt.datetime.strptime(self.properties['Due-date'], "%Y-%m-%d %H:%M:%S")
        if (self.properties['Due-date'] - dt.datetime.now()).total_seconds()<=0:
            self.properties['Status'] = 'Overdue'
            return 'Overdue'
        elif (self.properties['Due-date'] - dt.datetime.now()).total_seconds()<=urgent_timedelta:
            self.properties['Status'] = 'Urgent'
            return 'Urgent'
        return 'Pending'

class Course:
    def __init__(self, title):
        self.title = title
        self.assignments = {}

class Dashboard:
    def __init__(self):
        self.courses = {}
        self.preferences = {'Time' : 24*60*60, 'Show Courses' : 'All', 'Hide Done' : False, 'Hide Overdue' : False}
        course_listbox = [sg.Listbox(values=self.courses.keys(),
                                     size=(30, 10),
                                     key='-COURSE_LIST-',
                                     enable_events=True,
                                     background_color=	'#A9A9A9',
                                     font=('Helvetica', 13))]

        assignments_table = sg.Table(values=[],
                                     headings=['Title', 'Course', 'Due-date', 'Status'],
                                     key='-ASSIGNMENT_LIST-',
                                     # size=(120, 20),
                                     auto_size_columns=False,
                                     justification='left',
                                     selected_row_colors=('black', 'blue'),
                                     select_mode='browse',
                                     background_color='#A9A9A9',
                                     max_col_width=55,
                                     def_col_width=20,
                                     expand_x=True)

        courses_column = [[sg.Button('Add Course'), sg.Button('Delete Course', button_color='red')],
                          [sg.Text('Courses: ', font=('Helvetica', 14))],
                          course_listbox,
                          [sg.Text('', key='-COURSES_ERROR-', text_color='red')]]

        assignments_column = [[sg.Button('Add Assignment'), sg.Button('Delete Assignment', button_color='red'), sg.Button('Mark As Done', button_color='green')],
                              [sg.Text('Assignments: ', font=('Helvetica', 14))],
                              [assignments_table],
                              [sg.Text('', key='-ASSIGNMENTS_ERROR-', text_color='red')],
                              ]
        layout = [
            [
                [sg.Button('Settings')],
                [sg.Column(courses_column, size=(350,400), element_justification='center'),
                sg.VSeperator(),
                sg.Column(assignments_column, size=(750,400), element_justification='center')]
            ]
        ]
        self.main_window = sg.Window('Dashboard', layout)
        while True:
            self.main_window.read(timeout=1)
            self.read_from_file()
            event, values = self.main_window.read()
            if event in (None, sg.WINDOW_CLOSED):
                break
            else:
                if event in ['Add Course', 'Add Assignment', '-ASSIGNMENT_LIST-', '-COURSE_LIST-', 'Settings', 'Delete Assignment', 'Delete Course']:
                    self.update_assignments_status()
                    self.reset_errors()
                if event == 'Delete Course':
                    if values['-COURSE_LIST-']:
                        if self.confirmation_window():
                            self.delete_course(values['-COURSE_LIST-'][0])
                            self.write_to_file()
                    else:
                        self.main_window['-COURSES_ERROR-'].update('No course was selected')
                if event == 'Add Course':
                    self.add_course_window()
                    self.write_to_file()
                if event == 'Add Assignment':
                    self.add_assignment_window()
                    self.write_to_file()
                if event == 'Delete Assignment':
                    if len(values['-ASSIGNMENT_LIST-'])>0:
                        self.delete_assignment(index = values['-ASSIGNMENT_LIST-'][0])
                    else:
                        self.main_window['-ASSIGNMENTS_ERROR-'].update('No assignment was selected')
                    self.write_to_file()
                if event == 'Mark As Done':
                    if len(values['-ASSIGNMENT_LIST-'])>0:
                        selected_assignment = self.main_window['-ASSIGNMENT_LIST-'].Values[values['-ASSIGNMENT_LIST-'][0]]
                        self.mark_as_done(title=selected_assignment[0], course=selected_assignment[1])
                    else:
                        self.main_window['-ASSIGNMENTS_ERROR-'].update('No assignment was selected')
                    self.write_to_file()
                if event == 'Settings':
                    self.settings_window()
                    self.write_to_file()
        self.main_window.close()

    def add_course_window(self):
        title_row = [sg.Text('Title: '), sg.Input(key='-TITLE-'), sg.Button('Add')]
        layout = [
            [
                [title_row],
                [sg.Text('', key='-ERROR-', text_color='red')]
            ]
        ]
        ac_window = sg.Window('Add Course', layout)
        while True:
            event, values = ac_window.read()
            if event in (None, 'Exit', sg.WINDOW_CLOSED):
                break
            else:
                if event == 'Add' and values['-TITLE-'] and values['-TITLE-'] not in self.courses.keys():
                    self.add_course(title=values['-TITLE-'])
                    ac_window.close()
                    break
                elif not values['-TITLE-']:
                    ac_window['-ERROR-'].update('You must enter a title')
                elif values['-TITLE-'] in self.courses.keys():
                    ac_window['-ERROR-'].update('This title is already taken')
        return

    def add_assignment_window(self):
        course_listbox = sg.Listbox(values=list(self.courses.keys()),
                                     size=(40, 5),
                                     key='-COURSE_LIST-',
                                     select_mode="LISBOX_SELECT_MODE_SINGLE",
                                     enable_events=True)
        title_row = [sg.Text('Title: '), sg.Input(key='-TITLE-')]
        course_row = [sg.Text('Course: '), course_listbox]
        calendar_input = sg.In(key='-CAL-', enable_events=True, visible=True)
        date_row = [sg.Text('Due-date: '), calendar_input, sg.CalendarButton('Calendar', target='-CAL-')]
        layout = [
            [
                course_row,
                title_row,
                date_row,
                sg.Button('Add'),
                [[sg.Text('', key='-ERROR-', text_color='red')]]
            ]
        ]
        aa_window = sg.Window('Add Assignment', layout)
        while True:
            event, values = aa_window.read()
            if event == 'Add':
                if not values['-TITLE-'] or not values['-COURSE_LIST-'] or not values['-CAL-']:
                    aa_window['-ERROR-'].update('You must fill out all fields')
                elif values['-TITLE-'] in set(self.courses[values['-COURSE_LIST-'][0]].assignments.keys()):
                    aa_window['-ERROR-'].update('Assignments in the same course must have different titles')
                else:
                    self.add_assignment(course=values['-COURSE_LIST-'][0], title=values['-TITLE-'], due_date=values['-CAL-'])
                    aa_window.close()
                    break
            if event in (None, 'Exit'):
                break
        aa_window.close()

    def add_course(self, title):
        course_obj = Course(title=title)
        self.courses[title] = course_obj
        self.main_window['-COURSE_LIST-'].Values.append(course_obj.title)
        self.main_window['-COURSE_LIST-'].update(self.main_window['-COURSE_LIST-'].Values)


    def add_assignment(self, course, title, due_date):
        assignment_obj = Assignment(title=title, due_date=dt.datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S"))
        (self.courses[course].assignments)[title] = assignment_obj
        self.main_window['-ASSIGNMENT_LIST-'].Values.append([title, course, due_date, assignment_obj.check_status(urgent_timedelta = self.preferences['Time'])])
        self.main_window['-ASSIGNMENT_LIST-'].update(self.main_window['-ASSIGNMENT_LIST-'].Values)
        self.update_assignments_status()

    def delete_assignment(self, index):
        # self.courses[self.main_window['-ASSIGNMENT_LIST-'].Values[index][1]].assignments[self.main_window['-ASSIGNMENT_LIST-'].Values[index][0]].__del__()
        self.courses[self.main_window['-ASSIGNMENT_LIST-'].Values[index][1]].assignments.pop(self.main_window['-ASSIGNMENT_LIST-'].Values[index][0])
        self.main_window['-ASSIGNMENT_LIST-'].Values.pop(index)
        self.main_window['-ASSIGNMENT_LIST-'].update(self.main_window['-ASSIGNMENT_LIST-'].Values)

    def reset_errors(self):
        self.main_window['-ASSIGNMENTS_ERROR-'].update('')
        self.main_window['-COURSES_ERROR-'].update('')

    def confirmation_window(self):
        layout = [
            [
                [sg.Text("Are you sure?")],
                [sg.Button('Yes'), sg.Button('No')]
            ]
        ]
        cwindow = sg.Window('', layout)
        while True:
            event, values = cwindow.read()
            if event in (None, sg.WINDOW_CLOSED):
                return False
            elif event == 'No':
                cwindow.close()
                break
            elif event == 'Yes':
                cwindow.close()
                return True
        return False

    def delete_course(self, course):
        for i in list((self.courses[course].assignments).values()):
            assignment = [i.title, course, str(i.properties['Due-date']), i.properties['Status']]
            self.delete_assignment(self.main_window['-ASSIGNMENT_LIST-'].Values.index(assignment))
        self.courses.pop(course)
        self.main_window['-COURSE_LIST-'].update(list(self.courses.keys()))

    def settings_window(self):
        time_row = [sg.Text('Define assignments as urgent '),
                    sg.Input(default_text=self.preferences['Time']/(24*60*60), key='-TIME-'),
                    sg.Listbox(values=['Weeks', 'Days', 'Hours'],
                               default_values='Days',
                               key='-TIME_UNITS-',
                               select_mode="LISBOX_SELECT_MODE_SINGLE",
                               size=(10,3)),
                    sg.Text(' before due-date')]
        # if self.preferences['Hide Done']==True:
        #     sd_def='No'
        # else:
        #     sd_def='Yes'
        # if self.preferences['Hide Overdue']==True:
        #     so_def='No'
        # else:
        #     so_def='Yes'
        # sc_row = [sg.Text('Display assignments for: '), sg.Listbox(values=['All Courses', 'Selected Course Only'],
        #                                                           default_values='All Courses',
        #                                                           size=(20,2),
        #                                                           select_mode="LISBOX_SELECT_MODE_SINGLE")]
        sd_row = [sg.Text('Hide done assignments: '), sg.Listbox(values=['Yes', 'No'],
                                                                 default_values=self.sd_def(),
                                                                 select_mode="LISBOX_SELECT_MODE_SINGLE",
                                                                 size=(5,2),
                                                                 key='-HIDE_DONE-')]
        so_row = [sg.Text('Hide overdue assignments: '), sg.Listbox(values=['Yes', 'No'],
                                                                 default_values=self.so_def(),
                                                                 select_mode="LISBOX_SELECT_MODE_SINGLE",
                                                                 size=(5,2),
                                                                 key='-HIDE_OVERDUE-')]
        layout = [
            [
                [time_row],
                [sg.HorizontalSeparator()],
                # [sc_row],
                [sd_row],
                [so_row],
                [sg.Button('Save')]
            ]
        ]
        swindow = sg.Window('Settings', layout)
        units_dict = {'Weeks' : 7*24*60*60, 'Days' : 24*60*60, 'Hours' : 60*60}
        while True:
            event, values = swindow.read()
            if event in (None, sg.WINDOW_CLOSED):
                return
            elif event == 'Save':
                if values['-HIDE_DONE-'][0]=='Yes':
                    self.preferences['Hide Done'] = True
                else:
                    self.preferences['Hide Done'] = False
                if values['-HIDE_OVERDUE-'][0]=='Yes':
                    self.preferences['Hide Overdue'] = True
                else:
                    self.preferences['Hide Overdue'] = False
                self.preferences['Time'] = units_dict[values['-TIME_UNITS-'][0]]*float(values['-TIME-'])
                self.update_assignments_status()
                swindow.close()
                break

    def update_assignments_status(self):
        new_vals = []
        row_num = 0
        urgent_rows=[]
        overdue_rows=[]
        done_rows=[]
        pending_rows=[]
        for course in self.courses.values():
            for assignment in course.assignments.values():
                status = assignment.check_status(urgent_timedelta=self.preferences['Time'])
                if status in ['Pending', 'Urgent'] or (status=='Done' and self.preferences['Hide Done']==False) or (status=='Overdue' and self.preferences['Hide Overdue']==False):
                    new_vals.append([assignment.title, course.title, str(assignment.properties['Due-date']), status])
                    if status=='Pending':
                        pending_rows.append(row_num)
                    if status == 'Urgent':
                        urgent_rows.append(row_num)
                    if status == 'Overdue':
                        overdue_rows.append(row_num)
                    if status == 'Done':
                        done_rows.append(row_num)
                    row_num+=1
        self.main_window['-ASSIGNMENT_LIST-'].update(new_vals)
        for i in pending_rows:
            self.main_window['-ASSIGNMENT_LIST-'].update(row_colors=[[i, '#7D9EC0']])
        for i in urgent_rows:
            self.main_window['-ASSIGNMENT_LIST-'].update(row_colors=[[i, 'red']])
        for i in overdue_rows:
            self.main_window['-ASSIGNMENT_LIST-'].update(row_colors=[[i, 'black']])
        for i in done_rows:
            self.main_window['-ASSIGNMENT_LIST-'].update(row_colors=[[i, 'green']])


    def mark_as_done(self, title, course):
        (self.courses[course].assignments[title]).properties['Status'] = 'Done'
        self.update_assignments_status()

    def so_def(self):
        if self.preferences['Hide Overdue']==True:
            return 'Yes'
        return 'No'
    def sd_def(self):
        if self.preferences['Hide Done']==True:
            return 'Yes'
        return 'No'

    def write_to_file(self):
        self.update_assignments_status()
        data = {'Preferences' : self.preferences, 'Courses' : {}}
        for course in list(self.courses.keys()):
            assignments={}
            for assignment in self.courses[course].assignments.keys():
                assignments[assignment] = (self.courses[course].assignments[assignment]).properties
                assignments[assignment]['Due-date'] = (assignments[assignment]['Due-date']).strftime("%Y-%m-%d %H:%M:%S")
            data['Courses'][course] = assignments
        data = json.dumps(data)
        with open("courses_data.json", "w") as json_file:
            json_file.write(data)


    def read_from_file(self):
        try:
            with open("courses_data.json", "r") as json_file:
                json_data = json.load(json_file)
            self.preferences = json_data['Preferences']
            for course_title in list(json_data['Courses'].keys()):
                course_obj = Course(title=course_title)
                for assignment_title in json_data['Courses'][course_title].keys():
                    assignment_obj = Assignment(title=assignment_title, due_date=json_data['Courses'][course_title][assignment_title]['Due-date'])
                    course_obj.assignments[assignment_title] = assignment_obj
                self.courses[course_title] = course_obj
            self.main_window['-COURSE_LIST-'].update(list(json_data['Courses'].keys()))
            self.update_assignments_status()
        except:
            self.main_window['-ASSIGNMENTS_ERROR-'].update('There may have been a problem reading your saved data')








Dashboard().main_window()

