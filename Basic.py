"""
This is meant as a basic overview of the method through which this project tracks shifts in position.
Note that the algorithm compares each subsequent frame to an initial reference frame, as opposed to
comparing each subsequent frame to the previous frame. 
"""

from instrumental.drivers.cameras import uc480
import cv2
from Algorithms.Algorithm2 import imregpoc
import datetime


print("Start")


#initialize camera
instruments = uc480.list_instruments() #this creates a list of all available instruments
hCam = uc480.UC480_Camera(instruments[0]) #0: first available camera; 1-254: Camera with specified ID

#begin video
hCam.start_live_video(framerate="10Hz")

#variables
reference_images = [] #this creates a list to which reference images will be added
alg2_x_pixel_offset =[] #the offset in the x-direction will be added to this list
alg2_y_pixel_offset =[] #the offset in the y-direction will be added to this list
time_images =[] #the time each image is captured will be added to this list
indexes = [] #creates a list which indexes each frame

i=0
index = 0

#this loop finds the shift in each successive frame
while i < 20:
    nret = hCam.wait_for_frame() #this evaluates to "True" when there is a new frame
    if nret == True:
        i=i+1
        print(i)

        index = index + 1
        array = hCam.latest_frame(copy=False) #this gets the image data from the new frame

        #resize the image by 1/2
        frame = cv2.resize(array, (1024, 768), fx=0.5, fy=0.5)

        #add captured to the reference images
        if index == 1:
            reference_images.append(frame)

        #Applies Algorithm2
        alg2_offset = imregpoc(reference_images[0], frame) #compares the reference image to the captured image to compute shift
        #adds the measured shift to the lists created above
        alg2_x_pixel_offset.append(-alg2_offset.param[0])
        alg2_y_pixel_offset.append(-alg2_offset.param[1])

        #adds the time the image is captured to the list created above
        date_string = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S_%f")
        time_image = datetime.datetime.strptime(date_string, '%m_%d_%Y_%H_%M_%S_%f')
        time_images.append(time_image)

        #records index number of frame
        indexes.append(index)
