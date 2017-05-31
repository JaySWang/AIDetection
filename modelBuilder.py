
# coding: utf-8

# In[8]:

from scipy.stats import multivariate_normal
import numpy as np
import tensorflow as tf


# feature = ["cpu","file","memory","network"]

numOfData = 10075;

def initData():
  
    filename_queue = tf.train.string_input_producer(["anomaly - Normalization.csv"])
    reader = tf.TextLineReader()
    key, value = reader.read(filename_queue)
    record_defaults = [[1.],[1.],[1.],[1.],["s"]]
    cpu,file,memory,network,time = tf.decode_csv(
        value, record_defaults=record_defaults)
    features = tf.stack([cpu,file,memory,network])
    dataSet = [[0 for col in range(1)] for row in range(5)]
    with tf.Session() as sess:
      # Start populating the filename queue.
      coord = tf.train.Coordinator()
      threads = tf.train.start_queue_runners(coord=coord)
      for i in range(numOfData):
        # Retrieve a single instance:
        data1,data2,data3,data4= sess.run(features)
        dataSet[0].insert(i,data1)
        dataSet[1].insert(i,data2)
        dataSet[2].insert(i,data3)
        dataSet[3].insert(i,data4)

    coord.request_stop()
    coord.join(threads)
    
    print("initData done")
    return dataSet


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
    
    dist = multivariate_normal(mean=mu, cov=chol)
    #dist =  tf.contrib.distributions.MultivariateNormalFull(mu, chol)
    print("initDist")
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

def getMinPdf(pdfProductSet):
    init = tf.global_variables_initializer()
    sess = tf.InteractiveSession()
    sess.run(init)

    pdfProductData = np.array(pdfProductSet)
    pdfProductMin = tf.cast(np.min(pdfProductData,0),tf.float32)
    pmin = sess.run([pdfProductMin])
    return pmin

def initModel():
    dataSet = initData()
    dist = initDist(dataSet)
    pdfProductSet = getPdfProductSet(dist,dataSet)
    minPdf = getMinPdf(pdfProductSet)
    model = {'dist':dist,'KPI':minPdf}

    return model






# In[10]:

model = initModel()
dist = model['dist']
minP = model['KPI']


# In[ ]:



