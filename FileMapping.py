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
        logfile = self.s3_video_path.replace('phi/client100prod_1525443315/', 'non_phi/')
        path = logfile.rsplit('/',1)[0]
        path = ROOT + path
        print path
        files = os.listdir(path)
        print files
        lastest_file = max(files, key=os.path.getctime)
        return lastest_file


def createVideoList():
    with open('map_filename_to_s3.pkl', 'rb') as f:
        data = pickle.load(f)
        for key, value in data.items():
            print key
            print value
            video = Video(key, value)


if __name__ == "__main__":
    createVideoList()