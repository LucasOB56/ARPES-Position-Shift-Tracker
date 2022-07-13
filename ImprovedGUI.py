import PySimpleGUI as sg
from instrumental.drivers.cameras import uc480
import cv2
from Algorithms.Algorithm2 import imregpoc
import datetime
import csv
import numpy as np


"""
Variables for editing the code
"""
testmode = True #if true, allows you to run the program without being attached to a camera
vidsize = 780 #changes size of the live video screen in the gui
graphsize = 350 #changes sizes of the graphs

#recommended: don't change
imxp = 0 #x-component of the position of the top-left corner of the image in the live video screen
imyp = vidsize #y-component of the position of the top-left corner of the image in the live video screen

"""
Introducing Some Necessary Variables
"""
#sample tracking
xdisp=0
ydisp=0
xdispr=0
ydispr = 0
convf = 1
unitstr = ''
unitconvf = 0
index = 0

#camera settings
framerate = 10
exposure_time = 10

#graph settings
xaxismax = 100
yaxismax_x = 25
yaxismax_y = 25
xtickfreq = 10
ytickfreq = 5

#lists to which data will be added
reference_images = []  # this creates a list to which reference images will be added
alg2_x_pixel_offset = []  # the offset in the x-direction will be added to this list
alg2_y_pixel_offset = []  # the offset in the y-direction will be added to this list
time_images = []  # the time each image is captured will be added to this list
indexes = []  # creates a list which indexes each frame

#variables used to control the GUI
block = True
lock = False
setwindow_active = False
autoexp = True
camblock = True
click1 = False
click2 = False
roiblock = True
roimode = "set"
start = True


#default region of interest
roi1 = (0,vidsize)
roi2 = (vidsize, 0)


"""
Initializes camera if testmode is turned off
"""
if testmode == False:
    # Gives Possible Instruments
    print('There is/are', len(uc480.list_instruments()), 'available instrument(s).')
    if len(uc480.list_instruments()) != 0:
        print('Available Instrument(s):')
        print(uc480.list_instruments())
    else:
        print('Error: no available instruments.')
        exit(1)

    # initializes camera
    instruments = uc480.list_instruments()
    cam = uc480.UC480_Camera(instruments[0])

    # starts live video
    cam.start_live_video(framerate=str(framerate) + "Hz")
    cam.set_auto_exposure()

"""
Creates the GUI window
"""
#layouts for tabs (this one is data)
tab1_layout = [
    [sg.Text('x-displacement (px):'), sg.Text(xdisp, key = "-xdisp-")],
    [sg.Text('x-displacement ('), sg.Text(unitstr, key = "-xunitstr-"), sg.Text('):'), sg.Text(xdispr, key = "-xdispr-")],
    [sg.Text('y-displacement (px):'), sg.Text(ydisp, key = "-ydisp-")],
    [sg.Text('y-displacement ('), sg.Text(unitstr, key = "-yunitstr-"), sg.Text('):'), sg.Text(ydispr, key = "-ydispr-")],
    [sg.Text('')],
    [sg.Text('Conversion Factor:')],
    [sg.Input(convf, key="-convfin-", size=(10, 10)), sg.Button('Apply', key="-convfapply-"),
     sg.Text(key="-errconvf-")],
    [sg.Text('1 px ='), sg.Text(convf, key="-convf-"),
     sg.Listbox(["", "mm", "um", "nm", "cm", ], enable_events=True, size=(4, 1), key="-unit-")],
               ]

#this one is for the graphs
tab2_layout = [
    [sg.Text("Graphs of image shift (px) vs image number (right: x-displacement, left: y-displacement)")],
    [sg.Graph(canvas_size = (2*graphsize, graphsize), graph_bottom_left=(-20, -yaxismax_x-10), graph_top_right=(xaxismax+10, yaxismax_x+10), key = "-xgraph-", background_color="white", tooltip = "Graph of x-displacement", float_values = True)],
    [sg.Graph(canvas_size = (2*graphsize, graphsize), graph_bottom_left=(-20, -yaxismax_y-10), graph_top_right=(xaxismax+10, yaxismax_y+10), key = "-ygraph-", background_color="white", tooltip = "Graph of y-displacement", float_values = True)],
    [sg.Text("Graph dot size")],
    [sg.Slider(range = (0.1,2.5), default_value= 0.5, key = "-dotsize-", resolution = 0.1, orientation='h')]
]

#this one is for live images
tab3_layout = [
    [sg.Graph(canvas_size= (vidsize, vidsize), graph_bottom_left = (0, 0), graph_top_right = (vidsize, vidsize), key = '-image-', background_color="black", enable_events = True, motion_events=True, drag_submits= True)],
    [sg.Button('Select ROI', key = "-roi-")],
]

