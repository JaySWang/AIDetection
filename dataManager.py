import pymysql
import sys
import json
import traceback

import time
import calendar
import datetime

import dataCollector as dc
import modelBuilder as mb

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import math

import model.OrmManager as orm

from model.OrmManager import Task,Model,ModelFeature,Feature,FeatureData,Record,Data
from sqlalchemy import desc,or_

# from KMeans import *
from sklearn.cluster import KMeans

import numpy as np
from decimal import *

import click



def utc2local(utc_st):


    UTC_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
    utc_st = datetime.datetime.strptime(utc_st, UTC_FORMAT)


    now_stamp = time.time()
    local_time = datetime.datetime.fromtimestamp(now_stamp)
    utc_time = datetime.datetime.utcfromtimestamp(now_stamp)
    offset = local_time - utc_time
    local_st = utc_st + offset
    return local_st

def insertData(podNameD, cupD, fileD, memoryD,memoryWSD, networkD,requestCountD,time):
    features = ['cpu','fileSystem','memory','memoryWS','network','requestCount']
    values = [cupD, fileD, memoryD,memoryWSD, networkD,requestCountD]
    s = orm.getSession()

    time = utc2local(time)
    
    data = Data()
    data.time = time
    data.pod = podNameD
    data.monitoring = False
    index = 0
    for f in features:
        featureInDB = s.query(Feature).filter(Feature.name == f).first()
        if featureInDB == None:
           featureInDB = Feature()
           featureInDB.name = f
           s.add(featureInDB)
        featureData = FeatureData()
        featureData.data = data
        featureData.feature_name= featureInDB.name
        featureData.value = values[index]

        index+=1

    s.add(data)
    s.commit()

def saveDataUtilNow(intervalTime):
    endtime = calendar.timegm(time.gmtime())
    return saveData(intervalTime,endtime)

def saveData(intervalTime,endtime):
    rawData = dc.getJsonData(intervalTime,endtime)
    saveRawData(rawData)

def saveRawData(rawData):
    for pod in rawData['pods']:
        data = pod['data']
        for j in range(len(data)):
            d = data[j]
            cupD = d['cpu']
            fileD = d['fileSystem']
            memoryD = d['memory']
            memoryWSD = d['memoryWS']
            networkD = d['network']
            requestCountD = None
            if 'requestCount' in d:
                requestCountD = d['requestCount']
            if cupD!=None or fileD!=None or memoryD!=None or memoryWSD!=None or networkD!=None or requestCountD!=None:
                #save data
                insertData(pod['podName'],cupD,fileD,memoryD,memoryWSD,networkD,requestCountD,d['time'])

def initDBConnection():
    orm.init()

def saveDataEveryMin():
    while True:
        try:
            print ("saving data")
            saveDataUtilNow(60)

        except Exception:
             print (Exception)
             print('save data error')
        time.sleep(60) 

def updateDB():
    s = orm.getSession()
    result = s.query(Data).filter(or_(Data.monitoring == None,Data.monitoring == False)).order_by(desc(Data.time)).first()
    currentTime = calendar.timegm(time.gmtime())
    # currentTime = 1504337101
    if result ==None:
        intervalTime = 2*7*24*60*60 # 2 weeks
        #intervalTime = 10*60
    else:
        lastDateTime = result.time

        t = lastDateTime.timetuple()
        lastTimeStamp = int(time.mktime(t))  

         # from next min
        lastTimeStamp +=60
        print("update data from")
        print(lastDateTime)
        intervalTime = currentTime - lastTimeStamp
    
    saveData(intervalTime,currentTime)

def getDataByIntervalTime(intervalTime):

    endTime = calendar.timegm(time.gmtime())
    startTime =endTime - intervalTime

    endTime = datetime.datetime.fromtimestamp(endTime)
    startTime = datetime.datetime.fromtimestamp(startTime)

    return getDataForModelByTime(startTime,endTime)
    

def getDataForModelByTime(startTime,endTime):
    data = []
    s = orm.getSession()
    print ("from ",startTime)
    print ("to ",endTime)

    dataResult = s.query(Data).filter(Data.time >= startTime).filter(Data.time <= endTime).filter(Data.monitoring==False).all()
    print ("loaded ",len(dataResult)," data")

    for d in dataResult:
        dataItem = {}
        for fd in d.featureData:
            dataItem[fd.feature_name] = fd.value
        data.append(dataItem)   
    return data

