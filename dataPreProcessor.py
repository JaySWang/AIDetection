
# coding: utf-8

# In[10]:


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


def requestData(uri):
    r = requests.get(uri, cert=('./key/idKey.crt','./key/idKey.key'))
    return r.text

def getCurrentJsonData():
    
    endTime = calendar.timegm(time.gmtime())
    endTime = math.floor(endTime/60)*60-1  # in minute

    interval = 59
    startTime = endTime-interval

    
    cpuData = requestData(constructUri('cpu%2Fusage_rate','sum',startTime,endTime))
    memoryData = requestData(constructUri('memory%2Fusagepercentage','max',startTime,endTime))
    fileSystemData = requestData(constructUri('filesystem%2Fusage','sum',startTime,endTime))
    networkData = requestData(constructNetworkUri('network%2Ftx_rate','sum',startTime,endTime))

    cpuJson = json.loads(cpuData)
    memoryJson = json.loads(memoryData)
    fileSystemJson = json.loads(fileSystemData)
    networkJson = json.loads(networkData)
    
    metricsData = dict()
    pods = list()
    metricsData['pods'] = pods


    for serie in cpuJson['results'][0]['series']:
        pod = dict()
    
        pod['podName'] = serie['tags']['pod_name']
        data = list()
        cpuData = dict()
        cpuData['time'] = serie['values'][0][0]
        cpuData['cpu'] = serie['values'][0][1]
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
                d[0]['memory'] = serie['values'][0][1]    
    
    series = list()
    result = fileSystemJson['results'][0]

    if 'series' in result :
        series = result['series'] 
    
    for serie in series:    
        podName = serie['tags']['pod_name']
        for pod in metricsData['pods']:
            if pod['podName'] == podName:
                d = pod['data']
                d[0]['fileSystem'] = serie['values'][0][1]
    
    series = list()
    result = networkJson['results'][0]

    if 'series' in result :
        series = result['series']

    for serie in series:    
        podName = serie['tags']['pod_name']
        for pod in metricsData['pods']:
            if pod['podName'] == podName:
                d = pod['data']
                d[0]['network'] = serie['values'][0][1]

    print(metricsData) 
    return metricsData
                


# In[11]:

getCurrentJsonData()


# In[3]:




# In[4]:




# In[6]:




# In[8]:




# In[ ]:




# In[ ]:




# In[ ]:



