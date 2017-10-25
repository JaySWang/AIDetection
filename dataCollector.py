# coding: utf-8
import requests
import time
import math
import calendar
import json

#ur.urlopen('https://www.zhihu.com')

#requests.get('https://delta.sapanywhere.io/api/datasources/proxy/2/query?db=k8smetrics&q=SHOW%20TAG%20VALUES%20FROM%20%22uptime%22%20WITH%20KEY%20%3D%20%22namespace_name%22&epoch=ms')
#ur.urlopen('https://delta.sapanywhere.io/api/datasources/proxy/2/query?db=k8smetrics&q=SHOW%20TAG%20VALUES%20FROM%20%22uptime%22%20WITH%20KEY%20%3D%20%22namespace_name%22&epoch=ms')

def constructUri(feature,aggregate,startTime,endTime):
    uriPre = 'https://delta.sapanywhere.io/api/datasources/proxy/2/query?db=k8smetrics&q=SELECT%20AGGREGATE(%22value%22)%20FROM%20%22FEATURE%22%20WHERE%20%22type%22%20%3D%20%27pod_container%27%20AND%20%22namespace_name%22%20%3D~%20%2Fus%24%2F%20AND%20%22pod_name%22%20%3D~%20%2F%5Eattachment%2F%20AND%20%22container_name%22%20%3D~%20%2F%5Eattachment%24%2F%20AND%20time%20%3E%3D%20'
    uriPre = uriPre.replace('FEATURE',feature)
    uriPre = uriPre.replace('AGGREGATE',aggregate)
    startTime = str(startTime)
    uriMid = 's%20and%20time%20%3C%20'
    endTime = str(endTime)
    uriEnd = 's%20GROUP%20BY%20time(60s)%2C%20%22container_name%22%2C%20%22namespace_name%22%2C%20%22pod_name%22%20fill(null)' 
    uri = uriPre+startTime+uriMid+endTime+uriEnd
    return uri

def constructNetworkUri(feature,aggregate,startTime,endTime):
    uriPre = 'https://delta.sapanywhere.io/api/datasources/proxy/2/query?db=k8smetrics&q=SELECT%20AGGREGATE(%22value%22)%20FROM%20%22FEATURE%22%20WHERE%20%22type%22%20%3D%20%27pod%27%20AND%20%22namespace_name%22%20%3D~%20%2Fus%24%2F%20AND%20%22pod_name%22%20%3D~%20%2F%5Eattachment%2F%20AND%20time%20%3E%3D%20'
    uriPre = uriPre.replace('FEATURE',feature)
    uriPre = uriPre.replace('AGGREGATE',aggregate)
    startTime = str(startTime)
    uriMid = 's%20and%20time%20%3C%20'
    endTime = str(endTime)
    uriEnd = 's%20GROUP%20BY%20time(60s)%2C%20%22container_name%22%2C%20%22namespace_name%22%2C%20%22pod_name%22%20fill(null)' 
    uri = uriPre+startTime+uriMid+endTime+uriEnd

    return uri

def constructCountUri(startTime,endTime):
    uriPre = 'https://delta.sapanywhere.io/api/datasources/proxy/3/query?db=appmetrics&q=SELECT%20sum(%22increment-count%22)%20%20FROM%20%22servlet-response-status-meter%22%20WHERE%20%22landscape%22%20%3D~%20%2F%5Eus%24%2F%20AND%20%22namespace%22%20%3D~%20%2F%5Eus%24%2F%20AND%20%22service%22%20%3D~%20%2F%5Eattachment%24%2F%20AND%20%22uri%22%20%3D~%20%2F%5E*%24%2F%20AND%20%22method%22%20%3D~%20%2F%5E(DELETE%7CGET%7CPOST)%24%2F%20AND%20%22X_Tenant_ID%22%20%3D~%20%2F%5E*%24%2F%20AND%20time%20%3E%3D%20'
    startTime = str(startTime)
    uriMid = 's%20and%20time%20%3C%20'
    endTime = str(endTime)
    uriEnd = 's%20GROUP%20BY%20time(60s)%2C%20%22host%22%20fill(none)' 
    uri = uriPre+startTime+uriMid+endTime+uriEnd
    return uri
def requestData(uri):
    try:
        proxies = { "http": "http://"+'10.58.32.55:8080', "https": "http://"+"10.58.32.55:8080"}
        r = requests.get(uri, cert=('./key/idKey.crt','./key/idKey.key'), proxies=proxies)
        return r.text
    except Exception as e:
        print("error getting",uri,e)
        return "{}"

def getCurrentJsonData():
    interval =60
    return getJsonData(interval)
    
def getJsonData(intervalInSec,endTime = None):

    if endTime ==None:
       endTime = calendar.timegm(time.gmtime())

    endTime = math.floor(endTime/60)*60-1  # in minute

    startTime = endTime-intervalInSec+1

    countData = requestData(constructCountUri(startTime,endTime))
    cpuData = requestData(constructUri('cpu%2Fusage_rate','mean',startTime,endTime))

    memoryData = requestData(constructUri('memory%2Fusagepercentage','mean',startTime,endTime))
    memoryDataWS = requestData(constructUri('memory%2Fworking_set','mean',startTime,endTime))
    fileSystemData = requestData(constructUri('filesystem%2Fusage','mean',startTime,endTime))
    networkData = requestData(constructNetworkUri('network%2Frx_rate','mean',startTime,endTime))
    cpuJson = json.loads(cpuData)
    memoryJson = json.loads(memoryData)
    memoryWSJson = json.loads(memoryDataWS)

    fileSystemJson = json.loads(fileSystemData)
    networkJson = json.loads(networkData)
    countJson = json.loads(countData)
    
    metricsData = dict()
    pods = list()
    metricsData['pods'] = pods
    
    series = list()
    result = cpuJson['results'][0]
    
    if 'series' in result :
        series = result['series'] 
        
    for serie in series:
        pod = dict()
    
        #init podName when processing the first feature(cup)
        pod['podName'] = serie['tags']['pod_name']
        data = list()
        for value in serie['values'] :
            cpuData = dict()
            cpuData['time'] = value[0]
            cpuData['cpu'] = value[1]
            data.append(cpuData)
    
        pod['data']=data   
        pods.append(pod)    
        
    series = list()
    result = memoryJson['results'][0]

    if 'series' in result :
        series = result['series'] 
    
    for serie in series:    
        podName = serie['tags']['pod_name']
        for pod in metricsData['pods']:
            if pod['podName'] == podName:
                d = pod['data']
                dataIndex = 0
                for value in serie['values']:
                    d[dataIndex]['memory'] = value[1]
                    dataIndex+=1
    series = list()
    result = memoryWSJson['results'][0]

    if 'series' in result :
        series = result['series'] 
    
    for serie in series:    
        podName = serie['tags']['pod_name']
        for pod in metricsData['pods']:
            if pod['podName'] == podName:
                d = pod['data']
                dataIndex = 0
                for value in serie['values']:
                    d[dataIndex]['memoryWS'] = value[1]
                    dataIndex+=1  


    series = list()
    result = fileSystemJson['results'][0]

    if 'series' in result :
        series = result['series'] 
    
    for serie in series:    
        podName = serie['tags']['pod_name']
        for pod in metricsData['pods']:
            if pod['podName'] == podName:
                d = pod['data']
                dataIndex = 0
                for value in serie['values']:
                    d[dataIndex]['fileSystem'] = value[1]
                    dataIndex+=1
    
    series = list()
    result = networkJson['results'][0]

    if 'series' in result :
        series = result['series']

    for serie in series:    
        podName = serie['tags']['pod_name']
        for pod in metricsData['pods']:
            if pod['podName'] == podName:
                d = pod['data']
                dataIndex = 0
                for value in serie['values']:
                    d[dataIndex]['network'] = value[1]
                    dataIndex+=1

    series = list()
    result = countJson['results'][0]

    if 'series' in result :
        series = result['series']

    for serie in series:    
        podName = serie['tags']['host']
        for pod in metricsData['pods']:
            if pod['podName'] == podName:
                d = pod['data']
                dataIndex = 0
                for value in serie['values']:
                    d[dataIndex]['requestCount'] = value[1]
                    dataIndex+=1

    return metricsData

if __name__ == "__main__":
    result = getCurrentJsonData()
    print (result)
