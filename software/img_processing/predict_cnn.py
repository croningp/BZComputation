###############################################################################
#
# This code is heavily based on the book "Hands on ML & Tensorflow"
# You can see the jupyter notebook here:
# https://github.com/ageron/handson-ml/blob/master/13_convolutional_neural_networks.ipynb
# Basically I have adapted it to our problem.
#
###############################################################################

import sys, time
sys.path.append('..')

import cv2, threading, queue
import numpy as np
from collections import deque

from gridclickdata17 import GridClickData17
from generate_dataset import bz_average_color
from variabledeque import VariableQueue
import FSM

import tensorflow as tf


class CNN(threading.Thread):

    def __init__(self, kwargs=None):

        # super to threading.Thread
        super().__init__()

        # queue where to share results with main thread
        self.resq = kwargs['resq']
        # queue where to put signal to stop this thread
        self.stopsig = kwargs['stopsig']

        # the path to analyse, it can be a cam or a video
        self.streampath = kwargs['streampath']
        # name of the video to produce with the results
        self.outvideo = kwargs['outvideo']

        # start our clock to control freq of oscillations
        self.clock = BZClock()


    def run(self):
        self.predict_stream()


    def predict_frame(self, sess, graph, frame, caframe, bz_coordinates, bkg_color, 
        filter_deque, FSM_deque):
        ''' Given a frame and the bz coordinates, it extracts the cells 
        and uses the model to predict if it will be a blue or red cell'''

        # top right and bottom right corner of the bz platform
        x1, y1, x2, y2 = bz_coordinates
        height = y2 - y1
        width = x2 - x1
        stepw = int(width / 7)
        steph = int(height / 1)

        # where to store CA frame results, and it will be put in queue
        frame_res = np.zeros((7,7))
        # where to store the CNN oscillations detection
        predictions = []

        for i in range(7):
            for j in range(1):
                # top left corner of the current cell (i,j)
                pointA = (x1+11 + stepw * i, y1+11 + steph * j)
                # bottom right corner of the current cell (i,j)
                pointB = (x1-11 + stepw * (i+1), y1-11 + steph * (j+1))
                # Define the Region of Interest as the current cell (i, j)
                roi = frame[pointA[1]:pointB[1], pointA[0]:pointB[0]]
                b,g,r = cv2.split(roi)
                roi = cv2.merge((b,r))
                res = cv2.resize(roi, (50,50)) / 255.
                res[0][0][0] = float(bkg_color[0])/255.
                res[0][0][1] = float(bkg_color[2])/255.

                # use the CNN to predict the probabilities
                X = graph.get_tensor_by_name('inputs/X:0')
                Y_proba = graph.get_tensor_by_name('output/Y_proba:0')

                y_probabilities = Y_proba.eval(feed_dict={
                    X: res.reshape(1,50,50,2)}) 
                # get the max one
                prediction = np.argmax(y_probabilities)
                # store it in the deque
                filter_deque.append(i, prediction)
                # assume prediction is the rounded median
                prediction = int(round(np.median(filter_deque.get(i))))
                predictions.append(prediction)
                # also store it in for the window analysis
                FSM_deque.append(i, prediction)
                #convert to numpy so we can select column
                FSM_d = FSM_deque.tonp()
                
                # check that there will be enough data for CA analysis
                if (FSM_d.ndim < 2):
                    continue
                if (FSM_d.shape[1] < FSM_deque.maxlen):
                    continue

                # init the FSM to calculate the states of the CA
                ca_fsm = FSM.OscillationsFSM()
                # calculate CA state through the i column
                ca_state = ca_fsm.runthrough(FSM_d[i])

                # add results to list
                frame_res[i,j]=ca_state
                
                if ca_state == 1:
                    # if predicted as 0, paint it dark blue
                    cv2.rectangle(caframe, pointA, pointB, (180,120,31), -1) 
                
                elif ca_state == 0:
                    # if predicted as 0, paint it light blue
                    cv2.rectangle(caframe, pointA, pointB, (227,206,166), -1) 

                else: # else it is red
                    cv2.rectangle(caframe, pointA, pointB, (28,26,227), -1) 

                if prediction == 0:
                    # if predicted as 0, paint it dark blue
                    cv2.rectangle(frame, pointA, pointB, (180,120,31), -1) 
               
                elif prediction == 1:
                    # if predicted as 0, paint it light blue
                    cv2.rectangle(frame, pointA, pointB, (227,206,166), -1) 

                else:
                    cv2.rectangle(frame, pointA, pointB, (28,26,227), -1) 

        clock_state = self.clock.update_clock(predictions, 0.1) #0.5 originally

        # if clock state is tock it means BZ made a full cycle
        if clock_state is 'tock':
            cv2.rectangle(frame, (0,0), (1024,576), (0,255,0), -1)
            self.clock.reset_clock() #reset it for next cycle

            # send to main thread the results from the CA
            while not self.resq.empty(): # first empty it
                self.resq.get()
            self.resq.put_nowait(frame_res) # now put results
    

    def predict_stream(self):

        vc = cv2.VideoCapture(self.streampath)
        #vc = cv2.VideoCapture(0)
        
        vc.set(cv2.CAP_PROP_FRAME_WIDTH, 1024) #frame resolution for CA
        vc.set(cv2.CAP_PROP_FRAME_HEIGHT, 576)
        vc.set(cv2.CAP_PROP_BRIGHTNESS, 155/255.)
        vc.set(cv2.CAP_PROP_SATURATION, 255/255.)
        vc.set(cv2.CAP_PROP_CONTRAST, 222/255.)
        click_grid = GridClickData17()    
        play = True # True means play, False means pause

        bkg_window = 3000 # number of avg frame colors we will keep it was 3000
        frame_color = deque(maxlen=bkg_window) # keeps the average color per frame

        videoraw = self.outvideo+".avi"
        videocnn = self.outvideo+"_cnn.avi"
        fourcc = cv2.VideoWriter_fourcc(*'X264')
        out_raw = cv2.VideoWriter(videoraw, fourcc, 15.0, (1024,576))
        out_cnn = cv2.VideoWriter(videocnn, fourcc, 15.0, (1024,576))

        # get number of frames to calculate window decay
        total_frames = int(vc.get(cv2.CAP_PROP_FRAME_COUNT))
        #total_frames = 30 * 60 * 15
        init_window = 3 # window size of the low pass filter
        steps_decay = int(total_frames/init_window)
        frame_counter = 0

        # to clean the results using a low pass filter
        filter_deque = VariableQueue(numcells=7, maxLen=init_window)
        # to store a window of oscillations for CA analysis
        fsm_deque = VariableQueue(numcells=7, maxLen=40)
        
        tf.reset_default_graph()

        with tf.Session() as sess:

            saver = tf.train.import_meta_graph("cnn_oscs.meta")
            saver.restore(sess, "cnn_oscs")
            graph = tf.get_default_graph()

            while(True):

                # if the queue stopsig is not empty, it needs to stop
                if not self.stopsig.empty():
                    break

                if play is True:
                    ret, frame = vc.read()

                if ret is False:
                    break

                # first thing we ask the user to define the 5x5 grid
                if click_grid.finished is False:
                    click_grid.get_platform_corners(frame, self.streampath)
                    #time.sleep(10*60) # sleep for 5 min while the reaction gets ready

                frame_counter += 1
                framecopy = frame.copy()

                # every steps_decay frames we decrease the LPF window
                #if frame_counter % steps_decay == 0:
                #    newlen = max(filter_deque.maxlen - 1, 1)
                #    filter_deque.newmaxlength(newlen)

                # calculate the average color of this frame
                avg_c = bz_average_color(frame, click_grid.points) 
                # save it
                frame_color.append(avg_c)
                # calculate the average color of the last n frames
                window_c = np.average(frame_color, axis=0).astype('float32')

                # "click_grid" is now populated with the x,y corners of the platform
                click_grid.draw_grid(frame)
                # we use the CNN to decide if the cells are painted red or blue
                caframe = frame.copy()
                self.predict_frame(sess, graph, frame, caframe, click_grid.points, 
                        window_c, filter_deque, fsm_deque)
                out_raw.write(framecopy)
                out_cnn.write(caframe)

                cv2.imshow("CNN",frame)
                #cv2.imshow("CA",caframe)
                cv2.imshow("RAW",framecopy)
                cv2.waitKey(1)


        vc.release()
        out_raw.release()
        out_cnn.release()
        cv2.destroyAllWindows()


    def reset_graph(self, seed=42):
        tf.reset_default_graph()
        tf.set_random_seed(seed)
        np.random.seed(seed)