def getDataByTime(startTime,endTime):
    data = []
    s = orm.getSession()
    print ("from ",startTime)
    print ("to ",endTime)

    dataResult = s.query(Data).filter(Data.time >= startTime).filter(Data.time <= endTime).filter(Data.monitoring==False).all()
    print ("loaded ",len(dataResult)," data")

    for d in dataResult:
        dataItem = {}
        for fd in d.featureData:
            dataItem[fd.feature_name] = fd.value
        dataItem['id'] = d.id
        data.append(dataItem)

    return data


def dataHistogram(condition = None):
    cupData = []
    fileData = []
    memoryData = []
    networkData = []

    data = getData(condition)
    for d in data:
        cd,fd,md,nd = d[0],d[1],d[2],d[3]
        cd,fd,md,nd = mb.processData(cd,fd,md,nd)
        cupData.append(cd)
        fileData.append(fd)
        memoryData.append(md)
        networkData.append(nd)

    cupData = mb.normalizeDataSet(cupData)
    fileData = mb.normalizeDataSet(fileData)

    memoryData = mb.normalizeDataSet(memoryData)
    networkData = mb.normalizeDataSet(networkData) 

    showFigure(1,cupData,"cupData")    
    showFigure(2,fileData,"fileData")  
    showFigure(3,memoryData,"memoryData")    
    showFigure(4,networkData,"network")    
    plt.show()


def showFigure(id=1,data=[],title="none",binSize = 0.001,show=False):
    print ('showing feature')
    plt.figure(id)

    data = np.array(data)
    x = np.arange(data.min(),data.max(),binSize) 
    y = normfun(x, data.mean(), data.std())
    plt.plot(x,y)
    plt.hist(data,bins = 200, normed=True)
    plt.title(title)
    
    print ('drawing')

    if show:
       plt.show()
#pdf
def normfun(x,mu,sigma):
    print ('calculating pdf')
    pdf = np.exp(-((x - mu)**2)/(2*sigma**2)) / (sigma * np.sqrt(2*np.pi))
    return pdf

def save(obj):
    s = orm.getSession()
    s.add(obj)
    s.commit()
    # s.close()

def getById(ctype,id):
     s = orm.getSession()
     obj = s.query(ctype).filter(ctype.id == id).first()
     return obj


def showRequestFigureByTime(featureName,startTimeStamp,endTime,dataUnitSize=1,windowSize=10):
    data = getDataForModelByTime(startTime,endTime)
    showRequestFirgure(featureName,data,dataUnitSize,windowSize)

 

def showRequestFigureByIntervalTime(featureName,intervalTime,dataUnitSize=1,windowSize=10):
    data = getDataByIntervalTime(intervalTime)
    showRequestFirgure(featureName,data,dataUnitSize,windowSize)
  
def showRequestFirgure(featureName,data,dataUnitSize,windowSize):
    requestCounts = []
    x = []
    y = []
    i = 0 
    
    for i in range(0,int((len(data)/dataUnitSize))):
        requestValue = 0;

        for j in range(0,dataUnitSize):
            l=0
            k = dataUnitSize*i+j
            d = data[k]
            if d[featureName] != None:
                requestValue+=d[featureName]
                l+=1
       
        if l !=0:
           yValue =  (requestValue/l)*dataUnitSize
           x.append(i)
           y.append(int(yValue))


    windowSize = 10

    subFigureCount = int(len(x)/windowSize)

    plt.figure(figsize=(4,8),dpi=100)
    plt.title(featureName)
    plt.ylabel(featureName)  
    plt.xlabel('time unit/'+str(dataUnitSize))  



    for b in range(0,int(len(x)/windowSize)):

        p = plt.subplot(subFigureCount,1,b+1)

        if(windowSize*(b+1)<len(x)):
            p.plot(x[(windowSize*b):(windowSize*(b+1))],y[(windowSize*b):(windowSize*(b+1))])
    plt.show()

def close():
    orm.close()


def getTrainningData(windowSize, featureName,startTimeS,endTimeS):
    startTime = datetime.datetime.strptime(startTimeS,'%Y-%m-%d  %H:%M:%S')
    endTime = datetime.datetime.strptime(endTimeS,'%Y-%m-%d  %H:%M:%S')
    data = getDataByTime(startTime,endTime);

    sampleData = []
    for i in range(0,len(data)):
        d = data[i]
        if(d[featureName]!= None):
            sampleData.append(d[featureName])
        else:
            print("something wroing")

    return sampleData

