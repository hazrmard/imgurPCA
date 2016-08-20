__author__ = 'Ibrahim'

import numpy as np
from imgurparse import ImgurParse
import csv


class ImgurTrain:
    def __init__(self):
        self.idlist = []
        self.wordlist = []
        self.data = np.array([])

    def extract(self, datasource):
        """
        get/convert parsed data from file or ImgurParse class.
        Source data must be consolidated (same word keys for all items/posts).
        """
        if type(datasource) == str:
            parseinstance = ImgurParse()
            parseinstance._read_noncumulative(datasource)
            datasource = parseinstance
        randomitem = datasource.worddict.keys()[0]
        self.wordlist = datasource.worddict[randomitem].keys()
        self.idlist = datasource.idlist
        for item in datasource.worddict.keys():

    def pca(self):
        pass

    def custom_vectors(self):
        pass

