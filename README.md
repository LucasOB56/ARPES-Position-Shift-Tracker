# ARPES-Position-Shift-Tracker

ARPES Position Shift Tracker v1.0

Created by Lucas O'Brien

## Overview

The purpose of this project is to enable a user to track subtle shifts in the position of a object. This is done by capturing consecutive images, and comparing each subsequent image with an initial reference frame. The program was written to be used with a ThorLabs DCx camera. 

## Setup

First, open the code in your Python editor, and download the required packages. 

A PyCharm Virtual Environment was used to to install the required packages for this program. Some required packages include:

**pip** (this is required for package installation).
    
**opencv-contrib-python** (this is required for cv2).
    
**instrumental-lib**.

**pywin32** and **nicelib** (these are required for instrumental).

Then, to allow the program to interface with the camera, install ThorCam. This can be done from this link: https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=ThorCam. If ThorCam works and is able to recognize the camera, the program should work. 

If ThorCam is installed, but does not recognize camera:

If the light on the camera is red, uninstall and reinstall ThorCam, then restart your computer and try again.

If the light on the camera is green, uninstall all other camera interfacing softwares (uEye, IDS, Spinnaker, Flir), restart, and try again. Some information on troubleshooting Thorlabs and IDS incompatibility can be found at https://pylablib.readthedocs.io/en/latest/devices/uc480.html#operation.
