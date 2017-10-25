import model.OrmManager as orm
from model.OrmManager import Task,Model,ModelFeature,Feature,FeatureData,Record,Data
import time
import calendar
import datetime
import modelBuilder as mb
import dataManager

def initTask(configs):
    task = Task()
    startTime = calendar.timegm(time.gmtime())
    startTime = datetime.datetime.fromtimestamp(startTime)
    task.start_time = startTime
    global s
    s = orm.getSession()

    dists = []

    for config in configs:
        model = None

        if "intervalTime" in config:
            print("init by interval")
            model = mb.initModelByInterval(s,config["intervalTime"],config["featureConfig"],config["description"],config["kpi"])
        else:
            print("init by start and end time")
            model = mb.initModel(s,config["startTime"],config["endTime"],config["featureConfig"],config["description"],config["kpi"])

        dists.append(model.dist)

        task.models.append(model)


    s.add(task)
    s.commit()
    
    for i in range(len(task.models)):
        mb.distMap[task.models[i].id] = dists[i]

    return task

def endTask(task):
    print(mb.distMap[task.models[0].id].pdf([0.7422929,0.99538261,0.99596864,0.84127188]))

    endTime = calendar.timegm(time.gmtime())
    endTime = datetime.datetime.fromtimestamp(endTime)
    task.end_time = endTime
    s.add(task)
    s.commit()

if __name__ == "__main__":
    configs=[]
    config1 = {}
    config1["intervalTime"] = 5*24*60*60
    featureConfig1 = {"cpu":["log2",0,20],"fileSystem":["log10",0,-1],"memory":["log2",0,-1],"network":["log10",0,-1]}
    config1["featureConfig"] = featureConfig1
    config1["kpi"] = 0.001
    config1["description"] = 'idle'


    config2 = {}
    config2["intervalTime"] = 5*24*60*60
    featureConfig2 = {"cpu":["log2",20,-1],"fileSystem":["log10",0,-1],"memory":["log2",0,-1]}
    config2["featureConfig"] = featureConfig2
    config2["kpi"] = 0.001
    config2["description"] = 'working'


    configs.append(config1)
    configs.append(config2)


    t = initTask(configs);
    endTask(t)
    s.close()



