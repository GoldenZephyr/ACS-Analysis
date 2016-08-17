import matplotlib.pyplot as plt
import math


def div_plot_setup(nsorties, rows=8, stacked=False, n_extra_lines=0, y_axis_loc=0, x_axis_loc=-1, format_axes=True):

    if not stacked:
        columns = int(math.ceil(float(nsorties)/rows))
    else:
        columns = 1
    fig = plt.figure(figsize=(8,10))
    axlist = []
    vbuf = .02  # vertical buffer between subplots
    hbuf = .01  # horizontal buffer between subplots
    header = .09  # space at top of figure
    footer = .03  # space at bottom of figure
    left_marg = .05  # space at left of figure
    right_marg = n_extra_lines*.1 # space at rightt of figure

    if x_axis_loc < 0:
        x_axis_loc = rows + x_axis_loc
    if y_axis_loc < 0:
        y_axis_loc = columns + x_axis_loc

    horiz_space = left_marg + right_marg
    vert_space = header + footer
    dx = (1-horiz_space)/(float(columns)*(hbuf+1.))  # Width of graph
    dy = (1.01-vert_space - vbuf)/(float(rows+1)*(vbuf*1.6+1.))  # Height of graph
    c_row = 0
    c_col = 0
    label_list = {}
    if not stacked:
        nrows = rows * columns
    else:
        nrows = nsorties
    for count in xrange(nrows):
        xmin = left_marg + dx*c_col + hbuf*c_col
        ymin = (1-header) - dy*(c_row+1) - vbuf*c_row
        ax = fig.add_axes([xmin, ymin, dx, dy])
        if format_axes:
            if (c_row != x_axis_loc) & (count != nrows-1):
                ax.get_xaxis().set_visible(False)
            if c_col != y_axis_loc:
                ax.get_yaxis().set_visible(False)

        axlist.append(ax)
        if c_col == 0:
            label_list.setdefault(0,[]).append(ax)
        if c_col == columns-1:
            for count in range(n_extra_lines):
                lax = fig.add_axes([xmin + dx + .07*(count+1) + hbuf, ymin, .0001, dy])
                lax.tick_params(labelbottom='off')
                label_list.setdefault(count+1, []).append(lax)
        c_row += 1
        if c_row == rows:
            c_row = 0
            if not stacked:
                c_col += 1
            else:
                fig = plt.figure()

    final_list = []
    final_list.append(axlist)
    for ii in range(len(label_list)-1):
        temp_list = []
        for ax in axlist:
            new_ax = ax.twinx()
            new_ax.tick_params(labelright='off')
            temp_list.append(new_ax)
        final_list.append(temp_list)

    for ii in range(1,len(label_list)):
        for ax in label_list[ii]:
            #ax.set_ylabel('yyyyyyyy', rotation=90)
            ax.get_yaxis().set_label_position('right')

    return final_list, label_list