def trainning(startTimeS,endTimeS,startTest, endTest,windowSize,ksize):

    featureName = 'requestCount'


    trainningData = getTrainningData(windowSize,featureName,startTimeS,endTimeS)
    td = initTrainnigData(trainningData,windowSize)
    # td = moving_average(trainningData)
    # td = chunks(td,windowSize)

    td = np.array(td)

    # kmeans = KMeans(n_clusters=ksize, random_state=0,init='random',n_init=10).fit(td)
    kmeans = KMeans(n_clusters=ksize, random_state=0,init='random',n_init=1).fit(td)

    clusters = kmeans.cluster_centers_


    normalKmeans = getNormalKMeans(kmeans,td,ksize,windowSize)

    # print(clusters)
    # print(kmeans.labels_)
    for i in range(0,len(kmeans.labels_)):
        if kmeans.labels_[i] in stdevs:
           evs = stdevs[kmeans.labels_[i]]
           evs.append(getDiff(clusters[kmeans.labels_[i]],td[i]))

        else:
           evs = []
           evs.append(getDiff(clusters[kmeans.labels_[i]],td[i]))
           stdevs[kmeans.labels_[i]] = evs


    for k in stdevs:
        mean =  np.mean(stdevs[k])
        var = np.var(stdevs[k])
        stdevMeans[k] = mean.quantize(Decimal('0.00'))
        stdevVars[k] = var.quantize(Decimal('0.00'))  

    # print(kmeans.inertia_)


    # print(kmeans.predict([[0,0,0], [4, 14,7]]))
    # print(kmeans.cluster_centers_)



    plt.figure(figsize=(4,8),dpi=100)
    plt.title("requestCount")
    plt.ylabel("requestCount")  



    testSample = getTrainningData(windowSize,featureName,startTest,endTest);
    testSample = initTestData(testSample,windowSize)

    x = []
    for j in range(0,windowSize):
        x.append(j)

    p = plt.subplot(2,1,1)
    legend = []
    for i in range(0,len(clusters)):
        p.plot(x,clusters[i])
        if(i in stdevs):
            legend.append("group "+str(i)+" with "+str(len(stdevs[i]))+" data" +"   stdev mean:"+str(stdevMeans[i])+" stdev vars:"+str(stdevVars[i]))
        else:
            legend.append("group "+str(i)+" with 0 data")

    plt.legend(legend, loc='upper left')


    p = plt.subplot(2,1,2)

    legend = []
    for j in range(0,len(testSample)):
        predictGroup = kmeans.predict([testSample[j]])
        t = " belongs to" + str(predictGroup)+" with stdev:"+str(getDiff(clusters[predictGroup][0],testSample[j]))
        print("test data ",j,t)
        print("there are ", str(len(stdevs[predictGroup[0]])), " data in group ",predictGroup," with stdev mean:",str(stdevMeans[predictGroup[0]])," stdev vars:",str(stdevVars[predictGroup[0]]))
        print(" ")

        p.plot(x,testSample[j])
        legend.append(t)

    plt.legend(legend, loc='upper left')

 
    # plt.show()


    taskData['normalKmeans'] = normalKmeans
    taskData['kmeans'] = kmeans
    taskData['testData'] = testSample


    return kmeans

def getNormalKMeans(kmeans,td,ksize,windowSize):

    print("inertia_/dataSize:",kmeans.inertia_/len(td))

    print("----remove anormaly data------")
    anormalyGroup = {}
    dataGroup = {}

    normalTd = []
    normalKPI = (len(td)/ksize)*0.05
    print("kpi:",normalKPI)

    # count the data of each label
    for i in range(0,len(kmeans.labels_)):
        if kmeans.labels_[i] in dataGroup:
           dataGroup[kmeans.labels_[i]] = dataGroup[kmeans.labels_[i]]+1
        else:
           dataGroup[kmeans.labels_[i]]=1

    # find anormaly group with little data
    for i in range(0,len(td)):
        if (dataGroup[kmeans.labels_[i]]>=normalKPI):
            normalTd.append(td[i])
        else:
            if kmeans.labels_[i] not in anormalyGroup:
               anormalyGroup[kmeans.labels_[i]]= []
            anormalyGroup[kmeans.labels_[i]].append(td[i])
            anormalyGroups.append(td[i])


    # print (normalTd)


    print("anormaly groups:",len(anormalyGroup))
    for i in anormalyGroup:
        print ("group:",i," with ",len(anormalyGroup[i])," data")
        showAnormalyGroup(i,normalKPI,anormalyGroup[i],windowSize,kmeans)




    print("current normal data size:",len(normalTd))
    ksize = ksize-len(anormalyGroup)
    normalKmeans = KMeans(n_clusters=ksize, random_state=0,init='random',n_init=1).fit(np.array(normalTd))

    if(len(anormalyGroup)==0):
        print("final normal data size:",len(normalTd))
        print("final normal k size:",ksize)
        return normalKmeans
    else:
        return getNormalKMeans(normalKmeans,normalTd,ksize,windowSize)

    return normalKmeans



