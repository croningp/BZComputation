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
import multiprocessing
import numpy as np
from collections import deque

from gridclickdata_2D import GridClickData2D
from generate_dataset_2D import bz_average_color
from npdeque import NPDeque

import tensorflow as tf



class CNN(multiprocessing.Process):

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

        # number of dblue frames required for the CA output 1
        self.CA_threshold = 10 # originally 10 I've changed it on 6/1/20
        self.clock = BZClock()

        # to count the number of frames between tocks
        self.framestocks = 0

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
        steph = int(height / 7)

        # where to store the 49 predictions
        predictions = []
        # where to store the position of each cell
        points = []
        # where to store CA frame results, and it will be put in queue
        frame_res = np.zeros((7,7))
        # where to store the individual cell CNN oscillations detection
        indata = []
        # another frame between tocks, add to the counter
        self.framestocks += 1 

        for i in range(7):  # X axis
            for j in range(7):  # y axis
                # top left corner of the current cell (i,j)
                pointA = (x1+14 + stepw * i, y1+14 + steph * j)
                # bottom right corner of the current cell (i,j)
                pointB = (x1-14 + stepw * (i+1), y1-14 + steph * (j+1))
                
                # Define the Region of Interest as the current cell (i, j)
                roi = frame[pointA[1]:pointB[1], pointA[0]:pointB[0]]
                b,g,r = cv2.split(roi)
                roi = cv2.merge((b,r))
                res = cv2.resize(roi,(50,50),interpolation=cv2.INTER_CUBIC)/255.
                res[0][0][0] = float(bkg_color[0])/255.
                res[0][0][1] = float(bkg_color[2])/255.
                indata.append(res)
                points.append( (pointA, pointB) )

        # use the CNN to predict the probabilities
        X = graph.get_tensor_by_name('inputs/X:0')
        Y_proba = graph.get_tensor_by_name('output/Y_proba:0')

        y_probabilities = Y_proba.eval(feed_dict={
            X: np.array(indata).reshape(49,50,50,2)})
                
        for i, y_prob in enumerate(y_probabilities):
            # get the max one
            prediction = np.argmax(y_prob)
            # store it in the deque
            filter_deque.append(i, prediction)
            # assume prediction is the rounded median
            prediction = int(round(np.median(filter_deque.get(i))))
            predictions.append(prediction)

            # Also store it in FSM for CA analysis
            FSM_deque.append(i, prediction)
            # calculate number of dark blues in the last "framestocks" frames
            dark_blues = (FSM_deque.get(i, self.framestocks) == 0).sum()
            
            if dark_blues > self.CA_threshold:
                ca_state = 1
            else:
                ca_state = 0

            frame_res[i//7][i%7] = ca_state

            pointA, pointB = points[i]

            # first paint the CNN prediction
            if prediction == 0:
                # if predicted as 0, paint it dark blue
                cv2.rectangle(frame, pointA, pointB, (180,120,31), -1) 
           
            elif prediction == 1:
                # if predicted as 1, paint it light blue
                cv2.rectangle(frame, pointA, pointB, (227,206,166), -1) 

            else:
                cv2.rectangle(frame, pointA, pointB, (28,26,227), -1)

            # Now pain the CA prediction
            if ca_state == 0: # ca state 0 paint it lblue
                cv2.rectangle(caframe, pointA, pointB, (227,206,166), -1) 
            else: # ca state 1 paint it dblue
                cv2.rectangle(caframe, pointA, pointB, (180,120,31), -1) 

        clock_state = self.clock.update_clock(predictions, 0.)

        if clock_state is 'tock':
            # draw a green square to visualize tock
            cv2.rectangle(frame, (0,0), (800,600), (0,255,0), -1)
            # reset the clock to prepare for next cycle
            self.clock.reset_clock()
            # reset the counter of tocks between frames
            self.framestocks = 0

            # empty the queue were we put the results
            while not self.resq.empty():
                self.resq.get()
            # put results
            self.resq.put_nowait(frame_res)


    def predict_stream(self):

        # vc = cv2.VideoCapture(self.streampath)
        vc = cv2.VideoCapture(0)
        
        vc.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        vc.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        vc.set(cv2.CAP_PROP_BRIGHTNESS, 145)
        vc.set(cv2.CAP_PROP_SATURATION, 255)
        vc.set(cv2.CAP_PROP_CONTRAST, 200)


        click_grid = GridClickData2D()    
        play = True
        #bkg_window = 3000 # number of avg frame colors we will keep
        bkg_window = 300 # number of avg frame colors we will keep
        frame_color = deque(maxlen=bkg_window) # keeps the average color per frame

        videoraw = self.outvideo+".avi"
        videocnn = self.outvideo+"_cnn.avi"
        videoCA = self.outvideo+"_CA.avi"
        fourcc = cv2.VideoWriter_fourcc(*'X264')
        out_raw = cv2.VideoWriter(videoraw, fourcc, 15.0, (800,600))
        out_cnn = cv2.VideoWriter(videocnn, fourcc, 15.0, (800,600))
        out_CA = cv2.VideoWriter(videoCA, fourcc, 15.0, (800,600))


        # to clean the results
        filter_deque = NPDeque(numcells=49, maxLen=30) # originally 1, changed to 10 6/1/20 then 10 for most experiment increasing for BZ life form
        # to store a window of oscillations for CA analysus
        fsm_deque = NPDeque(numcells=49, maxLen=800) 
        frame_counter = 0 

        tf.compat.v1.reset_default_graph()
        config = tf.compat.v1.ConfigProto()
        config.gpu_options.allow_growth = True

        with tf.compat.v1.Session(config=config) as sess:

            saver = tf.compat.v1.train.import_meta_graph("doublepool_data4sept.meta")
            saver.restore(sess, "doublepool_data4sept")

            graph = tf.compat.v1.get_default_graph()

            while(True):
                # if the queue stopsig is not empty, it needs to stop
                if not self.stopsig.empty():
                   break

                if play is True:
                    ret, frame = vc.read()

                if ret is False:
                    break

                # first thing we ask the user to define the 5x5 grid
                # if click_grid.finished is False:
                #   click_grid.get_platform_corners(frame, self.streampath)
                    #time.sleep(10*60) # sleep for 5 min while the reaction gets ready
                # removed click grid, coordinate has been hard coded
                frame_counter +=1
                rawframe = frame.copy()

                # calculate the average color of this frame
                avg_c = bz_average_color(frame, [108,13,663,577]) #[110,15,665,580] last one 

                # save it
                frame_color.append(avg_c)
                # calculate the average color of the last n frames
                window_c = np.average(frame_color, axis=0).astype('float32')

                # "click_grid" is now populated with the x,y corners of the platform
                click_grid.draw_grid(frame)
                # we use the CNN to decide if the cells are painted red or blue
                caframe = frame.copy()
                self.predict_frame(sess, graph, frame, caframe, [108,13,663,577], 

                        window_c, filter_deque, fsm_deque)

                out_raw.write(rawframe)
                out_cnn.write(frame)
                out_CA.write(caframe)

                cv2.imshow("CNN",frame)
                cv2.imshow("CA",caframe)
                cv2.imshow("RAW", rawframe)
                cv2.waitKey(1)

        vc.release()
        out_raw.release()
        out_cnn.release()
        out_CA.release()
        cv2.destroyAllWindows()


    def reset_graph(self, seed=42):
        tf.reset_default_graph()
        tf.set_random_seed(seed)
        np.random.seed(seed)

class BZClock(): 
    ''' this class will analyse the BZ chemical oscillations to
    detect the periodicity of the oscillations. The time it takes
    for a cell to oscillate twice will be our "clock"'''

    def __init__(self, numcells=49):

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
        if len(reds) == 47 and len(tocks)>13 and clock_state == "tick": # original len(reds) == 47 amd len(tock) == 14 ==49 and >6 for energy scan >6 for no fluctuation lifeform
            clock_state = "toTock" # len tock the most recent is >7 # BZ ENERGY ==45 >14
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

    resq = multiprocessing.Queue()
    stopt = multiprocessing.Queue()

    cnn = CNN(kwargs={
        'streampath': invideo, 'outvideo': outvideo,
        'resq': resq, 'stopsig': stopt
        })
    # start the thread
    cnn.start()
    # just wait for 120 seconds while it works on another thread
    #time.sleep(120)
    # resq is where the results are. we can print its size now
    #print(resq.qsize())
    # we put a 1 to this queue to stop the thread
    #stopt.put(1)
    # join to let it 100% finish and clean up.
    cnn.join()
