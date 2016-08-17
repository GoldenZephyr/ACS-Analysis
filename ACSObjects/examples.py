
# ACSObjects imports

from ACSObjects.Event import Event
from ACSObjects.Mission import Mission
from ACSObjects.Sortie import Sortie

# Imports used in example functions
import datetime
import matplotlib.pyplot as plt
import statsmodels.api as sm
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('inputpath', type=str, help='Path to Event directory')
args = parser.parse_args()



# Example 1: Graph values relevant to analyzing launch success
# Demonstrates sortie-level capability

def assess_launch(sortie):
        """Generates plot of several aircraft parameters as it takes off. Defaults to showing and saving figure. Returns handle to graph figure

        Plot information:

        X Axis: Time

        Y Axis: Ground Speed
                Forward Acceleration
                GPS Altitude
                Throttle %
                Baro Altitude

        """

        ## Plot information
        plt.close('all')

        fig, ax1 = plt.subplots()
        plt.title('Auto-Launch FX%d, Mission %d, Sortie %d' % (sortie.event_number, sortie.mission_number, sortie.sortie_number), fontweight='bold')

        if sortie.handoff_time is None:
            handoff = sortie.launch_time + datetime.timedelta(seconds=30)
        else:
            handoff = sortie.handoff_time

        # Cut the end of the x axis to the 'handoff' time
        cut_data = sortie.flight_data[sortie.launch_time - datetime.timedelta(seconds=5):handoff]

        # Plot GPS_Spd, IMU Acceleration, GPS and BARO Alt, and Throttle output
        ax1.plot(cut_data.index, cut_data.GPS_Spd, color='r', label='Ground speed [m/s]')
        plt.hold('on')
        plt.plot(cut_data.index, cut_data.IMU_AccX, color='m', label='Forward acceleration [m/s^2]')
        ax1.set_xlabel('Actual Time [local]', fontweight='bold')
        ax1.set_ylabel('Gnd Speed [m/s], Forward acc [m/s^2]', fontweight='bold')

        ax2 = ax1.twinx()
        ax2.plot(cut_data.index, cut_data.CTUN_ThrOut, color='g', label='Throttle [%]')
        ax2.plot(cut_data.index, cut_data.GPS_Alt, color='b',
                 label='GPS altitude [m AGL]')
        ax2.plot(cut_data.index, cut_data.BARO_Alt, color='b', linestyle='-.', label='BARO altitude [m AGL]')
        ax2.set_ylim([-10, 110])
        ax2.set_ylabel('Throttle [%], GPS Alt [m AGL], BARO Alt [m AGL]', rotation=-90, fontweight='bold')

        plt.plot(figsize=(15, 10))

        # Annotate the figure
        ax1.legend(loc='best')
        ax2.legend(loc=(0.012, 0.7))
        plt.grid(b=True, which='major', color='b', linestyle=':')

        plt.show()

def assess_alt_separation(mission):
    """Generates a plot showing altitude separation of the UAVs"""
    print(mission.sortie_list[1].handoff_time)
    mission.query_sorties(['index', 'handoff_time', 'egress_time'])

    plt.figure()
    plt.hold(True)
    for sortie in mission.sortie_list.itervalues():
        x_data = sortie.cut_data.index
        y_data = sortie.cut_data.GPS_Alt

        fitx = sm.add_constant(range(len(x_data)))
        model = sm.OLS(y_data,fitx)
        results = model.fit()

        plt.plot(x_data,y_data,color='b')
        plt.plot(x_data,results.fittedvalues,color='r')
    plt.show()

def mission_plot_demo(mission):

    # Plots data from all Sorties in a Mission. index is the timestamps of the data.
    mission.plot('index',['GPS_Alt','GPS_Spd','BARO_Alt'],stacked=True)

if __name__ == '__main__':

    my_event = Event(args.inputpath)
    my_event.analyze()

    # If used with the NPS FX 23 data, mission_list[23] holds the 30-plane mission data. Otherwise loads the first mission.
    try:
        my_mission = my_event.mission_list[23]
    except:
        my_mission = my_event.mission_list[1]

    my_sortie = my_mission.sortie_list[1]

    print(my_sortie.handoff_time)

    assess_launch(my_sortie)

    assess_alt_separation(my_mission)

    mission_plot_demo(my_mission)