def initTrainnigData(data,windowSize):
    td = []
    for i in range(windowSize,len(data),1):
        td.append(data[i-windowSize:i])

    print("trainning data inited")
    print("size",len(td))
    return td

def initTestData(data,windowSize):
    td = []
    for i in range(windowSize,len(data),windowSize):
        td.append(data[i-windowSize:i])

    print("test data inited")
    print("size",len(td))
    return td

def moving_average(a,n=5):
    ret = np.cumsum(a,dtype = float)
    ret[n:]=ret[n:]-ret[:-n]
    return ret[n-1:]/n

def chunks(a,n):
    twoDArray = []
    for i in range(n,len(a),n):
        subArray = a[i-n:i]
        twoDArray.append(subArray.tolist()) 
    return twoDArray

def getDiff(center,sample):

    sum = Decimal(0);
    for i in range(0,len(center)):
        sum+=np.square((Decimal(center[i])-Decimal(sample[i])))
    sum=sum/Decimal(len(center))
    sum = np.sqrt(sum)

    return sum.quantize(Decimal('0.00'))


def showAnormalyGroup(group,normalKPI,anormalyData,windowSize,kMeans):

    clusters = kMeans.cluster_centers_

    plt.figure(figsize=(4,8),dpi=100)
    plt.title(" anormaly requestCount")
    plt.ylabel("requestCount")  


    x = []
    for j in range(0,windowSize):
        x.append(j)


    p = plt.subplot(2,1,1)
    legend = []

    print(group)
    print(clusters)
    p.plot(x,clusters[group])
    legend.append("group "+str(group)+" is anormaly with only "+str(len(anormalyData))+" data;KPI is "+str(normalKPI) )


    plt.legend(legend, loc='upper left')
    
    p = plt.subplot(2,1,2)

    legend = []
    for j in range(0,len(anormalyData)):
            p.plot(x,anormalyData[j])

    plt.legend(legend, loc='upper left') 

    # plt.show()



def showGroup(group,windowSize,testSample=None,km = "kmeans"):

    print(km)

    clusters = taskData[km].cluster_centers_

    plt.figure(figsize=(4,8),dpi=100)
    plt.title("requestCount")
    plt.ylabel("requestCount")  


    if(testSample==None):
       print("possible?") 
       testSample = taskData['testData']

    x = []
    for j in range(0,windowSize):
        x.append(j)


    p = plt.subplot(2,1,1)
    legend = []
    p.plot(x,clusters[group])
    if(group in stdevs):
       legend.append("group "+str(group)+" with "+str(len(stdevs[group]))+" data" +"  stdev mean:"+str(stdevMeans[group])+" stdev vars:"+str(stdevVars[group]) )
    else:
        legend.append("group "+str(group)+" with 0 data")

    plt.legend(legend, loc='upper left')


    p = plt.subplot(2,1,2)

    legend = []
    for j in range(0,len(testSample)):
        predictGroup = taskData[km].predict([testSample[j]])[0]
        if(predictGroup==group):
            p.plot(x,testSample[j])
            print(clusters[predictGroup])
            t = "belongs to" + str(predictGroup)+" with stdev:"+str(getDiff(clusters[predictGroup],testSample[j]))
            legend.append(t)

    plt.legend(legend, loc='upper left') 
    plt.show()


# -----------gloable values
taskData={}
args = []
stdevs = {}
stdevMeans = {}
stdevVars = {}
anormalyGroups =[]

