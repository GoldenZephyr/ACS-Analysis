from ACSObjects.abstract_class import AbstractLevel
from ACSObjects.Sortie import Sortie
import datetime
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import string
from plot_funcs import div_plot_setup

class Mission(AbstractLevel):
    """Object to represent Mission level of hierarchy

    A "Mission" is the set of sorties that were flown simultaneously
    """

    pattern_dictionary = AbstractLevel.pattern_dictionary.copy()
    """The pattern dictionary contains types as files as keys and search expressions as values.
    Each key corresponds to a type of file/folder related to the Mission. This is used by Mission.find_data()
    to load relevant files. This dictionary extends the one defined by AbstractLevel.

    Default values include:

   sortie_folder : Sortie*\n
   concurrent_sorties : FX*concurrent_sorties.png
    """
    pattern_dictionary['sortie_folder'] = 'Sortie*'
    pattern_dictionary['concurrent_sorties'] = 'FX*concurrent_sorties.png'

    def __init__(self, path=''):
        AbstractLevel.__init__(self)
        self.path = path
        '''Path to the Mission folder'''

        self.sortie_list = {}
        '''A dictionary of sorties keyed by Sortie number. The object associated with Sortie 1 will be in sortie_list[1].'''

        self.uav_list = {}
        '''A dictionary of sorties keyed by UAV number. The object associated with Sortie2-UAV06 will be in uav_list[6].'''

        self.num_sorties = None
        '''Number of sorties in the Mission'''

        self.mission_duration = None
        '''Duration of the Mission, launch of first plane to landing of last'''

        self.total_airtime = None
        '''Total UAV-flighthours of the mission'''

        self.mean_time_btw_launch = None
        '''A datetime object representing the mean time between sortie launches'''

        self.mission_number = None
        '''The number of this mission'''

        self.launch_time_list = None
        '''A list of launch times of the Sorties. Each item is a Timestamp object'''

        self.launch_time_dict = None
        '''A dictionary of launch times fo the Sorties. Each key is a Sortie number. Each value is a Timestamp object.'''

        self.landing_time_list = None
        '''A list of landing times of the Sorties. Each item is a Timestamp object'''

        self.landing_time_dict = None
        '''A dictionary of landing times fo the Sorties. Each key is a Sortie number. Each value is a Timestamp object.'''

        self.overlap_time = None
        '''The time from last launch to first landing'''

        if self.path != '':
            self.find_data()
            if 'sortie_folder' in self.path_dictionary.keys():
                for sortie_path in self.path_dictionary['sortie_folder']:
                    temp_sortie = Sortie(sortie_path)
                    self.sortie_list[temp_sortie.sortie_number] = temp_sortie
                    self.num_sorties = len(self.sortie_list)

            self.find_numbering()

    def find_numbering(self):
        """Identifies Mission/Event number and date from the path.
        Returns event number and mission number
        """
        tmp = string.split(self.path, '/')

        for i in tmp:
            indfx = string.find(i, 'Event')
            if indfx != -1:
                self.event_number = int(filter(str.isdigit, i))

            indm = string.find(i, 'Mission')
            if indm != -1:
                self.mission_number = int(filter(str.isdigit, i))

        self.date = datetime.datetime.strptime(self.path[0:-1].split('/')[-2], '%Y-%m-%d')

        return self.event_number, self.mission_number

    def get_sortie_times(self):
        """Gets dictionaries and lists of launch and landing times"""

        # TODO: Decide whether to get times of other occurrences, such as egress, landbreak, etc.
        takeoff_dict, takeoff_list = self.call_sortie_function('find_launch_time', [])
        takeoff_list = [time for time in takeoff_list if not isinstance(time,Exception) ]
        takeoff_dict = {key: (val if not isinstance(val, Exception) else None) for key, val in takeoff_dict.iteritems()}
        self.launch_time_dict = takeoff_dict
        self.launch_time_list = takeoff_list

        landing_dict, landing_list = self.call_sortie_function('find_landing_time', [])
        landing_list = [time for time in landing_list if not isinstance(time, Exception)]
        landing_dict = {key: (val if not isinstance(val, Exception) else None)for key, val in landing_dict.iteritems() }
        self.landing_time_dict = landing_dict
        self.landing_time_list = landing_list
        return self.landing_time_dict, self.landing_time_list

    def call_sortie_function(self, method, arg_list=None, skip_error=None):
        """Calls the method specified as a string by 'method' for each sortie in the mission.
        The the arg_list variable will be fed as the argument to all Sortie methods.

        The optional skip_error argument will not call sorties who have a None value in the skip_error dict

        Returns response_dict and response_list

        response_dict is a dictionary of outputs from the called sortie functions, with the key corresponding to the Sortie number.

        response_list is a list of outputs from the called sortie functions, in the order they were called.
        Not reliably ordered, but more intuitive to loop through for operations where order doesn't matter.
        """
        if arg_list is None:
            arg_list = []
        response_dict = {}
        response_list = []
        for sortie_num, sortie in self.sortie_list.iteritems():
            if skip_error is None or skip_error[sortie_num] is not None:
                built_method = getattr(sortie, method)
                try:
                    response = built_method(*arg_list)
                except Exception as ex:
                    print(ex)
                    response = ex
                response_dict[sortie_num] = response
                response_list.append(response)
        plt.show()
        return response_dict, response_list

    def query_sorties(self,query):
        """Calls the given query on all Sorties in the Mission. (see Sortie.query_data for information on query syntax"""
        if isinstance(query[0], basestring):
            query = [query]
        self.call_sortie_function('query_data',query)

    def get_sortie_variable(self, variable):
        """Gets the instance variable specified by 'variable' for each sortie in the mission
        Returns response_dict and response_list

        response_dict is a dictionary of outputs from the called sortie variables, with the key corresponding to the Sortie number.

        response_list is a list of outputs from the called sortie variables, in the order they were called.
        Not reliably ordered, but more intuitive to loop through for operations where order doesn't matter.
        """
        response_dict = {}
        response_list = []
        for sortie_num, sortie in self.sortie_list.iteritems():
            response = getattr(sortie, variable)
            response_dict[sortie_num] = response
            response_list.append(response)

        return response_dict, response_list

    def single_plot(self,x,y,show=False,save_name=None):
        """Plots the fields specified as strings by x and y for each Sortie on the same plot"""
        self.call_sortie_function('select_field', ['%s' % x, 'x'])
        self.call_sortie_function('select_field', ['%s' % y, 'y'])
        self.call_sortie_function('plot')
        if save_name is not None:
            plt.savefig(save_name)
        if show:
            plt.show()

    def plot3d(self, x, y, z, scatter=False):
        """Testing 3d plot capabilities"""

        fig = plt.figure(1)
        ax = fig.add_subplot(111,projection='3d')
        plt.hold(True)
        for sortie in self.sortie_list.itervalues():
            sortie.make_sparse(20)
            xdat = sortie.select_field(x, 'x')
            ydat = sortie.select_field(y, 'y')
            zdat = sortie.select_field(z, 'z')
            count = 0
            if not scatter:
                ax.plot(xdat, ydat, zdat, label='UAV %d' % sortie.uav_number)
            else:
                ax.scatter(xdat, ydat, zdat, label='UAV %d' % sortie.uav_number)
            if count == 0:
                ax.set_xlabel(sortie.x_label)
                ax.set_ylabel(sortie.y_label)
                ax.set_zlabel(sortie.z_label)
                count += 1
        plt.legend()
        plt.show()

    def plot(self, x, y, show=True, save=False, stacked=True, rows=8):
        """Plots data from all sorties in the Mission. Each sortie gets its own subplot.

        x: A string specifying the field to use as the x data (use 'index' for timestamps).
        y: A string or list of strings specifying the field(s) to use as y data.
        stacked: If set to True, it will stack the subplots on top of each other in one column, spanning multiple figures
                if necessary.
        rows: If stacked is False, specifies number of rows per column. If stacked is True, specifies number of rows
              per figure.
        """

        # TODO: Add more colors
        color = {1:'r',2:'b',3:'g', 4: 'c', 5: 'm', 6: 'y', 7: 'k'}
        line_list = []
        legend_labels = []
        plt.close('all')
        if isinstance(x, basestring):
            x = [x]
        if isinstance(y, basestring):
            y = [y]

        xmin=[None] * len(y)
        xmax=[None] * len(y)
        ymin=[None] * len(y)
        ymax=[None] * len(y)
        title_str = 'FX %d Mission %d' % (self.event_number, self.mission_number)
        for value in y:
            title_str += ', %s' % value
        n_ex_lines = len(y) - 1
        axlist, label_list = div_plot_setup(self.num_sorties, stacked=stacked, n_extra_lines=n_ex_lines, rows=8)
        real_labels = {}
        for ii in range(len(self.sortie_list)):
            current_sortie = self.sortie_list[ii+1]
            for jj in range(len(y)):

                # Sets up axis labels and correct data for each Sortie
                current_sortie.select_field(x[0], 'x')
                current_sortie.select_field(y[jj], 'y')
                if ii == 0:
                    real_labels[jj] = (current_sortie.x_label, current_sortie.y_label)

                x_data = current_sortie.x_data
                y_data = current_sortie.y_data

                if (xmin[jj] is None):
                    xmin[jj] = min(x_data)
                    print('xmin set to:')
                    print(xmin[jj])
                elif (min(x_data) < xmin[jj]):
                    xmin[jj] = min(x_data)
                    print('xmin set to:')
                    print(xmin[jj])

                if (xmax[jj] is None):
                    xmax[jj] = max(x_data)
                    print('xmax set to:')
                    print(xmax[jj])
                elif (max(x_data) > xmax[jj]):
                    xmax[jj] = max(x_data)
                    print('xmax set to:')
                    print(xmax[jj])

                if (ymin[jj] is None):
                    ymin[jj] = min(y_data)
                    print('ymin set to:')
                    print(ymin[jj])
                elif (min(y_data) < ymin[jj]):
                    ymin[jj] = min(y_data)
                    print('ymin set to:')
                    print(ymin[jj])

                if (ymax[jj] is None):
                    ymax[jj] = max(y_data)
                    print('ymax set to:')
                    print(ymax[jj])
                elif (max(y_data) > ymax[jj]):
                    ymax[jj] = max(y_data)
                    print('ymax set to:')
                    print(ymax[jj])

                line_obj = axlist[jj][ii].plot(x_data, y_data, color=color[jj+1])
                if ii == 0:
                    line_list.append(line_obj[0])
                    legend_labels.append(real_labels[jj][1])
                    axlist[jj][ii].legend(line_list,legend_labels, loc=3,bbox_to_anchor=[0,1,.5,.5])
                axlist[jj][ii].set_title('Sortie %d' % current_sortie.sortie_number, fontsize=8)
                if stacked:
                    if ii % rows == 0:
                        axlist[jj][ii].legend(line_list,legend_labels,loc=3,bbox_to_anchor=[0,1,.5,.5])

                # TODO: find way to set title on first figure that is independent of figure number
                if ii == 0:
                    plt.figure(1).suptitle(title_str)

        for ii in range(len(self.sortie_list)):
            for jj in range(len(y)):
                axlist[jj][ii].set_xlim(xmin[jj], xmax[jj])
                axlist[jj][ii].set_ylim(ymin[jj], ymax[jj])

        for key in label_list:
            for label in label_list[key]:
                label.set_ylabel(real_labels[key][1], rotation=90, fontsize=10)
                label.set_ylim(ymin[key], ymax[key])
        if show:
            plt.show()
        # TODO: implement save feature.

    def assess_baro_alt(self, show_figure=False, save_figure=True):
        """Generate an altitude plot showing sortie in the mission

        Calls the assess_baro_alt method of each sortie in the mission, and then shows and/or saves the figure
        """
        print('Landing time dict: %s\n\n\n\n\n\n' % self.landing_time_dict)
        responses = self.call_sortie_function('assess_baro_alt', [], skip_error=self.landing_time_dict)
        if save_figure:
            print('saving')
            save_destination = os.path.join(self.path,'FX%02d-M%02d_Altitude_Graph.png' % (self.event_number, self.mission_number))
            plt.savefig(save_destination)
            self.path_dictionary['altitude_graph'] = save_destination
        if show_figure:
            plt.show()

    def analyze_sorties(self):
        """Makes all the sorties in the Mission run their analysis methods"""
        print('Analyzing Mission %d' % self.mission_number)
        print('=============================')
        responses = self.call_sortie_function('analyze',[])
        self.get_sortie_times()

    def analyze(self,show_figures=False, save_figures=False):
        """Calls all mission analysis methods
        If show_figure is True, it will show every graph that is generated. Not recommended unless there is a specific reason
        """
        # TODO: Add other analysis methods here
        self.analyze_sorties()
        self.get_sortie_times()
        self.assess_mission_times()
        self.num_sorties = len(self.sortie_list)
        self.total_airtime = self.calculate_total_airtime()
        if len(self.sortie_list) > 1:
            self.assess_launch_separation()

    def make_wp_files(self):
        """Makes the .wp files for each Sortie in the Mission"""
        self.call_sortie_function('generate_mission_file')

    def make_parm_files(self):
        """Makes the .parm files for each Sortie in the Mission"""
        self.call_sortie_function('generate_parm')

    def assess_concurrence(self, show_figure=True, save_figure=False):
        """Generates a plot of number of UAVs aloft vs. time"""

        takeoff_times = self.launch_time_list

        landing_times = self.landing_time_list

        mat_takeoff_times = mdates.date2num(takeoff_times)
        mat_landing_times = mdates.date2num(landing_times)

        # Padding sets the whitespace before and after the histogram. Currently set to 5 minutes. mat_takeoff_times is a
        # list of floats. Each float represents the takeoff time in days since 0001-01-01 00:00:00 UTC plus one.
        padding = 1.0/(24*24.0)

        times = np.linspace(min(mat_takeoff_times) - padding, max(mat_landing_times) + padding, 7000)
        plot_times = mdates.num2date(times)
        drones_aloft = np.zeros(len(times))

        # These nested loops set up the graph.The concurrent sorties graph is built as a histogram with several thousand
        # bins. Each bin has a value that corresponds to the number of UAVs flying at that time.
        for time in mat_takeoff_times:
            for jj in xrange(len(times)):
                if times[jj] >= time:
                    for ii in xrange(jj, len(drones_aloft)):
                        drones_aloft[ii] = drones_aloft[ii] + 1
                    break

        for time in mat_landing_times:
            for jj in xrange(len(times)):
                if times[jj] >= time:
                    for ii in xrange(jj, len(drones_aloft)):
                        drones_aloft[ii] = drones_aloft[ii] - 1
                    break

        # Calculate the width of each histogram bar
        width = ((plot_times[-1] - plot_times[0]).total_seconds())/(86400*len(plot_times))

        plt.figure(figsize=(11, 8))
        plt.bar(plot_times, drones_aloft, width=width, linewidth=0)
        plt.xlim(plot_times[0], plot_times[-1])
        plt.xlabel('Time of Day')
        plt.ylabel('Number of Aircraft Aloft')
        plt.title('Graph of Concurrent Sorties - %s-%s-%s' % (takeoff_times[0].month, takeoff_times[0].day, takeoff_times[0].year))
        if save_figure:
            save_path = os.path.join(self.path,'FX%02d-M%02d_concurrent_sorties.png' % (self.event_number, self.mission_number))
            self.path_dictionary['concurrent_sorties'] = save_path
            plt.savefig(save_path)

        if show_figure:
            plt.show()

    def assess_launch_separation(self):
        """Calculates the mean time between launches. Returns timedelta object."""
        launch_times = sorted(self.launch_time_list)
        tdeltas = np.diff(launch_times)
        self.launch_separation = tdeltas
        self.mean_time_btw_launch = sum(abs(tdeltas),datetime.timedelta()) / len(tdeltas)
        return self.mean_time_btw_launch

    def assess_mission_times(self):
        """Calculate the mission duration and the overlap duration.
        Returns Mission Duration, Overlap Duration.
        Mission Duration: Time from first launch to last landing
        Overlap Duration: Time from last launch to first landing
        """
        landing_time_list_copy = list(self.landing_time_list)
        launch_time_list_copy = list(self.launch_time_list)
        while 1:
            if min(landing_time_list_copy) < max(launch_time_list_copy):
                landing_time_list_copy.remove(min(landing_time_list_copy))
            else:
                break
        self.overlap_time = min(landing_time_list_copy) - max(launch_time_list_copy)
        self.flight_time = max(self.landing_time_list) - min(self.launch_time_list)
        self.mission_duration = self.flight_time

        return self.mission_duration, self.overlap_time

    def calculate_total_airtime(self):
        """Calculates the total UAV-flighthours"""
        time_counter = datetime.timedelta(seconds=0)
        for sortie in self.sortie_list.itervalues():
            time_counter += sortie.flight_time
        self.total_airtime = time_counter
        return self.total_airtime

    def summarize(self, write_to_file=True):
        """Calls Mission.analyze and then prints out Mission Summary data in a text file.
        """
        self.analyze()
        self.param_dict = self.__dict__
        summary_file_name = os.path.join(self.path, 'FX%02d-M%02d_text_summary.txt' % (self.event_number, self.mission_number))
        self.path_dictionary['summary'] = summary_file_name
        with open(summary_file_name, 'w') as output:
            output.write('Summary of Mission. Generated by Mission.summarize()\n')
            output.write('Event: %d\nMission: %d\nDate: %s\n=============================\n' % (self.event_number, self.mission_number, self.date))
            output.write('Mission Duration: %s\n' % self.flight_time)
            output.write('Mission Overlap: %s\n' % self.overlap_time)
            output.write('Mean time between launches: %s\n' % self.mean_time_btw_launch)
