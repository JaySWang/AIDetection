import time
import calendar
import datetime

import math 
import dataCollector as dc,modelBuilder as mb
import dataManager
import taskManager
import model.OrmManager as orm
from model.OrmManager import Feature,FeatureData,Record,Data,Model

def init():
    configs= getMonitorConfigs()
    global task
    task = taskManager.initTask(configs)
        
def monitoring( inc = 60): 
    print("monitor with ",len(task.models)," models")
    print ("start monitoring")
    while True: 
        try:
            data = dc.getCurrentJsonData()
             #data = {'pods':[{'podName':'test','data':[{'cpu':22,'file':838184960,'memory':60,'network':223,'time':'2017-06-21 01:54:15'}]}]}
            print("checking data:")
            print(data)
            for pod in data['pods']:
                for d in pod['data']:
                    data = Data()
                    data.time = dataManager.utc2local(d['time'])
                    data.pod = pod['podName']
                    data.monitoring = True
                    s = orm.getSession()
                    for key,value in d.items():
                        #ignore time
                        if key == 'time':
                            continue

                        featureInDB = s.query(Feature).filter(Feature.name == key).first()
                        if featureInDB == None:
                            featureInDB = Feature()
                            featureInDB.name = key
                            s.add(featureInDB)
                        featureData = FeatureData()
                        featureData.data = data
                        featureData.feature_name= featureInDB.name
                        featureData.value = value
                    
                    for model in task.models:
                        # consider time feature
                        if len(d.keys())!=len(model.features)+1:
                            print('feature size not match')
                            print('data not match model ',model.id," ",model.description)
                            continue

                        match = True
                        for mf in model.features:
                            if mf.feature_name not in d:
                                match =False
                                print('data does not contain model feature ',mf.feature_name)
                                print('data not match model ',model.id," ",model.description)
                                break
                            # value = d[mf.feature_name]
                            # if  value < mf.value_from or (value>=mf.value_to and mf.value_to!=-1):
                            #     match = False
                            #     break

                        if match:
                           print("check with model:",model.id," ",model.description)
                           result = mb.checkDataWithModel(model,d)
                           if(result['result']):
                              print("normal")
                           else :
                              print("warning data:")
                           record = Record()
                           record.pdf = result['pdf']
                           record.data = data
                           record.model_id = model.id
                           record.task_id = task.id
                           record.result = result['result']
                           print("kpi: ",result['kpi'], "current: ",result['pdf'])


                    s.add(data)
                    s.commit()
                    s.close()


        except Exception as e:
            raise e
            print (e)
            print('invalid data,ignore checking')
        time.sleep(inc) 


def validating(startTime,endTime): 
    print("validate with ",len(task.models)," models")
    print ("start validating")
    endTime = datetime.datetime.fromtimestamp(endTime)
    startTime = datetime.datetime.fromtimestamp(startTime)
    try:
       data = dataManager.getDataByTime(startTime,endTime)
# {'cpu': Decimal('6.0000000000'), 'fileSystem': Decimal('556056576.0000000000'), 'memory': Decimal('98.1661376953'),
# 'network': Decimal('443.5544738770'), 'requestCount': Decimal('3.0000000000'), 'id': 57337}            
       for d in data:

                    s = orm.getSession()
                    for key,value in d.items():
                        #ignore id
                        if key == 'id':
                            continue
                    
                    for model in task.models:
                        # consider time feature
                        if len(d.keys())<len(model.features)+1:
                            print('feature size not match')
                            print('data not match model ',model.id," ",model.description)
                            continue

                        match = True
                        for mf in model.features:
                            if mf.feature_name not in d:
                                match =False
                                print('data does not contain model feature ',mf.feature_name)
                                print('data not match model ',model.id," ",model.description)
                                break

                            # check value
                            value = d[mf.feature_name]
                            if  value < mf.value_from or (value>=mf.value_to and mf.value_to!=-1):
                                match = False
                                break

                        if match:
                           # print("check with model:",model.id," ",model.description)
                           result = mb.checkDataWithModel(model,d)
                           # if(result['result']):
                           #    print("normal")
                           # else :
                           #    print("warning data:")
                           record = Record()
                           record.pdf = result['pdf']
                           record.data = s.query(Data).filter(Data.id == d['id']).first()

                           record.model_id = model.id
                           record.task_id = task.id
                           record.result = result['result']
                           nowTime = calendar.timegm(time.gmtime())
                           nowTime = datetime.datetime.fromtimestamp(nowTime)
                           record.time = nowTime
                           # print("kpi: ",result['kpi'], "current: ",result['pdf'])
                           
                           s.add(record)
                    s.commit()
                    s.close()


    except Exception as e:
            print (e)
            print('invalid data,ignore checking')


def getMonitorConfigs():
    intervalTime =2*7*24*60*60

    # 1500998400  2017/7/26 00:00:00
    endTime = 1500998400

    # 1501430400  2017/7/31 00:00:00
    # endTime = 1501430400

    # 1503504000 2017/8/24 00:00:00
    #endTime = 1503504000

    startTime =endTime - intervalTime

    endTime = datetime.datetime.fromtimestamp(endTime)
    startTime = datetime.datetime.fromtimestamp(startTime)


    configs= []
    config1 = {}
    config1["endTime"] = endTime
    config1["startTime"] = startTime

    # featureConfig1 = {"cpu":["log2",0,-1],"fileSystem":["log10",0,-1],"memoryWS":["log10",0,-1],"network":["log10",0,-1],"requestCount":["log2",10,-1]}
    featureConfig1 = {"cpu":["log2",0,-1],"fileSystem":["log10",0,-1],"network":["log10",0,-1],"requestCount":["log2",10,-1]}

    config1["featureConfig"] = featureConfig1
    config1["kpi"] = 0.001
    config1["description"] = 'request work '
    configs.append(config1)

    config2 = {}
    # config2["intervalTime"] = intervalTime
    config2["endTime"] = endTime
    config2["startTime"] = startTime
    # featureConfig2 = {"cpu":["log2",0,-1],"fileSystem":["log10",0,-1],"memoryWS":["log10",0,-1],"network":["log10",0,-1],"requestCount":["log2",0,10]}
    featureConfig2 = {"cpu":["log2",0,-1],"fileSystem":["log10",0,-1],"network":["log10",0,-1],"requestCount":["log2",0,10]}
    config2["featureConfig"] = featureConfig2
    config2["kpi"] = 0.001
    config2["description"] = 'request idle '
    configs.append(config2)

    # config3 = {}
    # config3["endTime"] = endTime
    # config3["startTime"] = startTime
    # # config3["intervalTime"] = intervalTime
    # featureConfig3 = {"cpu":["log2",0,-1],"fileSystem":["log10",0,-1],"memoryWS":["log10",0,-1],"requestCount":["log2",0,-1]}
    # config3["featureConfig"] = featureConfig3
    # config3["description"] = 'without network'
    # config3["kpi"] = 0.001
    # configs.append(config3)

    return configs

if __name__ == "__main__":
    # s = orm.getSession()
    # modelInDB = s.query(Model).filter(Model.id == 372).first()
    # print("kpi-------after reload",modelInDB.kpi_pdf)
    init()
    # monitoring()
    intervalTime =12*60*60

    # intervalTime =24*60*60

    # 1500998400  2017/7/27 00:00:00
    endTime = 1501084800

    # 2017/7/31 16:00:00
    # endTime = 1501488000

    #2017/8/25 00:00:00
    # endTime = 1503590400
    
    startTime =endTime - intervalTime
    validating(startTime,endTime)