class BZClock(): 
    ''' this class will analyse the BZ chemical oscillations to
    detect the periodicity of the oscillations. The time it takes
    for a cell to oscillate twice will be our "clock"'''

    def __init__(self, numcells=7):

        # save numcells for resetting the clock later on
        self.numcells = numcells
        # to store the frequency of BZ oscillations.
        # None means no oscillation, the other options are tick or tock
        # it will tick on red to lblue or dblue
        # it will tock when it goes back to red
        self.clock = [None] * self.numcells
        # None is no state, then tick or tock
        global clock_state
        clock_state = None


    def update_clock(self, current_oscillations, delay):
        '''current oscillations will be a list with numcells cells.
        In this list, as produced by the CNN, 0 means dblue, 1 means
        lblue and 2 means red.'''

        global clock_state

        for i in range(len(current_oscillations)):

            cell_oscillation = current_oscillations[i]

            # red cell, and clock not in clock, do nothing
            if cell_oscillation == 2 and self.clock[i] is None:
                continue
            # red cell, and clock in tick, move to tock
            elif cell_oscillation == 2 and self.clock[i] == 'tick':
                self.clock[i] = 'tock'
                self.toTock(current_oscillations, delay)
            # red cell, and clock in tock, do nothing
            elif cell_oscillation == 2 and self.clock[i] == 'tock':
                self.toTock(current_oscillations, delay)

            # lblue cell, and clock not in clock, do tick
            elif cell_oscillation == 1 and self.clock[i] is None:
                self.clock[i] = 'tick'
                self.tick()
            # lblue cell, and clock in tick, do nothing
            elif cell_oscillation == 1 and self.clock[i] == 'tick':
                continue
            # lblue cell, and clock in tock, unexpected
            elif cell_oscillation == 1 and self.clock[i] == 'tock':
                continue

            # dblue cell, and clock not in clock, do tick
            elif cell_oscillation == 0 and self.clock[i] is None:
                self.clock[i] = 'tick'
                self.tick()
            # dblue cell, and clock in tick, do nothing
            elif cell_oscillation == 0 and self.clock[i] == 'tick':
                continue
            # dblue cell, and clock in tock, unexpected
            elif cell_oscillation == 0 and self.clock[i] == 'tock':
                continue

        return clock_state


    def tick(self):
        '''when the first tick happens, we will change the
        clock_state to tick'''

        global clock_state

        # find all the "ticks" in the clock
        indices = [i for i, x in enumerate(self.clock) if x == "tick"]

        # if there is only exactly 1, it means it was the first tick
        # then we set the clock_state to tick
        if clock_state is None:
            clock_state = "tick"


    def toTock(self, current_oscillations, delay):
        '''when the last tock happens, we will change the
        clock_state to toTock meanding that after delay, it will tock'''

        global clock_state

        # count the number of cells in red
        reds = [i for i, x in enumerate(current_oscillations) if x == 2]
        # count the number of cells in tick
        tocks = [i for i, x in enumerate(self.clock) if x == "tock"]

        # if it is full red and it is in tick, make it a tock
        if len(reds) == 7 and len(tocks) > 2 and clock_state == "tick":
            clock_state = "toTock"
            threading.Timer(delay, self.tock).start()


    def tock(self):
        global clock_state
        clock_state = "tock"


    def reset_clock(self):
        '''When from main.py we read a tock, then we can set it all
        to None'''
        global clock_state
        clock_state = None
        self.clock = [None] * self.numcells



if __name__ == "__main__":

    invideo = sys.argv[1]
    outvideo = sys.argv[2]

    resq = queue.Queue()
    stopt = queue.Queue()

    cnn = CNN(kwargs={
        'streampath': invideo, 'outvideo': outvideo,
        'resq': resq, 'stopsig': stopt
        })
    # start the thread
    cnn.start()
    # just wait for 120 seconds while it works on another thread
    # time.sleep(120)
    # resq is where the results are. we can print its size now
    #print(resq.qsize())
    # we put a 1 to this queue to stop the thread
    #stopt.put(1)
    # join to let it 100% finish and clean up.
    cnn.join()
