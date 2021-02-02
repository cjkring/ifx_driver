# Authorization key obtained from Cloud Development project.

client_id = 'jjpdyfw5a6c58bdqkjz2'
secret = '5abfd5decc78431fbcb4b560ea04c075'

# The user of each interface should call the corresponding interface according to the region where it is located.
# The endpoint URL list:
# China https://openapi.tuyacn.com 
# Americas https://openapi.tuyaus.com 
# Europe https://openapi.tuyaeu.com 
# India https://openapi.tuyain.com

base ='https://openapi.tuyaus.com'

# Signature algorithm.

def calc_sign(msg,key):
  import hmac
  import hashlib

  sign = hmac.new(msg=bytes(msg, 'latin-1'),key = bytes(key, 'latin-1'), digestmod = hashlib.sha256).hexdigest().upper()
  return sign


import time
import requests
t = str(int(time.time()*1000))
r = requests.get(base+'/v1.0/token?grant_type=1',
                 headers={
                    'client_id':client_id,
                    'sign':calc_sign(client_id+t, secret),
                    'secret':secret,
                    't':t,
                    'sign_method':'HMAC-SHA256',
                  })

res = r.json()['result']
print(res)

import json

# Get function.

def GET(url, headers={}):

  t = str(int(time.time()*1000))
  default_par={
      'client_id':client_id,
      'access_token':res['access_token'],
      'sign':calc_sign(client_id+res['access_token']+t, secret),
      't':t,
      'sign_method':'HMAC-SHA256',  
      }
  print(default_par)
  r = requests.get(base + url, headers=dict(default_par,**headers))

  r = json.dumps(r.json(), indent=2, ensure_ascii=False) # Beautify the request result format for easy printing and viewing
  return r


# Post function.

def POST(url, headers={}, body={}):
  import json
  t = str(int(time.time()*1000))

  default_par={
      'client_id':client_id,
      'access_token':res['access_token'],
      'sign':calc_sign(client_id+res['access_token']+t, secret),
      't':t,
      'sign_method':'HMAC-SHA256',  
      }
  r = requests.post(base + url, headers=dict(default_par,**headers), data=json.dumps(body))

  r = json.dumps(r.json(), indent=2, ensure_ascii=False) # Beautify the request result format for easy printing and viewing
  return r