tab4_layout = [
    [sg.Graph(canvas_size= (vidsize, vidsize), graph_bottom_left = (0, 0), graph_top_right = (vidsize, vidsize), key = '-roiimage-', background_color="black")],
]

#this creates the elements which will be shown in the GUI window. Their key is how you call them within the code
layout = [
    [sg.TabGroup([[sg.Tab("Graph", tab2_layout, tooltip = 'Graph', key = "-graphtab-")], [sg.Tab("Data", tab1_layout, tooltip = 'Data')]]), sg.TabGroup([[sg.Tab("Full View", layout = tab3_layout, tooltip = "Full Image")], [sg.Tab("ROI View", layout = tab4_layout, tooltip = "ROI")]])],
    [sg.Button("Start", key = "-start-"), sg.Button("Stop", key = "-stop-"), sg.Button('Start Live Video', key = "-live-"), sg.Button("Settings", key = "-settings-")],
    [sg.Text('Press stop to export CSV file. Previous data will not be saved when starting program.')]
]

#Creates the Window
window = sg.Window(title = 'ARPES Sample Tracker', layout = layout, margins = (20, 20), finalize = True)

"""
Functions which will be used in main part of code
"""
def creategraph(xaxismax, yaxismax_x, yaxismax_y, xtickfreq, ytickfreq):
    xgraph = window["-xgraph-"]
    ygraph = window["-ygraph-"]

    # creates axis for graphs
    xgraph.DrawLine((0, 0), (xaxismax, 0))
    xgraph.DrawLine((0, -yaxismax_x), (0, yaxismax_x))

    ygraph.DrawLine((0, 0), (xaxismax, 0))
    ygraph.DrawLine((0, -yaxismax_y), (0, yaxismax_y))

    for x in range(0, xaxismax, xtickfreq):
        xgraph.DrawLine((x, -1), (x, 1))
        if x != 0:
            xgraph.DrawText(round(x), (x, -max(round(yaxismax_x/12), 1)), color='green')

    for y in range(-yaxismax_x, yaxismax_x, ytickfreq):
        xgraph.DrawLine((-1, y), (1, y))
        if y != 0:
            xgraph.DrawText(round(y), (-max(round(xaxismax/12), 1), y), color='blue')

    for x in range(0, xaxismax, xtickfreq):
        ygraph.DrawLine((x, -1), (x, 1))
        if x != 0:
            ygraph.DrawText(round(x), (x, -max(round(yaxismax_y/12),1)), color='green')

    for y in range(-yaxismax_y, yaxismax_y, ytickfreq):
        ygraph.DrawLine((-1, y), (1, y))
        if y != 0:
            ygraph.DrawText(round(y), (-max(round(xaxismax/12), 1), y), color='blue')


