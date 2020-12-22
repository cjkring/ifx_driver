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

# Create a get function.

def GET(url, headers={}):

  t = str(int(time.time()*1000))
  default_par={
      'client_id':client_id,
      'access_token':res['access_token'],
      'sign':calc_sign(client_id+res['access_token']+t, secret),
      't':t,
      'sign_method':'HMAC-SHA256',  
      }
  r = requests.get(base + url, headers=dict(default_par,**headers))

  r = json.dumps(r.json(), indent=2, ensure_ascii=False) # Beautify the request result format for easy printing and viewing
  return r


# Create a post function.

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


'''
--- Two-way control practice of smart devices ----
'''

# The ID of the associated device in the Cloud Development project.

device_id = '54011042840d8eaf0ee0'
device_id = '3616144040f520097344'

# Get the latest status of the device.

r = GET(url=f'/v1.0/devices/{device_id}/status')
print(r)

# Get control instruction set.

r = GET(url=f'/v1.0/devices/{device_id}/functions')
print(r)

# Issue control commands.

d = {"commands":[{"code":"switch_led","value":True},]}

r = POST(url=f'/v1.0/devices/{device_id}/commands', body=d)
print(r)

# Continuous control.

def turn_on_off(s):
  d = {"commands":[{"code":"switch_led","value":s},]}
  print(d)
  r = POST(url=f'/v1.0/devices/{device_id}/commands', body=d)
  print(r)

#group

r = GET(url=f'/v1.0/device-groups')
r = GET(url=f'/v1.0/homes')
print(r)

delay = 0.5


for i in range(1):
  turn_on_off(True)
  time.sleep(delay)
  turn_on_off(False)
  #time.sleep(delay)