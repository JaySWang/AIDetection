
from scipy.stats import multivariate_normal
import numpy as np
import dataCollector as dc
import json
import math
import dataManager

import time
import calendar
import datetime

import model.OrmManager as orm
from model.OrmManager import Task,Model,ModelFeature,Feature,FeatureData,Record,Data


global distMap
distMap = {}

def initData(features,startTime,endTime):

    data = dataManager.getDataForModelByTime(startTime,endTime)
    
    modelFeatureSize = len(features)
   
    #init 2d array
    dataSet = [[0 for col in range(1)] for row in range(modelFeatureSize)]
    #del 0
    for i in range(modelFeatureSize):
         del dataSet[i][0]

    for d in data:
        validation = True
        
        for mFeature in features:
            if mFeature.feature.name not in d:
               validation = False
               break
 
            value = d[mFeature.feature.name]
            fromLimit = mFeature.value_from
            toLimit = mFeature.value_to

            if value>=fromLimit and (value<toLimit or toLimit==-1 ):
                pass
            else:
            # value validation failed
               validation = False
               break;

        if validation:
            for k in range(len(features)):
                 f = features[k]
                 value = d[f.feature.name]
                 value = processData(value,f.process_method)
                 dataSet[k].append(value)

    numOfData = len(dataSet[0])
    print("initData done with ",numOfData," data")

    return dataSet


def processData(value,process_method):
    if process_method =="":
        value = math.fabs(value)
    # +1 to avoid math error
    elif process_method == 'log2':
       value = math.log2(value+1)
    elif process_method == 'log10':
       value = math.log10(value+1)

    return value


def initDist(model,dataSet):
    
    dataGroup = []

    for i in range(len(model.features)):

       dataGroup.append(np.array(dataSet[i]))

    data= np.vstack(dataGroup)

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

def getDataSample(model,dataSet,i):
    dataSample = []
    for j in range(len(model.features)):
          dataSample.append(dataSet[j][i])
    return dataSample

def getPdf(dist,data):
    return dist.pdf(data)

def getPdfProductSet(model,dist,dataSet):
    pdfProductSet = []
    for i in range(len(dataSet[0])):
        pdf = getPdf(dist,getDataSample(model,dataSet,i))
        pdfProductSet.append(pdf)

    return pdfProductSet    

def initModel(s,startTime,endTime,featureConfig,description = None,kpi=0.0001):
    print("init modle:",description)

    model = Model()
    initModelFeatures(s,model,featureConfig)
    dataManager.initDBConnection()
    dataSet = initData(model.features,startTime,endTime)
    dataSet = normalizeDataItemSet(model.features,dataSet)
    dist = initDist(model,dataSet)
    pdfProductSet = getPdfProductSet(model,dist,dataSet)


    # dataManager.showFigure(data = pdfProductSet,title = "PDF",binSize = 10,show=True)

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

    model.description = description
    model.kpi_index = kpi
    model.data_time_from = startTime
    model.data_time_to = endTime
    model.max_pdf = maxPdf
    model.min_pdf = minPdf
    model.mean_pdf = meanPdf
    model.kpi_pdf = kpiPdf
    model.dist = dist

    print(" init model done")
    print("kpi-------init",model.kpi_pdf)

    return model

def initModelByInterval(s,intervalTime,featureConfig,description = None,kpi=0.0001):

    endTime = calendar.timegm(time.gmtime())
    startTime =endTime - intervalTime

    endTime = datetime.datetime.fromtimestamp(endTime)
    startTime = datetime.datetime.fromtimestamp(startTime)
    return initModel(s,startTime,endTime,featureConfig,description,kpi)
 

