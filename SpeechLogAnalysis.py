import json
import sys
import os
import subprocess
import re
from PIL import Image, ImageDraw

COLOR_TALKING = (0,123,180, 50)
COLOR_IMA = (255,0,0, 50)
COLOR_RULER = (100,100,100,255)
PIX_PER_SEC = 50 
MARGIN = 50
LINE_WIDTH = 15

FFPROBE_PATH = './ffprobe'
AUDIO_FILE = '/home/lei/Desktop/speech_analysis/logfiles/test.mp3'


PROMPT_DICT = {
"no_response_prompt1":2,
"no_response_prompt2":3,
"short_response_prompt1":2,
"short_response_prompt2":2,
"move_on_prompt":2
}



"""

"""
def process(audio_filename, log_filename): 
    duration = get_duration(audio_filename)
    print duration
    detectList , promptList = parseSpeechLog(log_filename)

"""
Get the total record duration from the file. 
If the total duration can be recorded in the JSON file in the future, then we don't need this step. 
"""
def get_duration(filename):
    # valid for any audio file accepted by ffprobe
    args = (FFPROBE_PATH, "-show_entries", "format=duration", "-i", filename)
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = popen.communicate()
    match = re.search(r"[-+]?\d*\.\d+|\d+", output)
    return float(match.group())

"""
Parsing JSON log file into : 

1) a summary file in csv format 
2) a image to visualize the data 

"""
def parseSpeechLog(log_filename):
    with open(log_filename) as json_data:
        d = json.load(json_data)
        detectList = extractHumanTalking(d)
        promptList = extractAudioPrompt(d)
        visualize(detectList, promptList)
        return detectList, promptList

"""
def drawHuamnTalkingSegment():
    pass 

def drawImaTalkingSegment():
    pass

def drawStartEnd():
    pass

def combineMultipleImages(image_list):
    pass
"""



def extractHumanTalking(d):
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

def extractAudioPrompt(d):
    promptList = []
    try : 
        audioPrompt = d['audioPromptLog']
        if audioPrompt is not None:
            promptLogs = audioPrompt['logs']
            for log in promptLogs:
                promptList.append([log['occurTimeInSec'] , PROMPT_DICT[log['audioPromptType']]])
    except: 
        print("audioPromptLog dosen't exist.")
    return promptList


def visualize(detectionList, promptList):
    length = 0 
    for detection in detectionList:
        if detection[1] > length:
            length = detection[1] 
    for prompt in promptList:
        if prompt[0] > length: 
            length = prompt[0]

    length = PIX_PER_SEC * length + MARGIN * 2


    canvas = Image.new('RGBA', ((int)(length), MARGIN * 2), (255, 255, 255, 255)) 
    draw = ImageDraw.Draw(canvas) 
    for detection in detectionList: 
        position = getUISegment(detection)
        draw.line(position, fill=COLOR_TALKING, width=LINE_WIDTH)
    for prompt in promptList:
        position = getUIPixel(prompt[0])
        draw.line(position, fill=COLOR_IMA, width=LINE_WIDTH)
    drawRuler(draw, detectionList[-1][1])

    canvas.show()
    canvas.save("result_patient2.png")
    return canvas

def drawRuler(draw, endtime): 
    for i in range(int(endtime) + 1):
        w = 4 if i % 5 == 0 else 2
        position = getUIMarkPixel(i, w)
        draw.line(position, fill=COLOR_RULER, width = w)
    
    
def getUIMarkPixel(point, width):
    x = MARGIN + PIX_PER_SEC * point
    y = MARGIN * 2
    return (x, y, x , y - width*3)


def getUIPixel(time):
    x = MARGIN + PIX_PER_SEC * time
    y = MARGIN
    return (x, y, x + LINE_WIDTH, y) 

def getUISegment(tiem_range):
    x1 = MARGIN + PIX_PER_SEC * tiem_range[0]
    y1 = MARGIN
    x2 = MARGIN + PIX_PER_SEC * tiem_range[1]
    y2 = MARGIN
    return (x1, y1, x2, y2)


if __name__ == "__main__":
   # duration = get_duration('/home/lei/Desktop/speech_analysis/logfiles/test.mp3')
   # print duration
   # parseSpeechLog("logfiles/ios.log")
    process("/home/lei/Desktop/speech_analysis/logfiles/test.mp3", "logfiles/ios.log" ) 