from fnmatch import fnmatch
import os
import pickle
import matplotlib.pyplot as plt
import matplotlib.image as img
import shutil

class AbstractLevel(object):
    """Defines attributes and methods common to Sortie, Mission, and Event classes"""

    pattern_dictionary = {}
    pattern_dictionary['GPS-Baro-Pre'] = 'GPS-Baro-Preflight*.csv'
    pattern_dictionary['GPS-Baro-Post'] = 'GPS-Baro-Postflight*.csv'
    pattern_dictionary['GPS-Baro-Stats'] = 'GPS-Baro-Stats*.txt'
    pattern_dictionary['summary'] = 'FX*text_summary.txt'

    def __init__(self):
        self.path = ''
        self.path_dictionary = {}
        self.event_number = None
        self.date = None
        '''Date that related to the object'''
        self.flight_time = None
        self.var_pre = None
        self.var_post = None
        self.nickname = ''

    def analyze(self):
        return False

    def find_data(self):
        """Finds all files that match the object's pattern_dictionary and adds their paths to path_dictionary"""
        self.path_dictionary = {}
        # Loops through all entries in this directory
        for fn in os.listdir(self.path):
            # For each item in the directory, checks to see if it matches any patterns from pattern_dictionary
            for key,value in self.pattern_dictionary.iteritems():

                # If the file name matches a pattern, the absolute path to the file is added/appended to its associated
                #  key
                if fnmatch(fn,value):
                    self.path_dictionary.setdefault(key,[]).append(os.path.join(self.path,fn))
        return True

    def show_image(self, image_type):
        """Shows the image specified by image_type
        image_type is a key in pattern_dictionary. The specified image will be shown.
        Example: MyObject.show_image('altitude_graph')
        """
        image_path = self.path_dictionary[image_type][0]
        open_image = img.imread(image_path)
        plt.imshow(open_image)
        plt.show()
        return open_image

    def save(self, name='save'):
        """Saves the object as a .pickle file. It can be reloaded with unpickle"""
        save_name = name + '.pickle'
        with open(os.path.join(self.path, save_name), 'w') as file_obj:
            pickle.dump(self,file_obj)

    @staticmethod
    def load(path):
        """Loads a .pickle object"""
        return pickle.load(path)

    def copy_file(self,file_type,output,overwrite=False):
        """Moves the file(s) designated by file_type to the "output" directory"""

        file_to_move = self.path_dictionary[file_type][0]
        file_name = os.path.split(file_to_move)[-1]
        if not os.path.exists(output):
            os.makedirs(output)
        if not os.path.isdir(output):
            output = os.path.split(output)[0]
        destination_path = os.path.join(output,file_name)
        if (not os.path.isfile(destination_path)) or overwrite:
            shutil.copy(file_to_move,destination_path)

        return destination_path

    @staticmethod
    def show():
        """Shows the specified figure. Method exists to extend pyplot-like interface"""
        plt.show()

