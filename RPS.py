#!/usr/bin/python3

import requests
import uuid
import time
import hashlib
import base64
import hmac
import json

class RPS():
  def __init__(self, accessKeyID=None, accessKeySecret=None):
    self.accessKeyID     = accessKeyID
    self.accessKeySecret = accessKeySecret
    self.nonce           = self.getNonce()
    self.timestamp       = self.getTimeStamp()
    self.url             = 'https://api-dm.yealink.com:8443'

  def getNonce(self):
    return str( uuid.uuid4() )

  def getTimeStamp(self):
    return str( round(time.time()*1000) )

  def getContentMD5(self, body=None):
    if body is None or body=='':
      return None

    return base64.b64encode( hashlib.md5(body.encode()).digest() ).decode()

  def calculateSignature(self, httpMethod='GET', body=None, uri=None, params=None):
    if body is not None:
      headers = "Content-MD5:"    + self.getContentMD5(body) + "\n" + \
                "X-Ca-Key:"       + self.accessKeyID + "\n" + \
                "X-Ca-Nonce:"     + self.nonce + "\n" + \
                "X-Ca-Timestamp:" + self.timestamp
    else:
      headers = "X-Ca-Key:"       + self.accessKeyID + "\n" + \
                "X-Ca-Nonce:"     + self.nonce + "\n" + \
                "X-Ca-Timestamp:" + self.timestamp

    #TODO: maybe remove last \n

    #params = params.split('&')
    formattedQFStr = ''
    first = True
    for p in params:
      #pair = p.split('=')
      if not first:
        formattedQFStr += '&'
      #if len(pair)<2 or pair[1] == '':
      if not params[p]:
        #formattedQFStr += pair[0]
        formattedQFStr += p
      else:
        #formattedQFStr += pair[0] + '=' + pair[0]
        formattedQFStr += p + '=' + params[p]
      first = False

    stringToSign = httpMethod      +"\n" +\
                   headers         + "\n" +\
                   uri.lstrip('/')

    if formattedQFStr != '':
      stringToSign += "\n" + formattedQFStr

    print(stringToSign)
    return base64.b64encode( hmac.new(self.accessKeySecret.encode(), msg=stringToSign.encode(), digestmod=hashlib.sha256).digest() ).decode()

  def sendRequest(self, body=None, method='GET', uri=None, params=''):
    s = requests.Session()

    strBody = None
    if body is not None:
      strBody = json.dumps(body)

    headers = {
              "Content-Type"  : "application/json; charset=utf-8",
              "X-Ca-Key"      : self.accessKeyID,
              "X-Ca-Nonce"    : self.nonce,
              "X-Ca-Timestamp": self.timestamp,
              "X-Ca-Signature": self.calculateSignature(httpMethod=method, body=strBody, uri=uri, params=params),
    }
    if strBody is not None:
      headers["Content-MD5"] = self.getContentMD5(strBody)

    #print(headers)
    url = self.url+uri
    if method=='POST':
      res = s.post(url, headers=headers, data=strBody)
    else:
      res =  s.get(url, headers=headers, params=params)

    self.nonce           = self.getNonce()
    self.timestamp       = self.getTimeStamp()
    return res.json()

  #SERVERS
  def getServerList(self, key=None, skip=0, limit=10, autocount=True):
    body = {"skip":skip,"limit":limit,"autoCount":autocount}
    if key is not None:
      body['key'] = key
    return self.sendRequest(body=body, method='POST', uri='/api/open/v1/server/list')

  def getServerDetails(self, id=None):
    if id is None:
      return None
    return self.sendRequest(method='GET', uri='/api/open/v1/server/detail', params={"id": id})

  def serverExists(self, name=None):
    if name is None:
      return False

    ret = self.sendRequest(method='GET', uri='/api/open/v1/server/checkServerName', params={"serverName": name})
    if ret['ret'] == 1 and ret['error'] is None and ret['data'] == True:
      return True
    else:
      return False

  def editServer(self, id=None, name=None, url=None, authName=None, password=None, certificateURL=None):
    if id is None or name is None or url is None:
      return False

    body = {'id':id, 'serverName': name, 'url': url}
    if authName is not None:
      body['authName'] = authName
    if password is not None:
      body['password'] = password
    if certificateURL is not None:
      body['certificateUrl'] = certificateURL
    return self.sendRequest(body=body, method='POST', uri='/api/open/v1/server/edit')

  def deleteServers(self, ids=None):
    if ids is None:
      return False

    ret = self.sendRequest(body={'ids':ids}, method='POST', uri='/api/open/v1/server/delete')
    if ret['ret'] == 0 and ret['error'] is None and ret['data'] is None:
      return True
    else:
      return False

  def deleteServer(self, id=None):
    if id is None:
      return False

    return self.deleteServers(ids=[id])

  #DEVICES
  def addDevices(self, macs=None, serverId=None, uniqueServerUrl=None, remark=None, authName=None, password=None):
    if macs is None:
      return False

    body = {'macs':macs}
    if serverId is not None:
      body['serverId'] = serverId
    if uniqueServerUrl is not None:
      body['uniqueServerUrl'] = uniqueServerUrl
    if remark is not None:
      body['remark'] = remark
    if authName is not None:
      body['authName'] = authName
    if password is not None:
      body['password'] = password

    return self.sendRequest(body=body, method='POST', uri='/api/open/v1/device/add')

  def addDevice(self, mac=None, serverId=None, uniqueServerUrl=None, remark=None, authName=None, password=None):
    if mac is None:
      return False

    return self.addDevices(macs=[mac], serverId=serverId, uniqueServerUrl=uniqueServerUrl, remark=remark, authName=authName, password=password)

  def getDeviceList(self, key=None, status=None, skip=0, limit=10, autocount=True):
    body = {"skip":skip,"limit":limit,"autoCount":autocount}
    if key is not None:
      body['key'] = key
    if status is not None:
      body['status'] = status
    return self.sendRequest(body=body, method='POST', uri='/api/open/v1/device/list')

  def getDeviceDetails(self, id=None):
    if id is None:
      return None
    return self.sendRequest(method='GET', uri='/api/open/v1/device/detail', params={"id": id})

  def getDeviceStatus(self, mac=None):
    if mac is None:
      return None
    return self.sendRequest(method='GET', uri='/api/open/v1/device/checkDevice', params={"mac": mac})

  def getMacStatus(self, mac=None):
    if mac is None:
      return None
    return self.sendRequest(method='GET', uri='/api/open/v1/device/checkMac', params={"mac": mac})

  def editDevice(self, id=None, serverId=None, uniqueServerUrl=None, remark=None, authName=None, password=None):
    if id is None:
      return False

    body = {'id':id}
    if serverId is not None:
      body['serverId'] = serverId
    if uniqueServerUrl is not None:
      body['uniqueServerUrl'] = uniqueServerUrl
    if remark is not None:
      body['remark'] = remark
    if authName is not None:
      body['authName'] = authName
    if password is not None:
      body['password'] = password
    return self.sendRequest(body=body, method='POST', uri='/api/open/v1/device/edit')

  def migrateDevices(self, ids=None, serverId=None):
    if ids is None or serverId is None:
      return False

    return self.sendRequest(body={'ids':ids, 'serverId': serverId}, method='POST', uri='/api/open/v1/device/migrate')

  def migrateDevice(self, id=None, serverId=None):
    if id is None or serverId is None:
      return False

    return self.migrateDevices(ids=[id], serverId=serverId)

  def deleteDevices(self, ids=None):
    if ids is None:
      return False

    return self.sendRequest(body={'ids':ids}, method='POST', uri='/api/open/v1/device/delete')

  def deleteDevice(self, id=None):
    if id is None:
      return False

    return self.deleteDevices(ids=[id])