def initModelFeatures(s,model,featureConfig):
    # featureConfig = {"cpu":["log2",10,-1],"file":["log10",0,-1],"memory":["log2",0,-1],"network":["log10",0,-1]}

    for key,values in  featureConfig.items():
        name = key
        feature = s.query(Feature).filter(Feature.name == name).first()
        if feature == None:
            feature = Feature()
            feature.name = name
        modelFeature = ModelFeature()

        modelFeature.feature = feature
        modelFeature.process_method = values[0]
        modelFeature.value_from = values[1]
        modelFeature.value_to = values[2]
        model.features.append(modelFeature)

def normalizeDataItemSet(features,dataSet):
    for i in range(len(dataSet)):
        featureData = dataSet[i]
        maxValue = max(featureData)
        modelFeature = features[i]
        modelFeature.max_value = maxValue
        modelFeature.min_value = min(featureData)

        for j in range(len(featureData)):
            featureData[j] = normalizeDataItem(featureData[j],modelFeature.max_value)

    return dataSet   

def normalizeDataItem(value,max_value):
    value = value/float(max_value)
    return value  

def normalizeDataSet(dataSet):
    normalizedDataSet = []
    maxValue = max(dataSet)
    for d in dataSet:
        nd = d/maxValue
        normalizedDataSet.append(nd)

    return normalizedDataSet

def checkDataWithModel(model,data):
    dataItem = []
    for mf in model.features:
        rawValue = data.get(mf.feature_name)
        rawValue = processData(rawValue,mf.process_method)
        rawValue = normalizeDataItem(rawValue,mf.max_value)
        dataItem.append(rawValue)

    dist = distMap[model.id]
    currentPdf = dist.pdf(dataItem)
    kpiPdf = model.kpi_pdf

    result ={}
    result['pdf'] = currentPdf
    result['kpi'] = kpiPdf

    if currentPdf > kpiPdf:
         result['result'] = True
    else: 
         result['result'] = False

    return result

def filterDataByConfig(data,featureConfig):
    dataSet = []

    for d in data:
        valid = True
        for key in featureConfig.keys():
           if key in d:
               processMethod = featureConfig[key][0]
               fromLimit = featureConfig[key][1]
               toLimit = featureConfig[key][2]
               value = d[key]
               if (value>=fromLimit and (value < toLimit or toLimit ==-1)):
                   pass;
               else:
                    valid = False
                    break;
           else:
                valid = False
                break;
        if valid:
            dataSet.append(d)
    print ('valid num:',len(dataSet))
    return dataSet


def showFeature(data,featureConfig,normalize):
    for key in featureConfig.keys():
        dataSet = []
        for d in data:
           if key in d:
               processMethod = featureConfig[key][0]
               fromLimit = featureConfig[key][1]
               toLimit = featureConfig[key][2]
               value = d[key]
               if (value>=fromLimit and (value < toLimit or toLimit ==-1)):
                  dataSet.append(processData(d[key],processMethod))
        maxValue = max(dataSet)
        if normalize:

            processedValueSet = []
            for d in dataSet:
                processedValueSet.append(d/maxValue)
            dataSet = processedValueSet

        print ('valid num:',len(dataSet))

        dataManager.showFigure(data = dataSet,title = key+" from "+str(fromLimit)+" to "+ str(toLimit)+' with '+processMethod,show=True)


def close():
    dataManager.close()


if __name__ == "__main__":
    # process method,from,to

    intervalTime =3*7*24*60*60
    data = dataManager.getDataByIntervalTime(intervalTime)
    featureConfig = {"cpu":["",0,-1],"fileSystem":["log10",0,-1],"memory":["",0,-1],"network":["log10",0,-1],"requestCount":["",10,-1]}
    featureConfig = {"fileSystem":["",0,-1]}
  
    #data = filterDataByConfig(data,featureConfig)

    showFeature(data,featureConfig,normalize=False)

    #,"fileSystem":["log10",0,-1],"memory":["log2",0,-1],"network":["log10",0,-1],"requestCount":["log2",10,-1]}


    #checkData(6, 1654160000, 74.1612, 7854.78)
    close()



