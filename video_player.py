#! /usr/bin/env python3

#Author: David Morales
#Course: CS 4375 Theory of Operating Systems
#Instructor: Dr. Eric Freudenthal
#T.A: David Pruitt
#Assignment: Project 3
#Last Modification: 11/02/2020
#Purpose: Video to grayscale

from threading import Thread, Semaphore, Lock
import cv2
import time
import sys
import os.path

frame_count = 0
queue_limit = 10             #The queue size limit as specified in the lab requirements.

class ThreadQueue:           #Created new class to handle the thread put/get operations from the queue (based off of notes)
    def __init__(self, queue_limit):
        self.queue = []                         #Using lists to behave as queues 
        self.qlock = Lock()
        self.full = Semaphore(0)
        self.empty = Semaphore(queue_limit)     #Creates semaphore with queue_limit.


    def put(self, frame):                       #Puts new frames onto the queue
        self.empty.acquire()
        self.qlock.acquire()
        self.queue.append(frame)                #Appends (enqueue) frame onto lists
        self.qlock.release()
        self.full.release()


    def get(self):                              #Pops frames from the queue
        self.full.acquire()
        self.qlock.acquire()
        frame = self.queue.pop(0)
        self.qlock.release()
        self.empty.release()
        return frame                            #Returns frame

class extractFrames(Thread): #This method (thread) is a producer of frames for queue_frame_extraction.
    def __init__(self, filename):
        Thread.__init__(self)
        self.filename = filename
        self.count = 0
    def run(self):
        vidcap = cv2.VideoCapture(self.filename)
        frame_count = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))  #Gets total frames of the video
        success, frame = vidcap.read()                           #Extracts first frame and boolean value (if frame extraction is success)

        while True: 
            if success:                                          #Checks if frame extraction is success and within the frame limit
                queue_frame_extraction.put(frame)                #Within the semaphore, we append the frame to the queue
                success, frame = vidcap.read()                   #Continues to extract frames
                print("Reading frame:", self.count)
                self.count += 1

            if self.count >= frame_count:               #Once the counter reaches the total frame count...
                queue_frame_extraction.put(-1)  #We add -1 to the queue to signal the other threads to end work
                break

        sys.exit(1)

class convertToGrayscale(Thread): #This method (thread) is a consumer of frames (from queue_frame_extraction) and a producer of grayscale frames
    def __init__(self):
        Thread.__init__(self)
        self.count = 0
    def run(self):
        while True:
            frame = queue_frame_extraction.get()  #Pops a frame from the queue within the semaphore

            if type(frame) == int and frame == -1: #Checks frame is -1 to indicate to stop work (exit the loop)
                queue_grayscale.put(-1)            #Adds -1 to queue_grayscale to signal the other thread to end work
                break

            print("Converting frame:", self.count)
            grayscale_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) #Converts frame to grayscale
            queue_grayscale.put(grayscale_frame)                      #Adds grayscale frame to the queue within the semaphore

            self.count += 1

        sys.exit(1)

class displayFrames(Thread): #This method (thread) is a consumer of frames (from queue_grayscale)
    def __init__(self):
        Thread.__init__(self)
        self.delay = 42      #Sets the delay for 42ms as specified in lab requirements
        self.count = 0
    def run(self):
        while True:
            frame = queue_grayscale.get()

            if type(frame) == int and frame == -1:           #Checks frame is -1 to indicate to stop work (exit the loop)
                break

            print("Displaying frame:", self.count)
            cv2.imshow('Video', frame)                       #Displays frame in GUI
            self.count += 1

            if cv2.waitKey(self.delay) and 0xFF == ord("q"): #Waits for 42 ms and check if the user wants to quit
                break

        cv2.destroyAllWindows()                              #Exits and clean up
        sys.exit(1)

if len(sys.argv) < 2 or os.path.isfile(str(sys.argv[1])) == False:  #Just checks user usage
    print("Video file not found or incorrect input. Example: python3 video_player.py filename ")
    sys.exit(0)

filename = str(sys.argv[1]) #Gets filename of video file from command line argument

queue_frame_extraction = ThreadQueue(queue_limit)  #A list of the frames extracted (will behave as a queue)
queue_grayscale = ThreadQueue(queue_limit)         #A list of the grayscale frames (will behave as a queue)

#Runs all the threads to begin consumer/producer frame conversion to grayscale
extract_frames = extractFrames(filename)
extract_frames.start()
convert_frames = convertToGrayscale()
convert_frames.start()
display_frames = displayFrames()
display_frames.start()