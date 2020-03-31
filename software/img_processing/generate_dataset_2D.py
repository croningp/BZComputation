###############################################################################
#
# The objective of this script is to generate a dataset for the bz platform.
# What we want is to train an SVM (or any other ML method), in order to detect
# when a cell changes color from red to blue.
# Thus, we want to generate a big database of examples of red and blue cells.
#
# The user starts by marking where the grid is: top left and bottom right points
# This code assumes that the bz platform grid is 5 by 5.
# In the future we might add a variable to control this, but at the moment
# the 5 by 5 is hardcoded.
# Once the video starts playing, the user can click "p" to pause or play it.
# Once the video is paused and it shows a frame, the user can left or right
# click in order to mark the cells as red or blue.
# Once a cell is clicked, an image of that cell is saved into a folder
# These folders are named red of blue.
#
# Mouse callback based on: 
# http://docs.opencv.org/3.1.0/db/d5b/tutorial_py_mouse_handling.html
#
###############################################################################


import numpy as np
import cv2
import random, string, sys, pathlib
import subprocess
from collections import deque
from gridclickdata_2D_CA import GridClickData2D


class CellClickData:
    '''This class represents the data that is passed from and to
    the cell mouse callback in order to recognize clicks by the user in 
    order to select a cell and save it as red or blue for the database.'''


    def __init__(self):
        # returns a empty clicks array where we will store the user clicks
        # Each position of the array contains a 4 size array, which 4 elements
        # are: x, y, left or right click, saved or not
        self.clicks = np.delete(np.empty([1,4]), 0, axis=0)

        # create the 3 folders where to save the images
        pathlib.Path('reds').mkdir(parents=True, exist_ok=True)
        pathlib.Path('lblues').mkdir(parents=True, exist_ok=True)
        pathlib.Path('dblues').mkdir(parents=True, exist_ok=True)


    def mouse_cell(self, event, x, y, flags, param):
        '''mouse callback function when adding new clicks, 
        0 will mean left click, 1 right click, 2 means middle click'''

        if event == cv2.EVENT_LBUTTONDOWN:
            self.clicks = np.append(self.clicks, [[x,y,0,0]], axis=0)

        elif event == cv2.EVENT_RBUTTONDOWN:
            self.clicks = np.append(self.clicks, [[x,y,1,0]], axis=0)

        elif event == cv2.EVENT_MBUTTONDOWN:
            self.clicks = np.append(self.clicks, [[x,y,2,0]], axis=0)


    def draw_save_cells(self, frame, bz_coordinates, window_c):
        ''' colours and saves the bz cells where the user has clicked. '''

        x1, y1, x2, y2 = bz_coordinates
        height = y2 - y1
        width = x2 - x1
        stepw = int(width / 7)
        steph = int(height / 7)
        color = window_c.astype("int32")

        for click in self.clicks:
            # relative click coordinates to the origin of the bz grid (x1, y1)
            rx, ry = click[0] - x1, click[1] - y1
            # dividing this by step size and rounding we can guess the cell
            icell, jcell = int(rx/stepw), int(ry/steph)
            # now we can just draw the cell and also save it into a file
            pointA = (x1+9 + stepw * icell, y1+9 + steph * jcell)
            pointB = (x1-9 + stepw * (icell+1), y1-9+ steph * (jcell+1))

            if click[2] == 0: # left click

                if click[3] == 0: # not saved it yet
                    # define Region Of Interest around the cell we want
                    roi = frame[pointA[1]:pointB[1], pointA[0]:pointB[0]]
                    new_image = 'dblues/'+self.random_filename(5, color)
                    cv2.imwrite(new_image, roi) # save cell
                    click[3] = 1 # we mark it as saved

                #draw rectangle just for visualization    
                cv2.rectangle(frame, pointA, pointB, (255,0,0), -1) 

            elif click[2] == 1: # right click, see comments just above for following lines

                if click[3] == 0:
                    roi = frame[pointA[1]:pointB[1], pointA[0]:pointB[0]]
                    new_image = 'reds/'+self.random_filename(5, color)
                    cv2.imwrite(new_image, roi)
                    click[3] = 1

                cv2.rectangle(frame, pointA, pointB, (0,0,255), -1) 

            elif click[2] == 2: # middle click, see comments just above for following lines

                if click[3] == 0:
                    roi = frame[pointA[1]:pointB[1], pointA[0]:pointB[0]]
                    new_image = 'lblues/'+self.random_filename(5, color)
                    cv2.imwrite(new_image, roi)
                    click[3] = 1

                cv2.rectangle(frame, pointA, pointB, (198,146,66), -1) 


    def random_filename(self, size, color):
        ''' to create random names for the dataset pictures '''

        w = ''.join(random.choice(string.ascii_lowercase) for i in range(size))
        w += "_"+str(color[0]) +'_' +str(color[2])
        return w+'.png'



def bz_average_color(frame, bz_coordinates):
    ''' Given a frame, it gets the bz board, and returns in average color'''

    x1, y1, x2, y2 = bz_coordinates
    height = y2 - y1
    width = x2 - x1
    stepw = int(width / 7)
    steph = int(height / 7)
    cell_colors = []

    for cell in range(49):
        icell = int(cell / 7)
        jcell = cell % 7
        # calculate cell coordinates
        pointA = (x1+13 + stepw * icell, y1+13 + steph * jcell)
        pointB = (x1-13 + stepw * (icell+1), y1-13 + steph * (jcell+1))

        # define Region Of Interest around the cell we want
        roi = frame[pointA[1]:pointB[1], pointA[0]:pointB[0]]
        # calculate its average color
        avg_color_per_row = np.average(roi, axis=0)
        avg_color = np.average(avg_color_per_row, axis=0)
        cell_colors.append(avg_color)
        #cv2.imshow("roi"+str(cell), roi)

    return np.average(cell_colors, axis=0)



if __name__ == "__main__":


    video = cv2.VideoCapture(sys.argv[1])
    click_grid = GridClickData2D()    
    play = True # True means play, False means pause
    frame_counter = 0
    total_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
    bkg_window = 3000 # number of avg frame colors we will keep
    frame_color = deque(maxlen=bkg_window) # keeps the average color per frame

    while(True):

        if play is True:
            ret, frame = video.read()
            click_cell = CellClickData()
            frame_counter += 1
            if frame_counter % 100 == 0:
                sys.stdout.write("\r{0} in {1}".format(frame_counter, total_frames))
                sys.stdout.flush()

        if ret is False:
            break

        # first thing we ask the user to define the 5x5 grid
        if click_grid.finished is False:
            click_grid.get_platform_corners(frame)

        if play is True:
            # calculate the average color of this frame
            avg_c = bz_average_color(frame, click_grid.points) 
            # save it
            frame_color.append(avg_c)
            # calculate the average color of the last n frames
            window_c = np.average(frame_color, axis=0)

        # "click_grid" is now populated with the x,y corners of the platform
        click_grid.draw_grid(frame)
       
        # now while the video plays the user can click to save cells as dataset
        cv2.namedWindow('Left dark blue, Middle light blue, Right red')
        cv2.setMouseCallback('Left dark blue, Middle light blue, Right red', 
                click_cell.mouse_cell)
        click_cell.draw_save_cells(frame, click_grid.points, window_c)
        
        cv2.imshow('Left dark blue, Middle light blue, Right red', frame)
        key = cv2.waitKey(1) & 0xFF # 33 means roughly 30FPS 

        if key == ord('p'):
            play = not play


    video.release()
    cv2.destroyAllWindows()