def save_start(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    args.append(value)
    getEndTime()

def save_end(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    args.append(value)
    getTestStartTime()

def save_test_start(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    args.append(value)
    getTestEndTime()


def save_test_end(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    args.append(value)
    getWindowSize()

def save_window_size(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    args.append(value)
    getKSize()

def save_k_size(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    args.append(value)
    beginTrainning()


def save_group(ctx, param, value):
    if value ==-1:
        del args[:]
        getStartTime()
    elif value ==-2:
        testInputData()
    elif value ==-3:
        testInputDataWithNormalKmeans()  
    elif value ==-4:
        selectNormalGroup() 

    showGroup(value,args[4])
    selectGroup()

def save_normal_group(ctx, param, value):
    if value ==-1:
        del args[:]
        getStartTime()
    elif value ==-2:
        testInputData()
    elif value ==-3:
        testInputDataWithNormalKmeans() 
    elif value ==-4:
        selectGroup()   

    showGroup(value,args[4],km="normalKmeans")
    selectNormalGroup()

def save_test_data(ctx, param, value):
    if value =='-1':
        selectGroup()  
    test_test_data(value)

def save_test_data_with_normal(ctx, param, value):
    if value =='-1':
       selectNormalGroup()  

    test_test_data(value,"normalKmeans")

def test_test_data(value,kmeansType="kmeans"):
    testSampleGroup = []
    testSample = []
    data = value.split( )
    for d in data :
        dint = int(d)
        testSample.append(dint)

    testSampleGroup.append(testSample)
    print(testSample)
    print(kmeansType)

    predictGroup = taskData[kmeansType].predict([testSample])[0]
    print(predictGroup)
    showGroup(predictGroup,args[4],testSampleGroup,kmeansType)
    if(kmeansType=="kmeans"):
       testInputData()  
    else:
       testInputDataWithNormalKmeans()

# @click.command()
# @click.option('--start', prompt='trainning start time',callback=save_args)
# @click.option('--end', prompt='trainning end time',callback=save_args)
# @click.option('--starttest', prompt='testing start time',callback=save_args)
# @click.option('--endtest', prompt='testing end time',callback=save_args)
# def initUI(start, end,starttest, endtest):

#     # trainning(start,end,starttest, endtest)
#     print(start,end,starttest, endtest)


@click.command()
@click.option('--start', prompt='trainning start time',callback=save_start)
def getStartTime(start, end,starttest, endtest):

    # trainning(start,end,starttest, endtest)
    print(start,end,starttest, endtest)


@click.command()
@click.option('--end', prompt='trainning end time',callback=save_end)
def getEndTime(end):
    # trainning(start,end,starttest, endtest)
    print(start,end,starttest, endtest)


@click.command()
@click.option('--teststart', prompt='testing start time',callback=save_test_start)
def getTestStartTime(teststart):

    # trainning(start,end,starttest, endtest)
    print(teststart)


@click.command()
@click.option('--testend', prompt='testing end time',callback=save_test_end)
def getTestEndTime(testend):

    # trainning(start,end,starttest, endtest)
    print(testend)


@click.command()
@click.option('--groupsize',prompt='data window size',type=int,callback=save_window_size)
def getWindowSize(groupsize):

    # trainning(start,end,starttest, endtest)
    print(groupsize)

@click.command()
@click.option('--ksize',prompt='k value',type=int,callback=save_k_size)
def getKSize(ksize):
    print(ksize)


@click.command()
@click.option('--group', prompt='which gourp do you want to see ',type=int,callback=save_group)
def selectGroup(group):

    # trainning(start,end,starttest, endtest)
    print(group)

@click.command()
@click.option('--group', prompt='which normal gourp do you want to see ',type=int,callback=save_normal_group)
def selectNormalGroup(group):

    # trainning(start,end,starttest, endtest)
    print(group)


@click.command()
@click.option('--group', prompt='please enter test data(same window size)',type=str,callback=save_test_data)
def testInputData(data):

    # trainning(start,end,starttest, endtest)
    print(data)

@click.command()
@click.option('--group', prompt='please enter test data normal(same window size)',type=str,callback=save_test_data_with_normal)
def testInputDataWithNormalKmeans(data):

    # trainning(start,end,starttest, endtest)
    print(data)


def beginTrainning():
    print(args)
    trainning(args[0],args[1],args[2], args[3],args[4],args[5])
    selectGroup()



if __name__ == "__main__":

    initDBConnection()

    #getDataByIntervalTime(5*24*60*60)
    #d rop()
    #i nitTableIfNeed()
    #dataHistogram('order by time_stamp desc limit 10000')

    # updateDB()

    # showRequestFigure(3*7*24*60*60)

    # startTimeS = "2017-09-06 1:0:0"
    # endTimeS = "2017-09-06 5:0:0"
    # startTime = datetime.datetime.strptime(startTimeS,'%Y-%m-%d  %H:%M:%S')
    # endTime = datetime.datetime.strptime(endTimeS,'%Y-%m-%d  %H:%M:%S')

    # featureName = 'requestCount'
    # # featureName = 'network'
    # dataUnitSize = 1

    # windowSize = 20

    # showRequestFigureByTime(featureName,startTime,endTime,dataUnitSize,windowSize)


    # startTimeS = "2017-09-04 0:0:0"
    # endTimeS = "2017-09-06 0:0:0"


    # startTimeS = "2017-09-6 0:0:0"
    # endTimeS = "2017-09-6 3:0:0"

    getStartTime()

    orm.close()
