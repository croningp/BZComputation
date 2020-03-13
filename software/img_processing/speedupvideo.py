###############################################################################
#
# This script will speed up all the videos in the given folder.
# It should be called like "python speedupvideo.py path/to/folder speed newdir"
# for example "python speedupvideo experiments/ 15 y"
# path/to/folder is self-explanatory
# speed is the factor. 1 means equal, 2 means twice as fast
# newdir can be y or no. If no new files will be created in the path given.
# if y then a new folder will be created where to put the new files
#
###############################################################################


import subprocess, sys, multiprocessing, glob, os


def speedUpSinglevideo(video, outdir, speedUp, 
        processLimiter=multiprocessing.Lock()):

    _, videoname = os.path.split(video)
    outvideo = outdir + videoname.split(".")[0] + "_fast" + speedUp + ".avi"

    with processLimiter:
        print("Processing video: "+video)
        subprocess.run(["ffmpeg", "-an", "-i", video, "-vcodec", "libx264", 
            "-filter:v", "setpts=PTS/"+speedUp, outvideo])


def speedUpFolder(pathtofolder, speedUp, newdir):
    ''' This function will speed up all the videos in a folder.'''
    
    if newdir == 'y':
        outdir = pathtofolder + "fast" + speedUp + "/"
        try:
            os.makedirs(outdir)
        except FileExistsError:
            pass
    elif newdir == 'n':
        outdir = pathtofolder
    else:
        print("newdir can be 'y' or 'n'")
        raise SystemExit

    s = multiprocessing.Semaphore(4)
    allvideos = glob.glob(pathtofolder+'*.avi')
    for video in allvideos:
        p = multiprocessing.Process(target=speedUpSinglevideo, 
                args=(video, outdir, speedUp, s))
        p.start()


if __name__ == "__main__":
    
    folder = sys.argv[1]
    speedUp = sys.argv[2]
    newdir = sys.argv[3]

    speedUpFolder(folder, speedUp, newdir)
