import json
import pickle
import glob
import os

ROOT = '/home/sfeng/data/'
    
class Video(object):
    def __init__(self, decrypt_video_path, s3_video_path):
        self.decrypt_video_path = decrypt_video_path
        self.s3_video_path = s3_video_path
        self.valid = False
        print "===>"
        try:
            self.log_path = self.getLogFile()
            print self.log_path
            print "FOUND !!!!!!!!!!!!!!!!!!"
            self.valid = True
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
        paths = [os.path.join(path, basename) for basename in files]
        lastest_file = max(paths, key=os.path.getctime)
        return lastest_file


def createVideoList():
    with open('map_filename_to_s3.pkl', 'rb') as f:
        data = pickle.load(f)
        videoList = []
        for key, value in data.items():
            print key
            print value
            video = Video(key, value)
            if video.valid : 
                videoList.append(video)
        print len(videoList)
        print len(data.items())


if __name__ == "__main__":
    createVideoList()
