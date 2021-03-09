from enum import Enum
from config import read_config, validate_config

def getAnnotations():
     return addToAnnotations.annotations

def addToAnnotations(new_annos):
     # new_annos is a list, need to add
     last = max([a.value for a in addToAnnotations.annotations])
     for n in new_annos:
          if n:
               last += 1
               addToAnnotations.anno_dict[n]=last

     addToAnnotations.annotations = Enum('annotations', addToAnnotations.anno_dict)

addToAnnotations.anno_dict = {'EXISTING':0, 'NONE':1}
addToAnnotations.annotations = Enum('annotations', addToAnnotations.anno_dict)

if  __name__ == "__main__":

    config = read_config()
    validate_config(config)
    config_annos = config['app']['annotations']
    addToAnnotations(config_annos)
    for a in addToAnnotations.annotations:
        print(a)
         
    new_annos = ['kicking', 'screaming']
    addToAnnotations(new_annos)
    for a in addToAnnotations.annotations:
        print(a)
     
