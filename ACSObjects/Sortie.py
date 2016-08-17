from ACSObjects.abstract_class import AbstractLevel
import datetime
import pandas as pd
import numpy as np
import os
import string, re
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from ACSObjects.sdlog2_dump import SDLog2Parser
import subprocess
import helpers as hp

class Sortie(AbstractLevel):
    """A class to represent the data associated with a Sortie.

    A "Sortie" is the flight of a single aircraft from launch to landing.
    However, this object will have data from pre-launch and post-landing as well

    Unless otherwise noted, the return values of methods are also automatically stored in their instance variable counterparts
    """

    pattern_dictionary = AbstractLevel.pattern_dictionary.copy()
    """The pattern dictionary contains types of files as keys and search expressions as values.
    Each key corresponds to a type of file related to the Sortie. This is used by Sortie.find_data()
    to load relevant files. This dictionary extends the one defined by AbstractLevel.

    Default values include:

    data_csv : FX*-M*-S*.csv\n
    altitude_graph : *Altitude_Graph.png\n
    launch_graph : *autolaunch.png\n
    waypoint_graph : *WPExec.png\n
    landing_overshoot_graph : *Overshoot_Graph.png\n
    bin_summary : *.BIN_summary.txt\n
    bin : *.BIN\n
    bin_text : *.BIN.txt\n
    params : *.parm\n
    waypoint_file : *.wp\n
    summary : FX*text_summary.txt\n
    """
    pattern_dictionary['data_csv'] = 'FX*-M*-S*.csv'
    pattern_dictionary['altitude_graph'] = '*Altitude_Graph.png'
    pattern_dictionary['launch_graph'] = '*autolaunch.png'
    pattern_dictionary['waypoint_graph'] = '*WPExec.png'
    pattern_dictionary['landing_overshoot_graph'] = '*Overshoot_Graph.png'
    pattern_dictionary['bin_summary'] = '*.BIN_summary.txt'
    pattern_dictionary['bin'] = '*.BIN'
    pattern_dictionary['bin_text'] = '*.BIN.txt'
    pattern_dictionary['params'] = '*.parm'
    pattern_dictionary['waypoint_file'] = '*.wp'
    pattern_dictionary['all_png'] = '*.png'

    # TODO: Make a 'units' or 'label' dict that will assign a certain axis label for each field in the flight_data dataframe

    def __init__(self, path=''):
        """Initialize this Sortie. Path specifies the path of the Sortie folder. It is strongly recommended to instantiate the Sortie class with a specified path."""

        AbstractLevel.__init__(self)
        print('Making Sortie for path %s' % path)
        if not (os.path.isdir(path) | (path == '')):
            path = os.path.split(str(path))[0]

        self.flight_data = None
        '''Pandas Dataframe that contains a variety of flight data. Read in from a .csv file.'''

        self.launch_time = None
        '''Time that the aircraft took off, determined by reaching speed threshold of 3 m/s.
        A pandas Timestamp representing the launch time of the Sortie.
        '''

        self.landing_time = None
        '''Time that the aircraft landed, determined by last time the aircraft was at a (GPS) speed greater than 3 m/s.
        A pandas Timestamp representing the landing time of the Sortie
        '''

        self.land_cmd_time = None
        '''Time that the aircraft was first commanded to land.
        Timestamp of first time a landing command was sent to the aircraft.
        '''

        self.last_land_cmd_time = None
        '''Timestamp of last time a landing WP command was sent to the Aircraft.'''

        self.handoff_time = None
        '''
        Timestamp that the aircraft handoff occurred.
        '''

        self.climbout_time = None
        '''Timestamp of climbout. '''

        self.egress_time = None
        '''
        Timestamp that the aircraft entered egress.
        '''

        self.landbreak_time = None
        '''
        Timestamp that the aircraft pulls out of its descent spiral and heads straight before landing.
        '''

        self.autoland = None
        '''
        Boolean indicating whether the aircraft landed autonomously.
        Determined by looking at aircraft mode numbers.
        '''

        self.land_direction = None
        ''' Indicates which location the aircraft landed at. Determined by landing waypoint number'''

        self.climbout_distance = None
        '''Distance traveled between launch and when climbout has finished (Distance between launch lat/lon and climbout lat/lon). Units: Meters'''

        self.climbout_dAlt = None
        '''Change in altitude between launch and position when climbout has completed. Units: Meters'''

        self.log_start_time = None
        '''First timestamp in the log file'''

        self.log_end_time = None
        '''Last timestamp in the log file'''

        # TODO: Maybe make these dictionaries loaded from an external .txt file?

        self.waypoint_dict = {'egress': [15, 19], 'pre-climbout': 2, 'pre-handoff': 3, 'auto_landing_sequence': {'A': [13, 15, 17], 'B': [19, 21, 23]}, 'land': [17, 23]}
        '''Dict in form WP_type:WP#. Ex: {egress:19, ...}'''

        self.waypoint_data_dict = None
        '''Not Implemented. Will be a dictionary in the form WP#:(lat,lng,alt)'''

        self.cid_list = {'loiter_unl': 17, 'loiter_time': 19, 'loiter_to_alt': 31, 'land': 21}
        '''Dictionary relating Command ID (waypoint types) to their number'''

        self.label_dict = {'index': 'Local Time', 'GPS_Alt': 'GPS Alt (M MSL)', 'GPS_Spd': 'GPS Spd (M/s)', 'BARO_Alt': 'Baro Alt (M AGL)', 'IMU_AccX': 'X Acc. (m/s/s)', 'IMU_AccY': 'Y Acc. (m/s/s)', 'IMU_AccZ': 'Z Acc. (m/s/s)', 'GPS_NSats':'Num. of Satellites', 'GPS_HDop': 'HDOP','MODE_Mode':'Flight Mode','CMD_CNum': 'Waypoint Number'}

        self.mode_list = {'manual': 0, 'circle': 1, 'stabilize': 2, 'training': 3, 'acro': 4, 'fbw_A': 5, 'fbw_B': 6, 'cruise': 7, 'autotune': 8, 'auto': 10, 'rtl': 11, 'loiter': 12, 'guided': 15, 'initializing': 16}
        '''Dictionary relating mode type to mode number'''

        self.uav_number = None
        '''UAV number of the Sortie'''

        self.sortie_number = None
        '''Number of the Sortie. Sorties are numbered sequentially in the order of launch.'''

        self.mission_number = None
        '''Number of the mission to which the Sortie belongs.'''

        self.fx_data = None
        '''Tuple of (Sortie.event_number,Sortie.mission_number,Sortie.sortie_number,Sortie.uav_number'''

        self.cut_data = None

        self.x_data = None
        self.x_label = ''
        self.x_max = None
        self.x_min = None

        self.y_data = None
        self.y_label = None
        self.y_max = None
        self.y_min = None

        self.z_data = None
        self.z_label = None

        self.figure = None

        self.axes = None
        '''The pyplot.axes object of a sortie plot (if it exists). Can be used to manually modify auto-generated plots'''

        # TODO: Document these
        self.param_list = []
        self.param_dict = {}

        # TODO: Make these dynamic. These are placeholders
        self.target_landing_lat = 35.7195358276
        '''Latitude of target landing point for the sortie'''

        self.target_landing_lng = -120.771690369
        '''Longitude of target landing point for the sortie'''

        # If there is a defined path when the object is created, it will try to associate other relevant files with  it
        # and then load the data .csv file if it was found
        if path != '':
            self.set_path(path)
            self.cut_data = self.flight_data.copy()
        else:
            self.path = path
            '''Path of the Sortie folder'''

    def extractFromDataFlash(self):
        """Given the path to a .BIN file, generate the .csv and load the .csv into the Sortie object
        NOTE: The current workflow does not utilize this method. In order for us to sort the .BIN files into the necessary
        file hierarchy, the .csv files need to already be generated. However, in theory this method would be useful in order
        to make .csv files of unsorted .BIN files.
        """
        if self.event_number is None:
            self.event_number = raw_input('Please enter event number for path %s' % self.path)

        if self.event_number == 22:
            sat_message = 'numSV'
        else:
            sat_message = 'NSats'

            # Set sdlog2_dump.py parameters
            debut_out = False
            correct_errors = False
            msg_filter = []
            time_msg = ""
            opt = None
            csv_delim = ","
            csv_null = ""

            self.path_dictionary['data_csv'] = os.path.join(self.path, 'FX%02d-M%02d-S%02d-UAV%02d.csv' % (
            self.fx_data[0], self.fx_data[1], self.fx_data[2], self.fx_data[3]))

            # Specify messages to extract
            msg_filter = [('GPS', ['TimeMS', 'Week', 'T', 'Lat', 'Lng', 'Alt', 'Spd', sat_message, 'HDop']),
                          ('IMU', ['AccX', 'AccY', 'AccZ']),
                          ('CTUN', ['ThrOut']),
                          ('BARO', ['Alt', 'Press']),
                          ('ARSP', ['Airspeed', 'Temp']),
                          ('CURR', ['Curr', 'Volt']),
                          ('MODE', ['Mode']),
                          ('NTUN', ['Arspd']),
                          ('CMD', ['CNum', 'CId'])]

            # Use sdlog2_dump.py code to generate the desired CSV file
            parser = SDLog2Parser()
            parser.setCSVDelimiter(csv_delim)
            parser.setCSVNull(csv_null)
            parser.setMsgFilter(msg_filter)
            parser.setTimeMsg(time_msg)
            parser.setDebugOut(debut_out)
            parser.setCorrectErrors(correct_errors)
            parser.setFileName(self.path_dictionary['data_csv'])

            parser.process(self.path_dictionary['bin'])

    def set_path(self, path):
        """If Sortie was instantiated without a Path, this will add a path the the object.

        DO NOT use this method if you have already created the Sortie object with a path, because then the data contained within the class will be mixed
        """
        self.path = path
        self.find_data()
        if 'data_csv' in self.path_dictionary.keys():
            print('Loading Data CSV')
            self.load_csv()
        else:
            self.extractFromDataFlash()
        # TODO: An 'else' statement here could auto-generate the data .csvs with extractFromDataFlash, at the expense of waiting for the csv to be created.

        self.find_numbering()

    def find_launch_time(self):
        """Returns a Timestamp of launch time.
        Currently, this is based on GPS_Spd going over 5 m/s. A more robust approach would be to check that forward
        acceleration reached at least 20 m/s/s, but this simpler approach has not yet been erroneous.
        """
        df = self.query_data(['GPS_Spd >= 5'])
        self.query_data(['reset'])
        self.launch_time = df.index[0]
        return self.launch_time

    def find_landing_time(self):
        """Returns a Timestamp of landing time. TODO: Take into account deceleration so as to not include sliding on ground"""
        # TODO: Take into account deceleration so as to not include sliding on ground
        df = self.query_data(['GPS_Spd > 3'])
        self.query_data(['reset'])
        self.landing_time = df.index[-1]
        return self.landing_time

    def calculate_sortie_duration(self):
        """Calculates the duration of the Sortie
        :return: timedelta
        """
        duration = self.landing_time - self.launch_time
        self.flight_time = duration
        return duration

    def find_land_cmd_time(self):
        """Returns the first time a landing command was issued to the UAV. """
        self.query_data(['CMD_CNum == %d' % self.waypoint_dict['land'][0]])
        for wp in range(1,len(self.waypoint_dict['land'])):
            self.query_data(['or','CMD_CNum == %d' % self.waypoint_dict['land'][wp]])
        self.land_cmd = self.cut_data.index[0]
        self.query_data(['reset'])
        return self.cut_data.index[0]

    def find_last_land_cmd_time(self):
        """Returns the last time a landing command was issued to the UAV. """
        self.query_data(['CMD_CNum == %d' % self.waypoint_dict['land'][0]])
        for wp in range(1,len(self.waypoint_dict['land'])):
            self.query_data(['or','CMD_CNum == %d' % self.waypoint_dict[wp]])
        self.query_data(['reset'])
        self.last_land_cmd = self.cut_data[-1]
        return self.cut_data[-1]

    def find_handoff_time(self):
        """Determine the (clock) time of when the sortie is considered to have reached handoff
        and proceeds to SWARM_READY mission
        - Measured when targeted waypoint transitions from inspection waypoint (WP2)
            to next waypoint
        :return: Timestamp
        """
        self.handoff_time = self.flight_data.index[ self.flight_data.CMD_CNum == self.waypoint_dict['pre-handoff']][-1]
        return self.handoff_time

    def find_climbout_time(self):
        """Determine the time that the UAV reached climbout"""
        self.climbout_time = self.flight_data.index[self.flight_data.CMD_CNum == self.waypoint_dict['pre-climbout']][-1]
        return self.climbout_time

    def find_egress_time(self):
        """ Determine the (clock) time of when the sortie is considered to have reached egress
        and proceeds to landing
        :return Timestamp
    """
        df = self.flight_data.copy()
        for egress_wp in self.waypoint_dict['egress']:
            cut_data = df.index[df.CMD_CNum == egress_wp]
            if len(cut_data) > 0:
                self.egress_time = cut_data[0]
                break

        return self.egress_time

    def find_landbreak_time(self):
        """ Determine the (clock) time of when the sortie is landing and breaks towards final approach
        - Measured when targeted waypoint transitions to landing waypoint (WP#17 or #23)
        :return Datetime
    """
        df = self.flight_data.copy()
        self.landbreak_time = df.index[df.CMD_CId == self.cid_list['land']][0] # index of first message with the 'land' command ID
        return self.landbreak_time

    def checkIfAutoLand(self):
        """ Check if this sortie conducted a complete autonomous landing, i.e.,
      requires passing through landing submission

       The sequence of waypoints it must pass through are stored in the dictionary Sortie.waypoint_list['auto_landing_sequence']['LANDING_WP_LETTER']
    """
        is_AUTO = is_land_A = is_land_B = False
        land_dir = None
        df = self.flight_data.copy()
        if ( self.mode_list['auto'] not in df.MODE_Mode.values ):
            return False, land_dir
        else:
            if self.land_cmd is None:
                self.find_land_cmd_time()
            if self.landing_time is None:
                self.find_landing_time()
            is_AUTO = all( df.MODE_Mode[self.land_cmd:self.landing_time].interpolate() == self.mode_list['auto'])

            suc = 0
            for site,wps in self.waypoint_dict['auto_landing_sequence'].iteritems():
                for wp in wps:
                    if wp in df.CMD_CNum.values:
                        suc += 1
                        if suc == len(wp):
                            self.land_direction = site
                            valid_land = True
                            return (is_AUTO & valid_land), site

    def calculate_climbout_data(self, show_plots=False):
        """
    Measure distance traveled from launch point to completion of climbout
    - Determine point of launch, either by launch time or by lat/lon data
    :return int, int
    """
        df = self.flight_data.copy()

        # TODO: Cross reference WP# and altitude to make sure it is really on rails. (maybe check position vs. launch position)
        on_rails = df.index[df.MODE_Mode == self.mode_list['auto']][0]

        # Get lat/lng when on rails
        launch_lat = df['GPS_Lat'][on_rails]
        launch_lng = df['GPS_Lng'][on_rails]

        # Determine when wp changes away from launch waypoint
        end_time = self.climbout_time

        # Capture lat/lng at climbout
        climbout_lat = df['GPS_Lat'][end_time]
        climbout_lng = df['GPS_Lng'][end_time]

        # Compute distance
        self.climbout_distance = hp.distance_2GPS(launch_lat, launch_lng, climbout_lat, climbout_lng)

        # Compute dAlt
        self.climbout_dAlt = df.GPS_Alt[end_time] - df.GPS_Alt[on_rails]

        return self.climbout_distance, self.climbout_dAlt

    def generate_parm(self):
        """Use mavparms.py to construct list of parameters for this Sortie from the dataflash log. Returns the path to the newly created file.
        :return str
        """
        print('Generating .parm file for %s' % self.path_dictionary['bin'][0])
        proc = subprocess.Popen(["mavparms.py", self.path_dictionary['bin'][0]], stdout=subprocess.PIPE)
        out, err = proc.communicate()

        output_file = os.path.join(self.path, 'FX%02d-M%02d-S%02d-UAV%02d.parm' % (
        self.fx_data[0], self.fx_data[1], self.fx_data[2], self.fx_data[3]))
        with open(output_file, 'w') as open_output:
            open_output.write(out)

        self.path_dictionary['params'] = output_file
        return self.path_dictionary['params']

    def generate_mission_file(self):
        """Use mavmission.py to generate the waypoint mission file for the Sortie"""
        print('Generating mission file for %s' % self.path_dictionary['bin'])

        # Call 'mavmission.py' tool to extract mission, with designated output file
        optionStr = "--output=" + os.path.join(self.path,'FX%02d-M%02d-S%02d-UAV%02d.wp' % (self.event_number, self.mission_number, self.sortie_number, self.uav_number))
        subprocess.Popen(["mavmission.py", self.path_dictionary['bin'][0], optionStr], stdout=subprocess.PIPE)

        self.path_dictionary['waypoint_file'] = os.path.join(self.path,'FX%02d-M%02d-S%02d-UAV%02d.wp' % (self.event_number, self.mission_number, self.sortie_number, self.uav_number))

    def load_csv(self):
        """Loads the .csv data from the FX??-M??-S??.csv file into the Sortie.flight_data variable. Returns pandas Dataframe.

        The GPS_TimeMS and GPS_Week fields are used to generate a new Timestamp index for the Dataframe. Any CSVs that
        have fields in the form of GPS_GMS or GPS_GWk are also supported and turned into this Timestamp index format.
        :return Pandas.Dataframe()
        """
        print('Reading %s' % self.path_dictionary['data_csv'])
        self.flight_data = pd.read_csv(self.path_dictionary['data_csv'][0])
        if 'GPS_GMS' in self.flight_data.columns:
            self.flight_data.rename(columns={'GPS_GMS':'GPS_TimeMS','GPS_GWk': 'GPS_Week'}, inplace=True)
        self.flight_data = self.flight_data[np.isfinite(self.flight_data['GPS_TimeMS'])]
        datetime_list = hp.convertSeriesGPSTime(self.flight_data.GPS_TimeMS/1000., self.flight_data.GPS_Week)
        pd.DatetimeIndex([i.replace(tzinfo=None) for i in datetime_list])
        self.flight_data.index = datetime_list
        return self.flight_data

    def find_numbering(self):
        """Sets the event_number, mission_number, sortie_number, and uav_number fields based on directory structure. Returns tuple containing this data.
        Tuple form: event_number,mission_number,sortie_number,uav_number
        :return int,int,int,int
        """
        try:
            tmp = string.split(self.path, '/')

            for i in tmp:
                indfx = string.find(i, 'Event')
                if (indfx != -1):
                    self.event_number = int( filter(str.isdigit, i) )

                indm = string.find(i, 'Mission')
                if (indm != -1):
                    self.mission_number = int( filter(str.isdigit, i) )

                inds = string.find(i, 'Sortie')
                if (inds != -1):
                        try:
                            self.sortie_number = int( filter(str.isdigit, i) )
                        except:
                            self.sortie_number = -1

                matches = re.findall('Sortie(\d+)-UAV(-?\d*)',i)
                if(len(matches) > 0):
                    self.sortie_number = int(matches[0][0])
                    if matches[0][1] == '':
                        self.uav_number = -1
                    else:
                        self.uav_number = int(matches[0][1])
        except:
            self.fx_data = (-1, -1, -1, -1)

        self.fx_data = (self.event_number, self.mission_number, self.sortie_number, self.uav_number)

        if self.uav_number == -1:
            self.find_uav_number()
            self.fx_data = (self.fx_data[0], self.fx_data[1], self.fx_data[2], self.uav_number)

        return self.fx_data

    def find_uav_number(self):
        """Returns the UAV Number of the Sortie. Note that the number may have already been determined by Sortie.find_numbering

        Will attempt first to extract the number from the .BIN_summary.txt file, then with the mavparms.py tool.
        :return int
        """
        try:
            with open(self.path_dictionary['bin_summary'],'r') as txtlog:
                lines = txtlog.read()
                matches = re.findall('Summary\sfor\splane\snumber\s*:\s(\d*)',lines)
                if matches != []:
                    self.uav_number = int(matches[0])
        except:
            self.uav_number = -1

        if self.uav_number == -1:
            try:
                with open(self.path_dictionary['bin_text'],'r') as txtlog:
                    lines = txtlog.read(10000)
                matches = re.findall('SYSID_THISMAV,\sValue\s:\s(\d*)',lines)
                if matches != []:
                    self.uav_number = int(matches[0])
            except:
                self.uav_number = -1

        if self.uav_number == -1:
            try:
                proc = subprocess.Popen(["mavparms.py",self.path_dictionary['bin']], stdout=subprocess.PIPE)
                out,err = proc.communicate()
                matches = re.findall('SYSID_THISMAV\s*(\d*)',out)
                if matches != []:
                        return int(matches[0])
            except:
                self.uav_number = -1

        return self.uav_number

    def summarize(self):
        """Writes sortie information to a .txt file. The name is in the form FX%02d-M%02d-S%02d-UAV%02d_text_summary.txt"""

        self.analyze()
        self.param_dict = self.__dict__
        summary_file_name = os.path.join(self.path, 'FX%02d-M%02d-S%02d-UAV%02d_text_summary.txt' % (
        self.event_number, self.mission_number, self.sortie_number, self.uav_number))
        self.path_dictionary['summary'] = summary_file_name
        with open(summary_file_name, 'w') as output:
            output.write('Summary of Sortie. Generated by Sortie.summarize()\n')
            output.write('Event: %d\nMission: %d\nSortie: %d\nUAV: %d\n=============================\n' % (
            self.event_number, self.mission_number, self.sortie_number, self.uav_number))
            output.write('Launch Time: %s\n' % str(self.launch_time))
            output.write('Landing Time: %s\n' % str(self.landing_time))
            output.write('Sortie Duration: %s\n' % self.flight_time)
            output.write('Autoland: %s, %s\n' % (self.autoland, self.land_direction))
            output.write('Climbout Distance: %d meters\n' % self.climbout_distance)
            output.write('Egress Time: %s\n' % self.egress_time)
            output.write('Handoff Time: %s\n' % self.handoff_time)
            output.write('Time of Land command: %s\n' % str(self.land_cmd))
            output.write('Landbreak Time: %s\n' % self.landbreak_time)

            return self.param_dict

    def print_dict(self):

        # TODO: Remove or improve
        print(self.__dict__)

    def sortie_summary(self):
        """Returns a printable summary
        :return str
        """
        # TODO: Add more important fields here
        output = ''
        output += '============================\n'
        output += 'Event %d\n' % self.event_number
        output += 'Mission %d\n' % self.mission_number
        output += 'Sortie %d\n' % self.sortie_number
        output += 'UAV %d\n' % self.uav_number
        output += '- - - - - - - - - - - - - - -\n'
        output += 'Launch Time: %s\n' % self.launch_time
        output += 'Landing Time: %s\n' % self.landing_time
        output += 'Flight Time: %s\n' % self.flight_time
        output += '============================\n'

        return output

    def analyze(self, do_everything=False):
        """Tells Sortie to go through all of its methods and calculate any data that it does not already have

        The "do_everything" argument will make Sortie recalculate values that it already contains. Returns a list of of
        any methods that failed, and the associated exception message
        """
        failure_list = []
        print('Analyzing Sortie %d' % self.sortie_number)

        self.log_start_time = self.flight_data.index[0]
        self.log_end_time = self.flight_data.index[-1]

        try:
            if (self.event_number is None) or do_everything:
                self.find_numbering()
        except Exception as ex:
            failure_list.append(('find_numbering()', ex.message))

        try:
            if (self.launch_time is None) or do_everything:
                self.find_launch_time()
        except Exception as ex:
            self.query_data(['reset'])
            failure_list.append(('calculate_launch_time()', ex.message))

        try:
            if (self.landing_time is None) or do_everything:
                self.find_landing_time()
        except Exception as ex:
            self.query_data(['reset'])
            failure_list.append(('calculate_landing_time()', ex.message))

        try:
            if (self.flight_time is None) or do_everything:
                self.calculate_sortie_duration()
        except Exception as ex:
            failure_list.append(('calculate_sortie_duration()', ex.message))

        # TODO: Implement checkIfAutoLand correctly
        # try:
        #     if (self.autoland is None) or do_everything:
        #         self.checkIfAutoLand()
        # except Exception as ex:
        #     self.query_data(['reset'])
        #     failure_list.append(('checkIfAutoLand()', ex.message))

        try:
            if (self.climbout_distance is None) or do_everything:
                self.calculate_climbout_data()
        except Exception as ex:
            self.query_data(['reset'])
            failure_list.append(('calculate_climbout_data()', ex.message))

        try:
            if (self.egress_time is None) or do_everything:
                self.find_egress_time()
        except Exception as ex:
            self.query_data(['reset'])
            failure_list.append(('get_egress_time()', ex.message))

        try:
            if (self.landbreak_time is None) or do_everything:
                self.find_landbreak_time()
        except Exception as ex:
            print('Cannot get landbreak time')
            self.query_data(['reset'])
            failure_list.append(('get_landbreak_time()', ex.message))

        try:
            if (self.land_cmd_time is None) or do_everything:
                self.find_land_cmd_time()
        except Exception as ex:
            self.query_data(['reset'])
            failure_list.append(('find_land_cmd_time()', ex.message))

        try:
            if (self.climbout_time is None) or do_everything:
                self.find_climbout_time()
        except Exception as ex:
            self.query_data(['reset'])
            failure_list.append(('find_climbout_time()',ex.message))

        try:
            if (self.handoff_time is None) or do_everything:
                self.find_handoff_time()
        except Exception as ex:
            self.query_data(['reset'])
            failure_list.append(('find_handoff_time()',ex.message))

        print('- - - - - - - - - - - - - -')

        return failure_list
        # TODO: add more lines as the methods for this class are created.

    def load_variance_data(self):
        """Loads the GPS and BARO variance data from .csv files"""
        self.var_pre = pd.read_csv(self.path_dictionary['GPS-Baro-Pre'])
        self.var_post = pd.read_csv(self.path_dictionary['GPS-Baro-Post'])

    def calculate_landing_overshoot(self, show_figure=True, save_figure=True):
        """Gets the landing overshoot/undershoot of a UAV.

     Returns the offset distance in the direction of the plane's approach and the offset distance perpendicular to the
     plane's approach

     :return float,float
     """
        # TODO: make sure to change these to dynamic waypoint_data_dict values instead of hard-coded
        targlat = self.target_landing_lat
        targlng = self.target_landing_lng

        # Select end of the flight. Criteria can be improved
        # TODO: Improve selection criteria for "End of flight" (probably WP change to landing WP)
        end_data = self.flight_data[self.flight_data.GPS_Spd > 3]
        end_data = end_data[-20:]
        land_lng = end_data.GPS_Lng.values[-1]
        land_lat = end_data.GPS_Lat.values[-1]

        # Fit the last few points of the flight to a line to get heading. delta_y is the slope of the lng vs. lat line
        results = smf.ols('end_data.GPS_Lng ~ end_data.GPS_Lat', data=end_data).fit()
        # Verifies the end of flight selection, will be removed in final function
        fig = plt.figure()
        plt.scatter(end_data.GPS_Lat, end_data.GPS_Lng, label='End of flight points')
        plt.hold(True)
        plt.plot(end_data.GPS_Lat, results.fittedvalues, 'r', alpha=.9, label='Fitted heading')
        plt.scatter(targlat, targlng, color='g', label='Landing Target')
        plt.scatter(end_data.GPS_Lat.values[-1], end_data.GPS_Lng.values[-1], color='red', label='Actual Landing')
        plt.legend()
        plt.xlabel('GPS_Latitude')
        plt.ylabel('GPS_Longitude')
        plt.title('UAV Landing Accuracy')

        if save_figure:
            self.path_dictionary['landing_overshoot_graph'] = os.path.join(self.path,
                                                                           'FX%02d-M%02d-S%02d-UAV%02d_Overshoot_Graph.png' % (
                                                                           self.fx_data[0], self.fx_data[1],
                                                                           self.fx_data[2], self.fx_data[3]))
            plt.savefig(self.path_dictionary['landing_overshoot_graph'], bbox_inches='tight')

        if show_figure:
            plt.show()

        delta_y = results.params['end_data.GPS_Lat']
        th2 = np.arctan(delta_y)

        # delta_lng and delta_lat are the differences in longitude and latitude between the designated landing site and the actual UAV landing location
        delta_lng = targlng - land_lng
        delta_lat = targlat - land_lat
        th3 = np.arctan(delta_lng / delta_lat)
        th = th2 - th3

        dist = hp.distance_2GPS(land_lat, land_lng, targlat, targlng)
        vert = dist * np.cos(th)
        horiz = dist * np.sin(th)

        print('Horizontal offset: %d meters' % float(horiz))
        print('Vertical offset: %d meters' % float(vert))
        # TODO: Decide whether to store these values as instance variables
        return horiz, vert

    def assess_launch(self, show_figure=True, save_figure=True, end_of_window=None):
        """Generates plot of several aircraft parameters as it takes off. Defaults to showing and saving figure. Returns handle to graph figure

        end_of_window defines the number of seconds past launch to show on the x axis. If not specified, it will default
        to the handoff time. If handoff time hasn't been calculated, the max x of the graph is set to 30 seconds after
        launch.

        Plot information:

        X Axis: Time

        Y Axis: Ground Speed
                Forward Acceleration
                GPS Altitude
                Throttle %
                Baro Altitude

        """

        FXdata = self.fx_data

        # Determine analysis start_time as preceding the launch time (as determined by timeOfLaunch())

        ## Plot information
        plt.close('all')

        fig, ax1 = plt.subplots()
        plt.title('Auto-Launch FX%d, Mission %d, Sortie %d, UAV %d' % (self.event_number, self.mission_number, self.sortie_number, self.uav_number), fontweight='bold')

        if self.handoff_time is None:
            handoff = self.launch_time + datetime.timedelta(seconds=30)
        else:
            handoff = self.handoff_time

        if end_of_window is None:
            end_of_window = handoff
        else:
            end_of_window = self.launch_time + datetime.timedelta(seconds=end_of_window)

        cut_data = self.flight_data[self.launch_time - datetime.timedelta(seconds=5):end_of_window]

        ax1.plot(cut_data.index, cut_data.GPS_Spd, color='r', label='Ground speed [m/s]')
        plt.hold('on')
        ax1.plot(cut_data.index, cut_data.ARSP_Airspeed, color='k', label='Airspeed [m/s]')
        ax1.plot(cut_data.index, cut_data.IMU_AccZ, color='k', linestyle='-.', label='Vertical Acceleration [m/s^2]')
        plt.plot(cut_data.index, cut_data.IMU_AccX, color='m', label='Forward acceleration [m/s^2]')
        ax1.set_xlabel('Actual Time [local]', fontweight='bold')
        ax1.set_ylabel('Gnd Speed [m/s], Forward acc [m/s^2]', fontweight='bold')

        ax2 = ax1.twinx()
        ax2.plot(cut_data.index, cut_data.CTUN_ThrOut, color='g', label='Throttle [%]')
        ax2.plot(cut_data.index, map(lambda x: x - cut_data.GPS_Alt[0], cut_data.GPS_Alt), color='b',
                 label='GPS altitude [m AGL]')
        ax2.plot(cut_data.index, cut_data.BARO_Alt, color='b', linestyle='-.', label='BARO altitude [m AGL]')
        ax2.set_ylim([-10, 110])
        ax2.set_ylabel('Throttle [%], GPS Alt [m AGL], BARO Alt [m AGL]', rotation=-90, fontweight='bold')

        plt.plot(figsize=(15, 10))

        # Annotate the figure
        ax1.legend(loc='best')
        ax2.legend(loc=(0.012, 0.7))
        plt.grid(b=True, which='major', color='b', linestyle=':')

        # Save PNG
        if save_figure:
            self.path_dictionary['launch_graph'] = os.path.join(self.path,
                                                                 'FX%02d-M%02d-S%02d-UAV%02d_autolaunch.png' % (
                                                                 FXdata[0], FXdata[1], FXdata[2], FXdata[3]))
            plt.savefig(self.path_dictionary['launch_graph'], bbox_inches='tight', figsize=(8, 6))

        # Show figures
        if show_figure:
            plt.show()

        return fig

    def query_data(self, *args):
        """Provides an interface for querying the Sortie.flight_data field. It functions as a partial abstraction for
        Dataframe selection.

        Input should be N lists separated by commas

        Query Types:
        Note in these examples anything in all caps needs to be replaced with actual syntax. Choose only 1 operator per query.

        Three fields:
        ['FLIGHT_DATA FIELD', > / < / == , NUMBER]

        Combined into one:
        ['FLIGHT_DATA FIELD < / > / == NUMBER]

        Specifying multiple queryies in this way functions as an 'AND' query.
        Appending 'or' as the first field in either of the above lists will combine with previous queries as an 'OR' join.
        e.g.:
            Sortie.query_data(['GPS_Spd > 18'],['or','GPS_Spd < 10']) will return a Dataframe where all rows have GPS
            speed greater than 18 m/s or less than 10 m/s

        Index Query (useful for selecting regions of the Dataframe according to Timestamp)
        ['index', 'SORTIE_INSTANCE_VARIABLE_1', 'SORTIE_INSTANCE_VARIABLE_2']

        Calling Sortie.query_data(['reset']) will clear any previously called queries.

        The queried Dataframe resides in Sortie.cut_data

        """
        # TODO: Sanitize input -- This function uses eval
        full_query = None
        query_list = []
        for query_txt in args:
            if query_txt[0] == 'reset':
                self.cut_data = self.flight_data.copy()
                return self.cut_data

            if query_txt[0] == 'or':
                if len(query_txt) == 4:
                    fq = 'self.flight_data[self.flight_data.%s %s %s]' % (query_txt[1], query_txt[2], query_txt[2])
                if len(query_txt) == 2:
                    fq = 'self.flight_data[self.flight_data.%s]' % query_txt[1]
                else:
                    print("'Or' Query with length %d is not supported" % len(query_txt))

                new_cut = eval(fq)
                combined_df = self.cut_data.copy()
                combined_df.append(new_cut)
                combined_df["index"] = combined_df.index
                combined_df.drop_duplicates(cols='index', take_last=True, inplace=True)
                del combined_df["index"]

                self.cut_data = combined_df.sort_index()
                continue

            if query_txt[0] == 'index':
                if len(query_txt) == 3:
                    selection_range = 'self.%s:self.%s' % (query_txt[1], query_txt[2])
                full_query = 'self.cut_data[%s]' % selection_range
            elif len(query_txt) == 3:
                full_query = 'self.cut_data[self.cut_data.%s %s %f ]' % (query_txt[0], query_txt[1], query_txt[2])
            elif len(query_txt) == 1:
                full_query = 'self.cut_data[self.cut_data.%s ]' % query_txt[0]
            else:
                print('Cannot Execute Query. Query specifications must be 1 or 3 strings long. This query has %d strings' % len(query_txt))
                return None
            if full_query is not None:
                cut_data = eval(full_query)
                full_query = None
            self.cut_data = cut_data

        return self.cut_data

    def select_field(self, field, axis=None):
        """Sets the specified field of the Dataframe to the specified axis, and sets the associated axis label."""
        selected_data = getattr(self.cut_data.dropna(), field)
        if axis == 'x':
            self.x_data = selected_data
            for key,label in self.label_dict.iteritems():
                if field == key:
                    self.x_label = label
                    break
                else:
                    self.x_label = field
        if axis == 'y':
            self.y_data = selected_data
            for key,label in self.label_dict.iteritems():
                if field == key:
                    self.y_label = label
                    break
                else:
                    self.y_label = field

        if axis == 'z':
            self.z_data = selected_data
            for key,label in self.label_dict.iteritems():
                if field == key:
                    self.z_label = label
                    break
                else:
                    self.z_label = field
        return selected_data

    def make_sparse(self, factor):
        """Takes the cut_data Dataframe and keeps only 1 in FACTOR rows"""
        ind = self.cut_data.index
        new_indices = []
        for ii in xrange(len(ind)):
            if ii % factor == 0:
                new_indices.append(ind[ii])
        self.cut_data = self.cut_data[self.cut_data.index.isin(new_indices)]

    def plot3d(self, x=None, y=None, z=None):
        """Test function for 3d plots"""
        if x is not None:
            self.select_field(x, 'x')
        if y is not None:
            self.select_field(y, 'y')
        if z is not None:
            self.select_field(z,'z')

        x = self.x_data
        y = self.y_data
        z = self.z_data

        fig = plt.figure(1)
        ax = fig.add_subplot(111,projection='3d')
        ax.plot(x,y,z)
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        ax.set_zlabel(self.z_label)

    def plot(self, x=None, y=None, line=True, show=False, ax=None, save_name=None, plot_type=None, hold=True, new_y=False):
        """Plots the specified fields of the sortie data.
        Plots Sortie.x_data vs. Sortie.y_data. These values can be set with Sortie.select_field.
        Sortie.select_field selects data from Sortie.cut_data, so you can you Sortie.query_data to select data first.

        Parameters:

        line: Boolean, where False will graph a scatter plot and True will graph a line plot
        hold: If hold is set to true, the points will be plotted, the plot will be held, and the plot will NOT be shown
        fg: Figure number
        color: Can either specify color of all the points or, if line is false, it can be a list of colors, one entry for each point
        save_name: If specified, will save the generated image as [save_name].png
        plot_type: If specified, the resulting saved figure's path will be saved to the path dictionary as plot_type.
        Otherwise, the path will be saved in the path dictionary as type 'custom_fig'

        The pyplot axes object of the plot is store as Sortie.axes, and the pyplot figure object is stored as Sortie.figure.
        These can be used to modify the plot.
        """
        if x is not None:
            self.select_field(x,'x')
        if y is not None:
            self.select_field(y,'y')

        x = self.x_data
        y = self.y_data

        # Sets x/y axes to show all data
        if self.x_min is None:
            self.x_min = min(x)
        elif min(x) < self.x_min:
            self.x_min = min(x)

        if self.x_max is None:
            self.x_max = max(x)
        elif max(x) > self.x_max:
            self.x_max = max(x)

        if self.y_min is None:
            self.y_min = min(y)
        elif min(y) < self.y_min:
            self.y_min = min(y)

        if self.y_max is None:
            self.y_max = max(y)
        elif max(y) > self.y_max:
            self.y_max = max(y)

        plt.hold(hold)
        if new_y is True:
          ax = plt.twinx()
        elif ax is None:
            fig = plt.figure(1)
            ax = fig.add_subplot(111)
        plt.rc('lines', linewidth=1)
        # TODO: Figure out line color if the user elects to use a new y axis (currently the color cycle resets if the
        # new_y flag is used
        if line is False:
            ax.scatter(x,y,label='UAV %s %s' % (self.uav_number, self.y_label))
        else:
            ax.plot(x,y,label='UAV %s %s' % (self.uav_number, self.y_label))

        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)

        ax.set_xlim(self.x_min, self.x_max)
        ax.set_ylim(self.y_min, self.y_max)

        if save_name is not None:
            if save_name is True:
                print('saving')
                self.save_plot()
            elif plot_type is not None:
                print('saving')
                self.save_plot(save_name,plot_type)
            elif plot_type is None:
                print('saving')
                self.save_plot(save_name)

        # TODO: Figure out legend placement
        plt.legend()

        # TODO: Figure out titling scheme that is valid for plots of more than one line
        if not new_y:
            plt.title('%s vs. %s' % (self.x_label, self.y_label))
        if show:
            plt.show()

    def save_plot(self, name='custom_figure.png', type_='custom_fig'):
        """Saves the current custom plot in the Sortie's folder with a name of "name" """
        save_path = os.path.join(self.path, name)
        self.path_dictionary[type_] = [save_path]
        plt.savefig(save_path)

    def assess_sortie_wp_exec(self, show_figure=True, save_figure=True):
        """Generates plot of the waypoint commands given vs. time for a given mission
        Plot Information:

        X Axis: Time

        Y Axis 1: Waypoint #
        Y Axis 2: Mode #
        """

        # Trim to valid time interval
        df_trunc = self.flight_data[self.launch_time:self.landing_time]

        # Prepare the figure
        plt.close('all')

        fig, ax1 = plt.subplots(figsize=(8, 6), facecolor='w', edgecolor='k', dpi=120)
        # plt.figure( figsize=(8,6), facecolor='w', edgecolor='k', dpi=120 )

        # Plot the WP evolution
        ax1.plot(df_trunc.index, df_trunc['CMD_CNum'].interpolate(), linewidth=2, label='WP #')
        plt.hold('on')
        ax1.set_xlabel('Actual Time [local]', fontweight='bold')
        ax1.set_ylabel('Mission WP #', fontweight='bold')
        ax1.set_ylim([0, 26])

        ax2 = ax1.twinx()
        ax2.plot(df_trunc.index, df_trunc['MODE_Mode'].interpolate(), linewidth=2, label='MODE #', color='r',
                 linestyle='-.')
        ax2.set_ylim([0, 17])
        ax2.set_ylabel('UAV MODE #', rotation=-90, fontweight='bold', labelpad=15)

        plt.plot(figsize=(15, 10))

        # Annotate the figure
        ax1.legend(loc=2)
        ax2.legend(loc=1)
        # ax2.legend(loc=(0.012,0.7))
        plt.grid(b=True, which='major', color='b', linestyle=':')

        # Annotate
        # plt.xlabel('Time (GPS)', fontweight='bold')
        # plt.ylabel('Mission WP #', fontweight='bold')
        plt.title('Mission Execution (FX%02d-M%02d-S%02d-UAV%02d)' % (
            self.fx_data[0], self.fx_data[1], self.fx_data[2], self.fx_data[3]), fontweight='bold')

        # Save PNG
        if save_figure:
            self.path_dictionary['waypoint_graph'] = os.path.join(self.path,
                                                                  'FX%02d-M%02d-S%02d-UAV%02d_missionWPExec.png' % (
                                                                      self.fx_data[0], self.fx_data[1], self.fx_data[2],
                                                                      self.fx_data[3]))
        plt.savefig(self.path_dictionary['waypoint_graph'], bbox_inches='tight')

        # Show figures
        if show_figure:
            plt.show()
        return fig

    def dump_data(self):
        """In case it is decided that holding all the .csv files in memory requires too much memory, this will delete
        the flight_data and cut_data Dataframes. After using this, the Sortie object will no longer have any raw data
        but the existing fields will remain valid
        """
        self.flight_data = None
        self.cut_data = None
