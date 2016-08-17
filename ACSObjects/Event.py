import datetime
import os
from fnmatch import fnmatch
from ACSObjects.abstract_class import AbstractLevel
from ACSObjects.Mission import Mission
import string


class Event(AbstractLevel):
    """Object to represent the Event level of the hierarchy

    An "Event" is the set of missions flown over a consecutive set of field experimentation days
    """

    pattern_dictionary = AbstractLevel.pattern_dictionary.copy()
    """The pattern dictionary contains types as files as keys and search expressions as values.
    Each key corresponds to a type of file/folder related to the Mission. This is used by Mission.find_data()
    to load relevant files. This dictionary extends the one defined by AbstractLevel.

    Default values include:

   mission_folder : Mission*\n
   date_folder : ????-??-??
    """
    pattern_dictionary['mission_folder'] = 'Mission*'
    pattern_dictionary['date_folder'] = '????-??-??'

    def __init__(self, path=''):
        AbstractLevel.__init__(self)
        self.path = path
        '''Path to the Event folder'''

        self.start_date = None
        '''Start date of the event'''

        self.end_date = None
        '''End date of the event'''

        self.num_missions = None
        '''Number of missions over the event'''

        self.num_sorties = None
        '''Number of sorties over the event'''

        self.mean_intersortie_time = None

        self.total_airtime = None
        '''Total UAV-flighthours'''

        self.date = self.start_date

        self.mission_list = {}
        '''Dictionary of Missions, each key corresponds to a Mission Number. E.g. the Mission 3 object is in mission_list[3]'''

        self.mission_list_date = {}
        '''Dictionary of dates, each date has a list of missions. There will be one key for every day the Event was happening'''

        self.mission_definition_csv = None
        if self.path != '':
            self.find_data()
            if 'date_folder' in self.path_dictionary.iterkeys():
                for date_path in self.path_dictionary['date_folder']:
                    for dir in os.listdir(date_path):
                        if fnmatch(dir,self.pattern_dictionary['mission_folder']):
                            temp_mission = Mission(os.path.join(date_path,dir))
                            self.mission_list_date.setdefault(temp_mission.date.strftime('%Y-%m-%d'), []).append(temp_mission)

        for date, mission_list in self.mission_list_date.iteritems():
            for mission in mission_list:
                self.mission_list[mission.mission_number] = mission

        print self.mission_list

    def get_mission_variable(self, variable):
        """Gets the instance variable specified by 'variable' for each mission in the event
        Returns response_dict and response_list

        response_dict is a dictionary of outputs from the called Mission variables, with the key corresponding to the Mission number.

        response_list is a list of outputs from the called Mission variables, in the order they were called.
        Not reliably ordered, but more intuitive to loop through for operations where order doesn't matter.
        """
        response_dict = {}
        response_list = []
        for mission_num, mission in self.mission_list.iteritems():
            response = getattr(mission, variable)
            response_dict[mission_num] = response
            response_list.append(response)

        return response_dict, response_list

    def call_mission_function(self, method, arg_list):
        """Calls the method specified as a string by 'method' for each mission in the event
        Returns response_dict and response_list

        response_dict is a dictionary of outputs from the called mission functions, with the key corresponding to the mission number.

        response_list is a list of outputs from the called mission functions, in the order they were called.
        Not reliably ordered, but more intuitive to loop through for operations where order doesn't matter.
        """
        response_dict = {}
        for mission_num, mission in self.mission_list.iteritems():
            built_method = getattr(mission, method)
            try:
                response = built_method(*arg_list)
            except Exception as ex:
                response = ex
            response_dict[mission_num] = response

        return response_dict

    def get_num_sorties(self):
        """Gets the total number of sorties over the event"""
        sortie_counter = 0
        error_list = []
        for mission in self.mission_list.itervalues():
            try:
                sortie_counter += mission.num_sorties
            except Exception as ex:
                error_list.append(ex)
        print(error_list)
        self.num_sorties = sortie_counter
        return self.num_sorties

    def get_num_missions(self):
        """Gets the total number of missions over the event"""
        self.num_missions = len(self.mission_list)
        return self.num_missions

    def analyze_missions(self):
        """Makes all missions of the event execute their analysis methods"""
        self.call_mission_function('analyze', [])

    def calculate_total_airtime(self):
        time_counter = datetime.timedelta(seconds=0)
        error_list = []
        for mission in self.mission_list.itervalues():
            try:
                time_counter += mission.total_airtime
            except Exception as ex:
                error_list.append(ex)
        print(error_list)
        self.total_airtime = time_counter
        return self.total_airtime

    def calculate_launch_separation(self):
        """Gets average launch separation over the course of the event"""

        time_counter = datetime.timedelta(seconds=0)
        count = 0
        for mission in self.mission_list.itervalues():
            if mission.num_sorties > 1:
                time_counter += mission.mean_intersortie_time
                count += 1
        time_counter = time_counter/count
        self.mean_intersortie_time = time_counter
        return self.mean_intersortie_time

    def analyze(self):
        """Call all Event analysis methods"""
        self.find_numbering()
        print('Analyzing Event %d' % self.event_number)
        self.analyze_missions()
        self.get_num_missions()
        self.get_num_sorties()
        # TODO: add other event analysis methods

    def find_numbering(self):
        """Identifies Mission/Event number and date from the path.
        Returns event number and mission number
        """
        tmp = string.split(self.path, '/')

        for i in tmp:
            indfx = string.find(i, 'Event')
            if indfx != -1:
                self.event_number = int(filter(str.isdigit, i))

        return self.event_number

