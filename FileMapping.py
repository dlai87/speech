import json
import pickle
import sys
import os
import subprocess
import re
from PIL import Image, ImageDraw

ROOT = '/home/sfeng/data/'
FFPROBE_PATH = './ffprobe'



class Video(object):
    def __init__(self, decrypt_video_path, s3_video_path):
        self.decrypt_video_path = decrypt_video_path
        self.s3_video_path = s3_video_path
        self.valid = False
        try:
            self.log_path = self.getLogFile()
            self.valid = True
        except Exception, e :
            print "*******cannot find********" + str(e)

    def getLogFile(self):
        logfile = self.s3_video_path.replace('phi/', 'non_phi/')
        path = logfile.rsplit('/',1)[0]
        path = ROOT + path
        files = os.listdir(path)
        paths = [os.path.join(path, basename) for basename in files]
        lastest_file = max(paths, key=os.path.getctime)
        return lastest_file

    def getLength(self):
        filename = self.decrypt_video_path
        result = subprocess.Popen([FFPROBE_PATH, filename],
        stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        return [x for x in result.stdout.readlines() if "Duration" in x]


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


if __name__ == "__main__":
    videoList = createVideoList()
    for video in videoList:
        print video.get_duration()
