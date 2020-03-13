import cv2


class GridClickData17:
    '''This class represents the data that is passed from and to
    the mouse callback, in order to recognize clicks by the user
    The objective of this class is for the user to mark the corners
    of the grid, so we know its start x,y, width and height.'''


    def __init__(self):
        self.drawing = False # True if mouse is pressed
        self.ix, self.iy = -1, -1 # first click, or top left corner
        self.points = [0, 0, 0, 0] # Platform coordinates
        self.finished = False # True when user releases click


    def grid_callback(self, event, x, y, flags, param):
        '''mouse callback function. See OpenCV documentation example'''

        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.points = [x, y, x, y]
            self.ix, self.iy = x,y

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing == True:
                self.points = [self.ix, self.iy, x, y]

        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            self.points = [self.ix, self.iy, x, y]
            self.finished = True


    def draw_grid(self, frame):
        '''draws a 7x1 grid, just the lines. Used for visualization'''

        x1, y1, x2, y2 = self.points
        cv2.rectangle(frame, (x1,y1), (x2,y2), (0,0,255), 3)
        height = y2 - y1
        width = x2 - x1
        stepw = int(width / 7)
        #steph = int(height / 1)

        for i in range(1, 7):
            cv2.line(frame, (x1+stepw*i,y1),  (x1+stepw*i,y2), (0,0,255), 3)
            #cv2.line(frame, (x1,y1+steph*i),  (x2,y1+steph*i), (0,0,255), 3)


    def get_platform_corners(self, frame, name=""):
        '''Given a frame, it will let the user click on the platform corners
        in order to obtain its coordinates: 
        top left corner, bottom right corner'''

        cv2.namedWindow('Choose grid '+name)
        cv2.setMouseCallback('Choose grid '+name, self.grid_callback)
        unmodified = frame.copy()

        # grid_callback sets finished to True once the user selects both corners
        while(self.finished is False):
            frame = unmodified.copy()
            self.draw_grid(frame)
            cv2.imshow('Choose grid '+name, frame)
            cv2.waitKey(10)

        cv2.destroyWindow('Choose grid '+name)


