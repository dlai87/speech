import json
import pickle
import sys
import os
import subprocess
import re
import csv
from PIL import Image, ImageDraw, ImageFont

ROOT = '/home/sfeng/data/'
DECRYPT_ROOT = '/data/client100prod/'
FFPROBE_PATH = './ffprobe'

CSV_ROOT = 'csv/'
IMAGE_ROOT = 'img/'

# UI related 
MARGIN_H = 280
MARGIN_V = 80
PIX_PER_SEC = 50 
LINE_WIDTH = 60
GREEN = (77,175,80,255)
RED = (244,67,54,255)
BLUE = (142,180,232)
LIGHT_BLUE = (162,180,252, 200)
LIGHT_GRAY = (207,216,220, 255)
DARK_GRAY = (60,60,60,255)
WHITE = (255,255,255,255)

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

    def getMetadata(self):
        return 'trial_id:' + str(self.trial_id) + ',\n'\
        + 'patient_id:' + str(self.patient_id) + ',\n'\
        + 'date:' + str(self.date) + ',\n'\
        + 'questionnaire_id:' + str(self.questionnaire_id) + ',\n'\
        + 'question_id:' + str(self.question_id) + ',\n'\
        + 'video_name:' + str(self.video_name) + ',\n'


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
            self.detectList = self.extractHumanTalking(d)
            self.promptList = self.extractAudioPrompt(d)
            self.speech_total = 0 
            for detect in self.detectList:
                self.speech_total += (detect[1] - detect[0])
            self.ttr = self.detectList[0][0] - self.promptList[0][1]
            return self.detectList, self.promptList

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
    if not os.path.exists(writepath):
        os.mknod(writepath)
    with open(writepath, 'w') as csvfile: 
        fieldnames = ['time', 'type', 'metadata']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'metadata':video.getMetadata()})
        for prompt in promptList:
            writer.writerow({'time':prompt[0], 'type':'IMA start'})
            writer.writerow({'time':prompt[1], 'type':'IMA stop'})
        for detection in detectList: 
            writer.writerow({'time':detection[0], 'type':'human start'})
            writer.writerow({'time':detection[1], 'type':'human stop'})

def createVisulizeImage(video, duration, detectList, promptList):
    if detectList[-1][1] > duration:
        duration = detectList[-1][1]
    if promptList[-1][1] > duration:
        duration = promptList[-1][1]
    
    image_width = int ( duration * PIX_PER_SEC + MARGIN_H * 2 )
    image_height = int ( LINE_WIDTH + MARGIN_V * 2 )
    canvas = Image.new('RGBA', (image_width, image_height), LIGHT_GRAY) 
    draw = ImageDraw.Draw(canvas)
    for detection in detectList:
        drawDetection(detection, draw)
    for prompt in promptList:
        drawPrompt(prompt, draw)
    drawPoints(duration, video, draw)
    drawTTR(video, draw)
    writepath = IMAGE_ROOT + video.video_name + '.png'
    canvas.save(writepath)
    pass 


def drawDetection(detection, draw):
    x1 = MARGIN_H + PIX_PER_SEC * detection[0]
    y1 = MARGIN_V + LINE_WIDTH / 2
    x2 = MARGIN_H + PIX_PER_SEC * detection[1]
    y2 = MARGIN_V + LINE_WIDTH / 2
    position = (x1, y1, x2, y2)
    draw.line(position, fill=WHITE, width = LINE_WIDTH)
    position = (x1, y1, x1+5, y2)
    draw.line(position, fill=GREEN, width = LINE_WIDTH)
    position = (x2-5, y1, x2, y2)
    draw.line(position, fill=RED, width = LINE_WIDTH)
    x = x1 + (x2-x1)/3
    y = y1 - 62 
    font = ImageFont.truetype("./font/OpenSans-Regular.ttf", 18)
    draw.text((x,y), str(format(detection[1] - detection[0], '.3f')  ) + 's', font = font,  fill=DARK_GRAY)



def drawPrompt(prompt, draw): 
    x1 = MARGIN_H + PIX_PER_SEC * prompt[0]
    y1 = MARGIN_V + LINE_WIDTH / 2
    x2 = MARGIN_H + PIX_PER_SEC * prompt[1]
    y2 = MARGIN_V + LINE_WIDTH / 2 
    position = (x1, y1, x2, y2)
    draw.line(position, fill=BLUE, width = 10)
    position = (x1, y1, x1+5, y2)
    draw.line(position, fill=BLUE, width = LINE_WIDTH)
    position = (x2-5, y1, x2, y2)
    draw.line(position, fill=BLUE, width = LINE_WIDTH)

def drawPoints(duration, video, draw): 
    upper = MARGIN_V
    left = MARGIN_H - LINE_WIDTH
    lower = MARGIN_V + LINE_WIDTH
    right = MARGIN_H
    draw.ellipse((left, upper, right, lower), fill = GREEN, outline =GREEN)
    left = MARGIN_H + duration * PIX_PER_SEC
    right = left + LINE_WIDTH
    draw.ellipse((left, upper, right, lower), fill = RED, outline =RED)
    draw.line((MARGIN_H, MARGIN_V + LINE_WIDTH/2, MARGIN_H + duration * PIX_PER_SEC, MARGIN_V + LINE_WIDTH/2), fill = LIGHT_BLUE, width = 2)
    x = right + 22
    y = upper + 15
    font = ImageFont.truetype("./font/OpenSans-Regular.ttf", 22)
    draw.text((x,y), str(format(video.originalDuration, '.3f')) + 's total', font = font,  fill=DARK_GRAY)
    font = ImageFont.truetype("./font/OpenSans-Regular.ttf", 18)
    draw.text((x, y + 30), str(format(video.ttr, '.3f')) + 's TTR\n' + str(format(video.speech_total, '.3f')) + 's speech', font = font, fill = DARK_GRAY)


 
def drawTTR(video, draw): 
    prompt = video.promptList[0]
    detection = video.detectList[0]
    x1 = MARGIN_H + prompt[1]*PIX_PER_SEC
    y1 = MARGIN_V + LINE_WIDTH/2
    x2 = MARGIN_H + detection[0]*PIX_PER_SEC
    y2 = MARGIN_V + LINE_WIDTH/2
    draw.line((x1, y1, x2, y2), fill = DARK_GRAY, width = 4)
    x = x1 + (x2-x1)/3
    y = y1 + 50 
    font = ImageFont.truetype("./font/OpenSans-Regular.ttf", 22)
    draw.text((x,y), str(format( video.ttr, '.3f')  ) + 's', font = font,  fill=DARK_GRAY)



if __name__ == "__main__":
    videoList = createVideoList()
    for video in videoList:
        duration = video.get_duration()
        detectList, promptList = video.parseSpeechLog()
        print duration
        print detectList
        print promptList
        createCSVfile(video, duration, detectList, promptList)
        createVisulizeImage(video, duration, detectList, promptList)
        print "========================="
