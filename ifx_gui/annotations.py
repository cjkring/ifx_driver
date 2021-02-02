from enum import Enum,unique

@unique
class Annotations(Enum):
     NONE = 'None'
     CALM = 'Calm'
     SITTING = 'Sitting'
     WALKING = 'Walking'
     FALL = 'Fall'