def calc_dist_value( distance, min, max):
    if distance < min:
        ratio =  1.0
    elif distance > max:
        ratio =  0.0
    else:
        ratio =  (( 1 - (( distance - min )/( max - min ))) // 0.2) * 0.2

    #print( min,",",max,",",distance,",",ratio)
    return ratio

# base device class
class tuya_device():

  device_id = 0

  def __init__(self, device_id):
     self.device_id = device_id

  def on(self):
      print("Not implemented")

  def off(self):
      print("Not implemented")

  def brightness(self):
      print("Not implemented")

  def status(self):
      r = GET(url=f'/v1.0/devices/{self.device_id}/status')
      print(r)

  def functions(self):
      r = GET(url=f'/v1.0/devices/{self.device_id}/functions')
      print(r)

          

# bulb-specific class
class tuya_bulb(tuya_device):

  def __init__(self, device_id, on_max=2, on_min=1, off_max=3, off_min=2):
      self.on_off_state = -1
      self.dist_state = 0
      self.on_max = on_max
      self.on_min = on_min
      self.off_max = off_max
      self.off_min = off_min
      super().__init__(device_id)

  def registerTagDist( self, distance ):
    
      on_value = calc_dist_value( distance, self.on_min, self.on_max)
      off_value = calc_dist_value( distance, self.off_min, self.off_max)
      if on_value > self.dist_state:
          self.dist_state = on_value
          self.brightness(int(self.dist_state * 100))
          self.on()
          print( distance,",",self.on_off_state,",",self.dist_state * 100)
      elif off_value < self.dist_state:
          self.dist_state = off_value
          self.brightness(int(self.dist_state * 100))
          self.off()
          print( distance,",",self.on_off_state,",",self.dist_state * 100)

  def on(self):
      if self.on_off_state == 1:
          return
      self.on_off_state = 1
      d = {"commands":[{"code":"switch_led","value":True},]}
      r = POST(url=f'/v1.0/devices/{self.device_id}/commands', body=d)
      print(r)

  def off(self):
      if self.on_off_state == 0:
          return
      self.on_off_state = 0
      d = {"commands":[{"code":"switch_led","value":False},]}
      r = POST(url=f'/v1.0/devices/{self.device_id}/commands', body=d)
      print(r)

  def brightness(self,value):
      print("brightness:", value)
      d = {"commands":[{"code":"bright_value","value":value},]}
      r = POST(url=f'/v1.0/devices/{self.device_id}/commands', body=d)
      print(r)

#device-groups -- need to test

# r = GET(url=f'/v1.0/device-groups')
# r = GET(url=f'/v1.0/homes')
# print(r)

# testing

# import array
# bulbs = array.array('o',[ tuya_bulb('3616144040f520097344'),
#                         tuya_bulb('3616144040f5200a1fd1'),
#                         tuya_bulb('3616144040f52011edbd'),
#                         tuya_bulb('3616144010521c47418b'),
#                         tuya_bulb('3616144040f52009b8c0'),
#                         tuya_bulb('3616144040f52009be4c'),
#                         tuya_bulb('3616144040f52012759d'),
#                         tuya_bulb('3616144010521c472a9e'),
#                         tuya_bulb('3616144040f52012d547'),
#                         tuya_bulb('3616144040f52013580e'),
#                         tuya_bulb('3616144040f52012ede4'),
#                         tuya_bulb('3616144010521c4718db'),
#                         tuya_bulb('36k16144040f5200a4f4b'),
#                         tuya_bulb('3616144040f5200e651e'),
#                         tuya_bulb('3616144040f5200e674a')])

# for bulb in bulbs:
#     bulb.on()
#     time.sleep(0.5)
#     bulb.off()
#     time.sleep(0.5)
bulb1 = tuya_bulb('3616144040f520097344')
bulb1.status()
#bulb2 = tuya_bulb('3616144040f5200a1fd1')
#bulb3 = tuya_bulb('3616144040f52011edbd')
#bulb = rgbcw4 = tuya_bulb('3616144010521c47418b')
#bulb = rgbcw5 = tuya_bulb('3616144040f52009b8c0')
#bulb = rgbcw6 = tuya_bulb('3616144040f52009be4c')
#bulb = rgbcw7 = tuya_bulb('3616144040f52012759d')
#bulb = rgbcw8 = tuya_bulb('3616144010521c472a9e')
#bulb = rgbcw9 = tuya_bulb('3616144040f52012d547')
#bulb = rgbcw10 = tuya_bulb('3616144040f52013580e')
#bulb = rgbcw11 = tuya_bulb('3616144040f52012ede4')
#bulb = rgbcw12 = tuya_bulb('3616144010521c4718db')
#bulb = rgbcw13 = tuya_bulb('36k16144040f5200a4f4b')
#bulb = rgbcw14 = tuya_bulb('3616144040f5200e651e')
#bulb = rgbcw15 = tuya_bulb('3616144040f5200e674a')
#bulb.on()
#time.sleep(0.5)
#bulb.off()
#time.sleep(0.5)
#bulb.on()
#time.sleep(0.5)
#bulb.off()

#bulb1.off()
#import numpy as np
#
#for dist in np.arange(20.0,1.0,-0.1):
#    bulb1.registerTagDist(dist)
#    time.sleep(0.1)
#for dist in np.arange(1.0,20.0,0.1):
#    bulb1.registerTagDist(dist)
#    time.sleep(0.1)
# bulb3.off()
# time.sleep(1)
# bulb3.on()
# time.sleep(1)
# bulb3.off()
# time.sleep(1)
# bulb3.on()
# bulb1.status()
# bulb1.functions()
# time.sleep(1.0)
# bulb1.on()
# time.sleep(1.0)
# bulb1.off()
# bulb2.off()
# bulb3.off()
# time.sleep(1.0)
# bulb1.on()
# bulb2.on()
# bulb3.on()
# time.sleep(1.0)
# bulb1.off()
# bulb2.off()
# bulb3.off()
# time.sleep(1.0)
# bulb1.on()
# bulb2.on()
# bulb3.on()
# bulb1.brightness(30)
# bulb1.brightness(50)
# bulb1.brightness(70)
# bulb1.brightness(90)
# bulb1.brightness(110)
# bulb1.brightness(130)
# bulb1.brightness(200)
# bulb1.brightness(255)
# bulb2.brightness(30)
# bulb2.brightness(90)
# bulb2.brightness(30)
# bulb2.brightness(30)
# bulb2.brightness(90)
# bulb2.brightness(255)
# bulb1.off()
# bulb2.off()
# bulb3.off()
