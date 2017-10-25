import OrmManager as orm
from OrmManager import Task,Model,ModelFeature,Feature,FeatureData,Record,Data
import calendar
import time
import datetime




intervalTime = 600

endTime = calendar.timegm(time.gmtime())
startTime =endTime - intervalTime

endTime = datetime.datetime.fromtimestamp(endTime)
startTime = datetime.datetime.fromtimestamp(startTime)


task = Task()
task.start_time = startTime
task.end_time = endTime


model1 = Model()
model1.kpi_index =0.001

model2 = Model()
model2.kpi_index =0.002

task.models.append(model1)
task.models.append(model2)


s = orm.getSession()

feature = s.query(Feature).filter(Feature.name == 'cpu').first()
if feature == None:
   feature = Feature()
   feature.name = "cpu"

modelFeature = ModelFeature()
modelFeature.model = model1
modelFeature.featue = feature
modelFeature.value_from =0
modelFeature.process_method = 'log2'
modelFeature.feature = feature

data = Data()
data.time = endTime
data.pod = "lala"

featureData = FeatureData()
featureData.feature = feature
featureData.data = data
featureData.value = 10

featureData2 = FeatureData()
featureData2.feature = feature
featureData2.data = data
featureData2.value = 11

record = Record()
record.pdf = 11.1
record.data = data
record.model = model1
record.task


s.add(task)
s.add(data)



s.commit()
s.close()

feature = s.query(Feature).filter(Feature.name == 'cpu').first()
print (feature)


