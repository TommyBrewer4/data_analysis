from common import *
#from constants import *

"""class json_file_reader(object):

    def __init__(self,**kwargs):
        self.file_name = None
        self.file_path = None
    
    def check_file_info(self):
        if file_path == None:
            try:

    def __enter__(self):
        pass
    def __exit__(self,exc_type,exc_val,tb):
        print('bye') 

with test() as t:
    pass"""

t = 'F:\Program Files (x86)\DAEMON Tools Pro\Plugins\Grabbers\ertlah.csv'
d = 'F:\Program Files (x86)\DAEMON Tools Pro\Plugins\Grabbers\ertlah'
t2 = regex_file_path(t,1)
t3 = regex_file_ext(t)
t4 = has_path(t)
t5 = has_file(t)
t6 = has_file(d)
print('done')