def exportcsv(indexes, alg2_x_pixel_offset, alg2_y_pixel_offset, time_images):
    # export data as csv file
    row_index = 0
    with open('pixel_vs_displ'+datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S_%f")+'.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        data = list(zip(indexes, alg2_x_pixel_offset, alg2_y_pixel_offset, time_images))
        writer.writerow(["Image Index", "Alg 2 x pixel offset", "Alg 2 y pixel offset", "Image time taken"])
        for row in data:
            row = list(row)
            writer.writerow(row)
            row_index = row_index + 1
            
creategraph(xaxismax, yaxismax_x, yaxismax_y, xtickfreq, ytickfreq)

"""
Runs the program
"""

while lock == False:
    #reads the GUI window for inputs
    event, values = window.read(timeout = 1)

    #Starts sample tracking by removing block if "start" is clicked
    if event == "-start-":
        #resets variables
        reference_images = []  # this creates a list to which reference images will be added
        alg2_x_pixel_offset = []  # the offset in the x-direction will be added to this list
        alg2_y_pixel_offset = []  # the offset in the y-direction will be added to this list
        time_images = []  # the time each image is captured will be added to this list
        indexes = []  # creates a list which indexes each frame
        index = 0

        #starts program
        block = False
        print('Start')

    # waits for next camera frame if not in test mode
    if testmode == False:
        nret = cam.wait_for_frame()  # this evaluates to "True" when there is a new frame
    else:
        nret = False

    #if there is a new frame and the program has been started, compares frame with reference and returns shift
    if nret == True and block != True:
        index = index + 1
        print(index)

        array = cam.latest_frame(copy=False)  # this gets the image data from the new frame


        #If a region of interest has been chosen, crops frame to region of interest
        if roimode == "reset" and roi1[0] != roi2[0] and roi1[1] != roi2[1]:
            array = cv2.resize(array, (vidsize, vidsize))
            a = min(roi1[1], roi2[1])
            b = max(roi1[1], roi2[1])
            c = min(roi1[0], roi2[0])
            d = max(roi1[0], roi2[0])

            #crops frame
            frame = array[vidsize - b:vidsize - a, c:d]
            frame = cv2.resize(frame, (1024,768), fx = 0.5, fy = 0.5)
        else:
            # resize the image by 1/2
            frame = cv2.resize(array, (1024, 768), fx=0.5, fy=0.5)


        # add captured to the reference images
        if index == 1:
            reference_images.append(frame)
            cv2.imwrite("ref_im.png", frame)

        # Applies Algorithm2
        alg2_offset = imregpoc(reference_images[0],
                               frame)  # compares the reference image to the captured image to compute shift

        # adds the measured shift to the lists created above
        alg2_x_pixel_offset.append(-alg2_offset.param[0])
        alg2_y_pixel_offset.append(-alg2_offset.param[1])

        xdisp = -alg2_offset.param[0]
        ydisp = -alg2_offset.param[1]

        #converts pixels to units
        xdispr = xdisp * convf
        ydispr = ydisp * convf

        # this updates the window (in the "data" tab) to show the given x- and y- displacement
        window["-xdisp-"].update(xdisp)
        window["-ydisp-"].update(ydisp)
        window["-xdispr-"].update(xdispr)
        window["-ydispr-"].update(ydispr)


        # adds the time the image is captured to the list created above
        date_string = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S_%f")
        time_image = datetime.datetime.strptime(date_string, '%m_%d_%Y_%H_%M_%S_%f')
        time_images.append(time_image)

        indexes.append(index)

        #updates the graph (in the "graph" tab)
        window["-xgraph-"].erase()
        window["-ygraph-"].erase()
        xaxismax = max(int(round(max(indexes))), 25)
        yaxismax_x = max(int(round(max(alg2_x_pixel_offset))), 5)
        yaxismax_y = max(int(round(max(alg2_y_pixel_offset))), 5)
        xtickfreq = max(5, int(round(xaxismax/5)))
        ytickfreq = int(round(max(yaxismax_x, yaxismax_y)/5))

        #gets user selected dotsize from graph
        dotsize = values["-dotsize-"]

        #changes graph size to fit axes
        window["-xgraph-"].change_coordinates(graph_bottom_left=(-5, -yaxismax_x-2), graph_top_right=(xaxismax+2, yaxismax_x+2))
        window["-ygraph-"].change_coordinates(graph_bottom_left=(-5, -yaxismax_y-2), graph_top_right=(xaxismax+2, yaxismax_y+2))
        creategraph(xaxismax, yaxismax_x, yaxismax_y, xtickfreq, ytickfreq)
        for i in range(index):
            window["-xgraph-"].draw_point((indexes[i], alg2_x_pixel_offset[i]), size = dotsize)
            window["-ygraph-"].draw_point((indexes[i], alg2_y_pixel_offset[i]), size = dotsize)

    #if "start live video" is clicked, removes block to start live video
    if event == "-live-":
        if camblock == True:
            window["-live-"].update('Stop Live Video')
            camblock = False
        elif camblock == False:
            window["-live-"].update('Start Live Video')
            camblock = True


    if camblock == False and nret == True:
        nframe = cam.latest_frame(copy=False) #gets latest frame from camera
        frame1 = np.stack((nframe,) * 3, -1)  # make frame as 1 channel image
        frame1 = frame1.astype(np.uint8)
        gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)

        #makes image the right size for live view frame
        im2 = cv2.resize(gray, (vidsize, vidsize))

        #saves image as a png and then updates window
        cv2.imwrite('image.png', im2)
        window["-image-"].draw_image(filename='image.png', location=(imxp, imyp))

        #this is to stop the roi rectangle from disappearing when the frame refreshes
        if roimode == "cancel" and click1 == True:
            window["-image-"].draw_rectangle(roi1, values["-image-"], line_color="green")
        if roimode == "reset":
            window["-image-"].draw_rectangle(roi1, roi2, line_color = "orange")

        #prints error if region of interest is zero
        if roi1[0] == roi2[0]:
            print("error")
        if roi1[1] == roi2[1]:
            print("error")

        #this ensures that the image isn't cropped in such a way that it has a width or height of zero
        if roi1[0] != roi2[0] and roi1[0] != roi2[0]:
            a = min(roi1[1], roi2[1])
            b = max(roi1[1], roi2[1])
            c = min(roi1[0], roi2[0])
            d = max(roi1[0], roi2[0])

            #crops image to region of interest
            frame = im2[vidsize - b:vidsize - a, c:d]
            #resizes the image to fit region of interest screen
            frame = cv2.resize(frame, (vidsize, vidsize))
            #saves image as png, then loads image to region of interest screen
            cv2.imwrite("roi_im.png", frame)
            window["-roiimage-"].erase()
            window["-roiimage-"].draw_image(filename='roi_im.png', location = (imxp, imyp))

    #activates if the "select ROI" button is clicked
    """
    The variable "roimode" keeps track of which mode the roi is in. If the roimode is "set", then 
    no user roi has been set and the roi is default. If the roimode is "cancel", then the user roi
    is in the process of being set. If the roimode is "reset", then a user roi is already set. The
    "select ROI" button changes according to what the roimode is, to reflect what the effect of pressing
    the button will be.
    """
    if event == "-roi-":
        if roimode == "set":
            window["-roi-"].update("Cancel")
            #allows user to select an roi
            roiblock = False
            #changes roimode
            roimode = "cancel"
            #resets click1 and click2 variables
            click1= False
            click2= False
        elif roimode == "cancel":
            print(roimode)
            window["-image-"].erase()
            window["-image-"].draw_image(filename='image.png', location=(imxp, imyp))
            #blocks user from selecting an roi
            roiblock = True
            #resets click1 and click2 varaibles
            click1=False
            click2=False
            #sets default roi
            roi1 = (0, vidsize)
            roi2 = (vidsize, 0)
            #changes roimode
            roimode = "set"
            window["-roi-"].update("Select ROI")
        elif roimode == "reset":
            print(roimode)
            window["-image-"].erase()
            window["-image-"].draw_image(filename='image.png', location=(imxp, imyp))
            #allows user to select an roi
            roiblock = False
            #changes roimode
            roimode = "cancel"
            window["-roi-"].update("Cancel")
            #resets click1 and click2 variables
            click1 = False
            click2 = False

    #this creates the drawings which appear on the full view screen when selecting an roi
    if event == "-image-":
        """
        The click1 and click2 variables are activated when the user clicks on the full view screen to 
        select an ROI, and are used to track where in the process of selecting the ROI the user is. If
        click1 is set to True, then the program knows that the first corner of the ROI has been set. 
        Similarly, if click2 is set to True, the program knows that the second corner of the ROI has been
        selected, thus completing the selection of the roi. 
        """
        #if the first corner has already been selected
        if click1 == True and roiblock == False:
            #this variable is a point corresponding to the second corner of the ROI
            roi2 = values["-image-"]
            roimode = "reset"
            roiblock = True
            window["-roi-"].update("Reset ROI")
            click2 = True
            print(roi1, roi2)
        #if neither corner has been selected
        elif click1 == False and roiblock == False:
            click1 = True
            click2 = False
            window["-image-"].draw_point(values["-image-"], color="red")
            #this variable is a point corresponding to the first corner of the ROI
            roi1 = values["-image-"]
            print(roi1,roi2)

    """
    When the first corner of the ROI has been selected but the second has not, this code creates a
    green square which shows what the selected ROI would be were the user to click. The square becomes
    purple if the selected ROI is square. 
    """
    if click1 == True and click2 == False:
        if event == '-image-+MOVE':
            window["-image-"].erase()
            window["-image-"].draw_image(filename='image.png', location=(imxp, imyp))
            window["-image-"].draw_point(values["-image-"], color = "red")
            if values["-image-"][0] - roi1[0] == values["-image-"][1] - roi1[1]:
                window["-image-"].draw_rectangle(roi1, values["-image-"], line_color="purple")
            else:
                window["-image-"].draw_rectangle(roi1, values["-image-"], line_color = "green")


    #this activates when the "apply conversion factor" button is pushed.
    if event == "-convfapply-":
        convfstr = values["-convfin-"]
        window["-errconvf-"].update('')
        #gives an error if the user created conversion factor is not a float
        try:
            convf = float(convfstr)
            window["-convf-"].update(convf)
        except ValueError:
            print('Error: conversion factor not a float')
            window["-errconvf-"].update('Error: non-float input')

    # this updates the units, both that are shown in the gui and the conversion ratio
    if event == "-unit-": #this only activates when a new unit is chosen
        oldunitconvf = unitconvf
        if values["-unit-"] == ['mm']:
            window["-xunitstr-"].update('mm')
            window["-yunitstr-"].update('mm')
            unitconvf = 1000
        elif values["-unit-"] == ['cm']:
            window["-xunitstr-"].update('cm')
            window["-yunitstr-"].update('cm')
            unitconvf = 10000
        elif values["-unit-"] == ['um']:
            window["-xunitstr-"].update('um')
            window["-yunitstr-"].update('um')
            unitconvf = 1
        elif values["-unit-"] == ['nm']:
            window["-xunitstr-"].update('nm')
            window["-yunitstr-"].update('nm')
            unitconvf = 10**(-3)
        else:
            unitconvf = 0
            window["-xunitstr-"].update('')
            window["-yunitstr-"].update('')


        if oldunitconvf == 0:
            window["-convf-"].update(convf)
        elif oldunitconvf != unitconvf:
            convf = convf * unitconvf/oldunitconvf
            window["-convf-"].update(convf)

        window.refresh()

    #creates a new window if "settings" is activated
    if event == "-settings-" and not setwindow_active:
        setwindow_active = True
        window.hide()

        #creates the settings window
        if autoexp == True:
            setlayout = [
                [sg.Text('Exposure Time (ms):'), sg.Input("Auto", key="-exposure-", disabled=True)],
                [sg.Text('Framerate (Hz):'), sg.Input(framerate, key="-framerate-")],
                [sg.Button("Manual Exposure", key="-manexp-"), sg.Button("Apply", key="-setapply-"),
                 sg.Text('', key="-seterr-")],
            ]
        else:
            setlayout = [
                [sg.Text('Exposure Time (ms):'), sg.Input(exposure_time, key="-exposure-", disabled=False)],
                [sg.Text('Framerate (Hz):'), sg.Input(framerate, key="-framerate-")],
                [sg.Button("Automatic Exposure", key="-manexp-"), sg.Button("Apply", key="-setapply-"),
                 sg.Text('', key="-seterr-")]
            ]

        setwindow = sg.Window(title = "Camera Settings", layout = setlayout)
        while True:
            ev2, vals2 = setwindow.Read()
            #if the "apply" button is pressed
            if ev2 == "-setapply-":
                if exposure_time > 1000*framerate:
                    print('error: exposure time greater than framerate')
                    setwindow["-seterr-"].update('error: exposure time greater than framerate')
                    exposure_time = 10
                    framerate = 10
                    setwindow["-exposure-"].update(exposure_time)
                    setwindow["-framerate-"].update(framerate)
                else:
                    cam.stop_live_video()
                    setwindow["-seterr-"].update('')
                    lfr = vals2["-framerate-"]
                    try:
                        lfr = float(lfr)
                        framerate = lfr
                    except ValueError:
                        print('Error: framerate not a float')
                        setwindow["-seterr-"].update('Please input a float')

                    if autoexp == False:
                        setwindow["-seterr-"].update('')
                        lexp = vals2["-exposure-"]
                        try:
                            lexp = float(lexp)
                            exposure_time = lexp
                            print(exposure_time)
                        except ValueError:
                            print('Error: exposure time not a float')
                            setwindow["-seterr-"].update('Please input a float')
                        cam.start_live_video(framerate= str(framerate)+"Hz", exposure_time= str(exposure_time)+"ms")
                    elif autoexp == True:
                        cam.start_live_video(framerate=str(framerate) + "Hz")
                        cam.set_auto_exposure()

            elif ev2 == sg.WIN_CLOSED:
                setwindow_active = False
                setwindow.Close()
                window.UnHide()
                break

            if ev2 == "-manexp-":
                if autoexp == True:
                    setwindow["-exposure-"].update(exposure_time, disabled=False)
                    setwindow["-manexp-"].update("Automatic Exposure")
                    autoexp = False
                elif autoexp == False:
                    setwindow["-exposure-"].update("Auto", disabled=True)
                    setwindow["-manexp-"].update("Manual Exposure")
                    autoexp = True

    #if "stop" is clicked, stops the sample tracking and exports data
    if event == "-stop-":
        block = True
        start = True
        if len(indexes) > 0:
            exportcsv(indexes, alg2_x_pixel_offset, alg2_y_pixel_offset, time_images)
            
        #resets variables
        reference_images = []
        alg2_x_pixel_offset = []
        alg2_y_pixel_offset = []
        time_images = []
        indexes = []
        index = 0
        
        print('Stop')

    #if the window is closed, stops the program
    if event == sg.WIN_CLOSED:
        print("End")
        lock = True
        if len(indexes) > 0:
            exportcsv(indexes, alg2_x_pixel_offset, alg2_y_pixel_offset, time_images)
    window.refresh()

window.close()
