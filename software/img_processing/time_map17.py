###############################################################################
#
# This script aims to create a time map of the BZ reaction, like the one that
# can be seen in many BZ papers.
# The idea is to take a column of pixels every frame (always the same one)
# and display an image with these columns adjacent to one another.
#
###############################################################################


import cv2, sys
import numpy as np
from gridclickdata17 import GridClickData17


def add_column(frame, timemap, bz_coord, xcol):

    x1, y1, x2, y2 = bz_coord
    step_w = int( (x2 - x1) / 7 )
    step_h = int( (y2 - y1) / 1 )
    height = y2 - y1
    width = x2 - x1

    for i in range(7):
        # pad = 0
        # if i == 0:
        #     pad = 10
        # if i == 1:
        #     pad = 10
        # if i == 2:
        #     pad = -10
        col = frame[y1:y2, x1 + step_w*i + 30]
        timemap[i*height:i*height+height, xcol] = col


if __name__ == "__main__":

    video = cv2.VideoCapture(sys.argv[1])
    click_grid = GridClickData17()
    frame_counter = 0
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    #total_frames = int(total_frames/30)+1
    timemap = np.zeros((600, total_frames, 3), np.uint8)
    speed = 1

    start_frame = 0 # 0 from beggining, 1800 half,...
    video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    outname = sys.argv[1].split(".")[0] + "_timemap.avi"
     
    while(True):

        ret, frame = video.read()

        if frame_counter % speed is not 0:
            continue

        if ret is False:
            break

        # first thing we ask the user to define the 5x5 grid
        if click_grid.finished is False:
            # click_grid is now populated with the x,y corners of the platform
            click_grid.get_platform_corners(frame)
            x1, y1, x2, y2 = click_grid.points
            height = (y2-y1)*7
            width = total_frames-start_frame
            timemap = np.resize(timemap, ( height, width, 3) )
          #  outvideo = cv2.VideoWriter(outname, fourcc, 10.0, (width,height))
        
        add_column(frame, timemap, click_grid.points, frame_counter)

        # comment or uncomment 2 following lines to see video
       # cv2.imshow('Time map', timemap)
        key = cv2.waitKey(1) & 0xFF
        frame_counter += 1

       # outvideo.write(timemap)


    outname = sys.argv[1].split(".")[0] + ".png"
    cv2.imwrite(outname, timemap)
   # video.release()

