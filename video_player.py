#! /usr/bin/env python3

#Author: David Morales
#Course: CS 4375 Theory of Operating Systems
#Instructor: Dr. Eric Freudenthal
#T.A: David Pruitt
#Assignment: Project 3
#Last Modification: 11/01/2020
#Purpose: Video to grayscale

from threading import Thread, Semaphore
import cv2
import time
import sys
import os.path

semaphore = Semaphore()     #Creates the semaphores
queue_frame_extraction = []  #A list of the frames extracted (will behave as a queue)
queue_grayscale = []         #A list of the grayscale frames (will behave as a queue)
frame_count = 0
queue_limit = 10             #The queue size limit as specified in the lab requirements.

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
            print("")
            if success and len(queue_frame_extraction) < queue_limit:  #Checks if frame extraction is success and within the frame limit
                semaphore.acquire()
                queue_frame_extraction.append(frame)                   #Within the semaphore, we append the frame to the queue
                semaphore.release()

                success, frame = vidcap.read()                         #Continues to extract frames
                print("Reading frame:", self.count)
                self.count += 1

            elif self.count >= frame_count:               #Once the counter reaches the total frame count...
                semaphore.acquire()
                queue_frame_extraction.append(-1)  #We add -1 to the queue to signal the other threads to end work
                semaphore.release()
                break

        sys.exit(0)

class convertToGrayscale(Thread): #This method (thread) is a consumer of frames (from queue_frame_extraction) and a producer of grayscale frames
    def __init__(self):
        Thread.__init__(self)
        self.count = 0

    def run(self):

        while True:
            if len(queue_frame_extraction) > 0 and len(queue_grayscale) < queue_limit: #Checks if there's frames in the queue and within the limit
                semaphore.acquire()
                frame = queue_frame_extraction.pop(0)  #Pops a frame from the queue within the semaphore
                semaphore.release()

                if type(frame) == int and frame == -1: #Checks frame is -1 to indicate to stop work (exit the loop)
                    semaphore.acquire()
                    queue_grayscale.append(-1)         #Adds -1 to queue_grayscale to signal the other thread to end work
                    semaphore.release()
                    break

                print("Converting frame:", self.count)
                grayscale_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) #Converts frame to grayscale
                semaphore.acquire()
                queue_grayscale.append(grayscale_frame)                   #Adds grayscale frame to the queue within the semaphore
                semaphore.release()

                self.count += 1

        sys.exit(0)

class displayFrames(Thread): #This method (thread) is a consumer of frames (from queue_grayscale)
    def __init__(self):
        Thread.__init__(self)
        self.delay = 42      #Sets the delay for 42ms as specified in lab requirements
        self.count = 0

    def run(self):

        while True:
            if len(queue_grayscale) > 0:                         #Checks if frames in the queue
                semaphore.acquire()
                frame = queue_grayscale.pop(0)
                semaphore.release()

                if type(frame) == int and frame == -1:           #Checks frame is -1 to indicate to stop work (exit the loop)
                    break

                print("Displaying frame:", self.count)
                cv2.imshow('Video', frame)                       #Displays frame in GUI
                self.count += 1

                if cv2.waitKey(self.delay) and 0xFF == ord("q"): #Waits for 42 ms and check if the user wants to quit
                    break

        cv2.destroyAllWindows()                                  #Exits and clean up
        sys.exit(0)

if len(sys.argv) < 2 or os.path.isfile(str(sys.argv[1])) == False:  #Just checks user usage
    print("Video file not found or incorrect input. Example: python3 video_player.py filename ")
    sys.exit(0)

filename = str(sys.argv[1]) #Gets filename of video file from command line argument

#Runs all the threads to begin consumer/producer frame conversion to grayscale
extract_frames = extractFrames(filename)
extract_frames.start()
convert_frames = convertToGrayscale()
convert_frames.start()
display_frames = displayFrames()
display_frames.start()