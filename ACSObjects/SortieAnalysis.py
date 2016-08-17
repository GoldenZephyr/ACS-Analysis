import matplotlib.pyplot as plt
import datetime
import os

def assess_launch(sortie, show_figure=True, save_figure=True, end_of_window=None):
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

        FXdata = sortie.fx_data

        # Determine analysis start_time as preceding the launch time (as determined by timeOfLaunch())

        ## Plot information
        plt.close('all')

        fig, ax1 = plt.subplots()
        plt.title('Auto-Launch FX%d, Mission %d, Sortie %d' % (FXdata[0], FXdata[1], FXdata[2]), fontweight='bold')

        if sortie.handoff_time is None:
            handoff = sortie.launch_time + datetime.timedelta(seconds=30)
        else:
            handoff = sortie.handoff_time

        if end_of_window is None:
            end_of_window = handoff
        else:
            end_of_window = sortie.launch_time + datetime.timedelta(seconds=end_of_window)

        cut_data = sortie.flight_data[sortie.launch_time - datetime.timedelta(seconds=5):end_of_window]

        ax1.plot(cut_data.index, cut_data.GPS_Spd, color='r', label='Ground speed [m/s]')
        plt.hold('on')
        ax1.plot(cut_data.index, cut_data.ARSP_Airspeed, color='k', label='Airspeed [m/s]')
        ax1.plot(cut_data.index, cut_data.IMU_AccZ, color='k', linestyle='-.', label='Vertical Acceleration [m/s^2]')

        # Time that is considered to be launch
        plt.axvline(sortie.launch_time)

        # Error bounds on actual launch (error stemming from low recorded upate rate
        plt.axvline(sortie.launch_time - datetime.timedelta(milliseconds=400), color='r')
        plt.axvline(sortie.launch_time + datetime.timedelta(milliseconds=400), color='r')

        # Time that the motor should turn on
        plt.axvline(sortie.launch_time + datetime.timedelta(milliseconds=700))

        # Error bounds on when motor should turn on
        plt.axvline(sortie.launch_time + datetime.timedelta(milliseconds=1100), color='g')
        plt.axvline(sortie.launch_time + datetime.timedelta(milliseconds=300), color='g')

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
            sortie.path_dictionary['launch_graph'] = os.path.join(sortie.path,
                                                                 'FX%02d-M%02d-S%02d-UAV%02d_autolaunch.png' % (
                                                                 FXdata[0], FXdata[1], FXdata[2], FXdata[3]))
            plt.savefig(sortie.path_dictionary['launch_graph'], bbox_inches='tight', figsize=(8, 6))

        # Show figures
        if show_figure:
            plt.show()

        return fig

def assess_wp_exec(sortie, show_figure=True, save_figure=True):
        """Generates plot of the waypoint commands given vs. time for a given mission
        Plot Information:

        X Axis: Time

        Y Axis 1: Waypoint #
        Y Axis 2: Mode #
        """

        # Trim to valid time interval
        df_trunc = sortie.flight_data[sortie.launch_time:sortie.landing_time]

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
            sortie.fx_data[0], sortie.fx_data[1], sortie.fx_data[2], sortie.fx_data[3]), fontweight='bold')

        # Save PNG
        if save_figure:
            sortie.path_dictionary['waypoint_graph'] = os.path.join(sortie.path,
                                                                  'FX%02d-M%02d-S%02d-UAV%02d_missionWPExec.png' % (
                                                                      sortie.fx_data[0], sortie.fx_data[1], sortie.fx_data[2],
                                                                      sortie.fx_data[3]))
        plt.savefig(sortie.path_dictionary['waypoint_graph'], bbox_inches='tight')

        # Show figures
        if show_figure:
            plt.show()
        return fig