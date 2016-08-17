import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os

def assess_concurrence(mission, show_figure=True, save_figure=False):
        """Generates a plot of number of UAVs aloft vs. time"""

        takeoff_times = mission.launch_time_list

        landing_times = mission.landing_time_list

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
            save_path = os.path.join(mission.path,'FX%02d-M%02d_concurrent_sorties.png' % (mission.event_number, mission.mission_number))
            mission.path_dictionary['concurrent_sorties'] = save_path
            plt.savefig(save_path)

        if show_figure:
            plt.show()