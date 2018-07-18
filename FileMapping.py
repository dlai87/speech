import json
import pickle
import glob
import os

ROOT = '/home/sfeng/data/'
    
class Video(object):
    def __init__(self, decrypt_video_path, s3_video_path):
        self.decrypt_video_path = decrypt_video_path
        self.s3_video_path = s3_video_path
        print "===>"
        try:
            self.log_path = self.getLogFile()
            print self.log_path
            print "FOUND !!!!!!!!!!!!!!!!!!"
        except Exception, e :
            print "*******cannot find********" + str(e)
        print "<==="

    def getLogFile(self):
        logfile = self.s3_video_path.replace('phi/', 'non_phi/')
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
