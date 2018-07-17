import json
import pickle
import glob
import os

ROOT = '/home/sfeng/data/'
    
class Video(object):
    def __init__(self, decrypt_video_path, s3_video_path):
        self.decrypt_video_path = decrypt_video_path
        self.s3_video_path = s3_video_path
        self.log_path = self.getLogFile()
        print "===>"
        print self.log_path
        print "<==="

    def getLogFile(self):
        logfile = self.s3_video_path.replace('phi/', 'non-phi/')
        path = logfile.rsplit('/',1)[0]
        path = ROOT + path + "/*"
        print path
        list_of_files = glob.glob(path)
        lastest_file = max(list_of_files, key=os.path.getctime)
        return lastest_file


def createVideoList():
    with open('map_filename_to_s3.pkl', 'rb') as f:
        data = pickle.load(f)
        for key, value in data.items():
            video = Video(key, value)


if __name__ == "__main__":
    createVideoList()