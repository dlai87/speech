import json
import pickle
import sys
import os
import subprocess
import re
import csv
from PIL import Image, ImageDraw

ROOT = '/home/sfeng/data/'
DECRYPT_ROOT = '/data/client100prod/'
FFPROBE_PATH = './ffprobe'

CSV_ROOT = './csv/'
IMAGE_ROOT = './img/'

class Video(object):
    def __init__(self, decrypt_video_path, s3_video_path):
        self.decrypt_video_path = decrypt_video_path
        self.s3_video_path = s3_video_path
        self.valid = False
        self.originalDuration = -1
        try:
            self.log_path = self.getLogFile()
            self.valid = True
            self.getIdentity()
        except Exception, e :
            print "*******cannot find********" + str(e)

    def getIdentity(self):
        tokens = self.s3_video_path.split('/')
        #print tokens
        self.trial_id = tokens[1]
        self.patient_id = tokens[2]
        self.schedle_or_dose_id = tokens[3]
        self.date = tokens[4]
        self.questionnaire_id = tokens[5]
        self.question_id = tokens[6]
        self.video_name = tokens[7]


    # private method
    def getLogFile(self):
        logfile = self.s3_video_path.replace('phi/', 'non_phi/')
        path = logfile.rsplit('/',1)[0]
        path = ROOT + path
        files = os.listdir(path)
        paths = [os.path.join(path, basename) for basename in files]
        lastest_file = max(paths, key=os.path.getctime)
        return lastest_file

    # private method 
    def find_between(self, s, first, last ):
        try:
            start = s.index( first ) + len( first )
            end = s.index( last, start )
            return s[start:end]
        except Exception, e:
            return ''

    # private method 
    def getTimeInSec(self, string):
        time = 0
        substr = self.find_between(string, "Duration: ", ", start")
        times = substr.replace(':',' ').replace('.',' ').split()
        time = int(times[3])*10+int(times[2])*1000+(int)(times[1])*60*1000+(int)(times[0])*60*60*1000
        return time/1000.0

    def get_duration(self):
        tokens = self.s3_video_path.split('/')
        filename = DECRYPT_ROOT + tokens[2] + '/' + self.decrypt_video_path
        result = subprocess.Popen([FFPROBE_PATH, filename], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        for line in result.stdout.readlines():
            if "Duration" in line :
                string = line 
                self.originalDuration = self.getTimeInSec(string)
        return self.originalDuration

    def parseSpeechLog(self):
        log_filename = self.log_path
        with open(log_filename) as json_data:
            d = json.load(json_data)
            detectList = self.extractHumanTalking(d)
            promptList = self.extractAudioPrompt(d)
            return detectList, promptList

    # private method 
    def extractHumanTalking(self, d):
        records = d['speechDetectionLog']['SpeechDetectionRecords']
        detectList = [] 
        detection = None
        for record in records:
            if record['type'] == "begin_overall":
                detection = [] 
                detection.append(record['timeInSec'])
            if record['type'] == "end_overall":
                detection.append(record['timeInSec'])
                detectList.append(detection)
        return detectList



    # private  method 
    def extractAudioPrompt(self, d):
        records = d['speechDetectionLog']['SpeechDetectionRecords']
        detectList = [] 
        detection = None
        firstActivateTime = -1; 
        for record in records:
            if record['type'] == "activated":
                detection = [] 
                detection.append(record['timeInSec'])
                if firstActivateTime < 0 : 
                    firstActivateTime = record['timeInSec']
            if record['type'] == "deactivated":
                if detection is not None:
                    detection.append(record['timeInSec'])
                    detectList.append(detection)
        promptList = []
        promptList.append([0, firstActivateTime])   # from 0 sec to first actived , is initial IMA talking
        for i in range(1, len(detectList)): 
            # IMA talking during prompt up instrution 
            promptList.append([detectList[i-1][1], detectList[i][0]])
        return promptList


def createVideoList():
    with open('map_filename_to_s3.pkl', 'rb') as f:
        data = pickle.load(f)
        videoList = []
        for key, value in data.items():
            video = Video(key, value)
            if video.valid : 
                videoList.append(video)
        print len(videoList)
        print len(data.items())
        return videoList


def groupByPatient():
    pass

def groupByQuestionniare():
    pass

def createCSVfile(video, duration, detectList, promptList):
    writepath = CSV_ROOT + video.video_name + '.csv'
    mode = 'a' if os.path.exists(writepath) else 'w'
    with open(writepath, mode) as csvfile: 
        fieldnames = ['time', 'tpye']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for prompt in promptList:
            writer.writerow({'time':prompt[0], 'type':'IMA start'})
            writer.writerow({'time':prompt[1], 'type':'IMA stop'})
        for detection in detectList: 
            writer.writerow({'time':detection[0], 'type':'human start'})
            writer.writerow({'time':detection[1], 'type':'huam stop'})
    pass

def createVisulizeImage(video, duration, detectList, promptList):
    pass 


if __name__ == "__main__":
    videoList = createVideoList()
    for video in videoList:
        duration = video.get_duration()
        detectList, promptList = video.parseSpeechLog()
        print duration
        print detectList
        print promptList
        createCSVfile(video, duration, detectList, promptList)
        print "========================="
