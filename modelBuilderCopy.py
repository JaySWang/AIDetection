
from scipy.stats import multivariate_normal
import numpy as np
import dataCollector as dc
import json
import math
import dataManager


# feature = ["cpu","file","memory","network"]
numOfData = 0 
maxValues=[]
model = {}

def initData(intervalTime):

    data = dataManager.getDataByIntervalTime(intervalTime)

    global numOfData

    #init 2d array
    dataSet = [[0 for col in range(1)] for row in range(4)]
    #del 0
    del dataSet[0][0]
    del dataSet[1][0]
    del dataSet[2][0]
    del dataSet[3][0]

    numOfData =  len(data)

    for j in range(numOfData):
        d = data[j]
        cupD = d[0]
        fileD = d[1]
        memoryD = d[2]
        networkD = d[3]

        cupD,fileD,memoryD,networkD = processData(cupD,fileD,memoryD,networkD)

        dataSet[0].insert(j,cupD)
        dataSet[1].insert(j,fileD)
        dataSet[2].insert(j,memoryD)
        dataSet[3].insert(j,networkD)

    print("initData done with ")
    print(numOfData)

    return dataSet


def processData(cupD,fileD,memoryD,networkD):

    cupD = math.log2(cupD)
    fileD = math.log10(fileD)
    memoryD = math.log2(memoryD)
    networkD = math.log10(networkD)

    return cupD,fileD,memoryD,networkD


def initDist(dataSet):
    

    cpuData = np.array(dataSet[0])

    fileData = np.array(dataSet[1])

    memoryData = np.array(dataSet[2])

    networkData = np.array(dataSet[3])

    data= np.vstack((cpuData,fileData,memoryData,networkData))

    mu = np.mean(data,axis=1,dtype =np.float32)
    print("means")
    print(mu)
    
    cor = np.corrcoef(data)
    print("correlation")
    print(cor)
    
    chol = (np.cov(data,bias=True))
    print("cov")
    print(chol)
    
    dist = multivariate_normal(mean=mu, cov=chol, allow_singular=True)
    print("init Dist done")
    return dist

def getDataSample(dataSet,i):
    dataSample = []
    dataSample.append(dataSet[0][i])
    dataSample.append(dataSet[1][i])
    dataSample.append(dataSet[2][i])
    dataSample.append(dataSet[3][i])
    return dataSample

def getPdf(dist,data):
    return dist.pdf(data)

def getPdfProductSet(dist,dataSet):
    pdfProductSet = []
    for i in range(numOfData):
        pdf = getPdf(dist,getDataSample(dataSet,i))
        pdfProductSet.append(pdf)

    return pdfProductSet    

def initModel(intervalTime,kpi=0.0001):
    

    
    dataManager.init()
    dataSet = initData(intervalTime)
    dataSet = normalizeDataItemSet(dataSet)
    dist = initDist(dataSet)
    pdfProductSet = getPdfProductSet(dist,dataSet)
    dataManager.showFigure(data = pdfProductSet,title = "PDF",binSize = 10,show=True)

    pdfProductSet = np.sort(pdfProductSet)
    kpiIndex = math.floor(len(pdfProductSet)*kpi)

    kpiPdf = pdfProductSet[kpiIndex]

    minPdf = min(pdfProductSet)
    maxPdf = max(pdfProductSet)
    a = np.array(pdfProductSet)
    meanPdf = np.mean(a)

    print ("min")
    print (minPdf)

    print ("max")
    print (maxPdf)

    print ("mean")
    print (meanPdf)

    print ("kpi")
    print (kpiPdf)


    global model
    model = {'dist':dist,'KPI':kpiPdf}

    print(" init model done")
    return model

def normalizeDataItemSet(dataSet):
    global maxValues
    for i in range(len(dataSet)):
        featureData = dataSet[i]
        maxValue = max(featureData)
        maxValues.insert(i,maxValue)
        for j in range(len(featureData)):
            data = featureData[j]
            data = data/maxValue
            featureData[j] = data

    return dataSet   

def normalizeDataItem(cupD,fileD,memoryD,network):


    cupD = cupD/maxValues[0]
    fileD =fileD/maxValues[1]
    memoryD =memoryD/maxValues[2]
    network =network/maxValues[3]


    return cupD,fileD,memoryD,network  

def normalizeDataSet(dataSet):
    normalizedDataSet = []
    maxValue = max(dataSet)
    for d in dataSet:
        nd = d/maxValue
        normalizedDataSet.append(nd)

    return normalizedDataSet

def checkData(cupD,fileD,memoryD,networkD):
    cupD,fileD,memoryD,networkD = processData(cupD,fileD,memoryD,networkD)
    cupD,fileD,memoryD,networkD = normalizeDataItem(cupD,fileD,memoryD,networkD)
    currentPdf = getPdf(model['dist'],[cupD,fileD,memoryD,networkD])
    kpiPdf = model['KPI']
    print("current pdf:")
    print(currentPdf)
    result ={}
    result['PDF'] = currentPdf
    result['KPI'] = kpiPdf

    if currentPdf > kpiPdf:
         result['result'] = True
    else: 
         print("warning")
         print("kpi pdf:")
         print(kpiPdf)
         result['result'] = False
         
    return result

def close():
    dataManager.close()

if __name__ == "__main__":
    initModel(2*7*24*60*60,0.0001)
    checkData(6, 1654160000, 74.1612, 7854.78)
    close()



