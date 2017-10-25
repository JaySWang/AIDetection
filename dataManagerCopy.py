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


def utc2local(utc_st):


    UTC_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
    utc_st = datetime.datetime.strptime(utc_st, UTC_FORMAT)


    now_stamp = time.time()
    local_time = datetime.datetime.fromtimestamp(now_stamp)
    utc_time = datetime.datetime.utcfromtimestamp(now_stamp)
    offset = local_time - utc_time
    local_st = utc_st + offset
    return local_st

   
def initDBConnection():
	global cursor
	global db 
	db = pymysql.connect("localhost","root","","monitor_system" )
	cursor = db.cursor()

def initTableIfNeed():

    sql = """CREATE TABLE POD_METRICS_DATA (
         POD_NAME  CHAR(100) NOT NULL,
         CPU  DOUBLE,
         FILE_SYSTEM DOUBLE,
         MEMORY DOUBLE,  
         NETWORK DOUBLE,
         TIME_STAMP TIMESTAMP)"""
    try:
   # 执行sql语句
        cursor.execute(sql)
        db.commit()
    except Exception:
   # 如果发生错误则回滚
         print("table might exist")
         db.rollback()

    sql = """CREATE TABLE MONITOR_DATA (
         POD_NAME  CHAR(100) NOT NULL,
         CPU  DOUBLE,
         FILE_SYSTEM DOUBLE,
         MEMORY DOUBLE,  
         NETWORK DOUBLE,
         PDF DOUBLE,
         KPI DOUBLE,
         RESULT TINYINT(1),
         TIME_STAMP TIMESTAMP)"""

def insertData(podNameD, cupD, fileD, memoryD, networkD,time):

    time = utc2local(time)

    sql = "INSERT INTO POD_METRICS_DATA(POD_NAME, \
       CPU, FILE_SYSTEM, MEMORY, NETWORK,TIME_STAMP) \
       VALUES ('%s', '%d', '%g', '%g', '%g','%s')" % \
       (podNameD, cupD, fileD, memoryD, networkD,time)
    try:
     # 执行sql语句
        cursor.execute(sql)
        db.commit()
    except Exception:
   # 如果发生错误则回滚
         print(traceback.print_exc())
         db.rollback()

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
            networkD = d['network']
            if cupD!=None and fileD!=None and memoryD!=None and networkD!=None:
                #save data
                insertData(pod['podName'],cupD,fileD,memoryD,networkD,d['time'])

def saveMonitorData(podName,d,result):
    podNameD = podName
    cupD = d['cpu']
    fileD = d['fileSystem']
    memoryD = d['memory']
    networkD = d['network']
    timeD = d['time']
    pdf = result['PDF']
    kpiPdf = result['KPI']

    result = result['result']
    timeD = utc2local(timeD)

    sql = "INSERT INTO MONITOR_DATA(POD_NAME, \
       CPU, FILE_SYSTEM, MEMORY, NETWORK,TIME_STAMP,PDF,KPI,RESULT) \
       VALUES ('%s', '%d', '%g', '%g', '%g','%s','%g','%g','%d')" % \
       (podNameD, cupD, fileD, memoryD, networkD,timeD,pdf,kpiPdf,result)
    try:
     # 执行sql语句
        cursor.execute(sql)
        db.commit()
    except Exception:
   # 如果发生错误则回滚
         print(traceback.print_exc())
         db.rollback()

def drop():
    try:
   # 执行sql语句
        cursor.execute("DROP TABLE IF EXISTS POD_METRICS_DATA")
        db.commit()
        cursor.execute("DROP TABLE IF EXISTS MONITOR_DATA")
        db.commit()
    except Exception:
         print("error")
         db.rollback()


def close():
    cursor.close()
    db.close

def init():
    initDBConnection()
    initTableIfNeed()

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
    sql = "SELECT time_stamp from POD_METRICS_DATA order by time_stamp DESC limit 1"
    cursor.execute(sql)
    result = cursor.fetchone() 

    currentTime = calendar.timegm(time.gmtime())
    if result ==None:
        intervalTime = 2*7*24*60*60 # 2 weeks
    else:
        lastDateTime = result[0]
        print("update data from")
        print(lastDateTime)

        t = lastDateTime.timetuple()
        lastTimeStamp = int(time.mktime(t))  

         # from next min
        lastTimeStamp +=60

        intervalTime = currentTime - lastTimeStamp
    saveData(intervalTime,currentTime)


def getDataByIntervalTime(intervalTime):

    endTime = calendar.timegm(time.gmtime())
    startTime =endTime - intervalTime

    endTime = datetime.datetime.fromtimestamp(endTime)
    startTime = datetime.datetime.fromtimestamp(startTime)

    return getDataByTime(startTime,endTime)
    

def getDataByTime(startTime,endTime):
    condition = 'WHERE time_stamp >= "%s" AND time_stamp<= "%s"' %(startTime,endTime)
    return getData(condition)

def getData(condition=None):
    sql = 'SELECT CPU,FILE_SYSTEM,MEMORY,NETWORK from POD_METRICS_DATA %s '%(condition)
    print(sql)
    cursor.execute(sql)
    results = cursor.fetchall()

    data = []
    for row in results:
        data.append((row[0],row[1],row[2],row[3]))

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

    plt.figure(id)

    data = np.array(data)
    x = np.arange(data.min(),data.max(),binSize) 
    y = normfun(x, data.mean(), data.std())
    plt.plot(x,y)
    plt.hist(data,bins = 200, normed=True)
    plt.title(title)

    if show:
       plt.show()
#pdf
def normfun(x,mu,sigma):
    pdf = np.exp(-((x - mu)**2)/(2*sigma**2)) / (sigma * np.sqrt(2*np.pi))
    return pdf


if __name__ == "__main__":

    initDBConnection()
    #drop()
    initTableIfNeed()
    #dataHistogram('order by time_stamp desc limit 10000')
    updateDB()
    close()

