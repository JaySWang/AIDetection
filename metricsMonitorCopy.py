import time
import math 
import dataCollector as dc,modelBuilder as mb
import dataManager

def init(intervalTime,kpi = 0.0001):
    mb.initModel(intervalTime,kpi)

def checkData(data):
    dist = model['dist']
    KPI = model['KPI']
    print((data['cpu'], data['fileSystem'],data['memory'],data['network']))
    currentPdf = dist.pdf((data['cpu'], data['fileSystem'],data['memory'],data['network']))
    print ("checking")
    print ("current pdf:")
    print (currentPdf)
    
    if KPI>currentPdf:

        print ('KPI')
        print (KPI)
        print ('warning')
    else: 
        print ('normal')
        
def monitoring( inc = 60): 
    print ("start monitoring")
    while True: 
        try:
            data = dc.getCurrentJsonData()
            print("checking data:")
            print(data)
            for pod in data['pods']:
                for d in pod['data']:
                    result = mb.checkData(d['cpu'],d['fileSystem'],d['memory'],d['network'])
                    if(result['result']):
                        print("normal")
                    else :
                        print("warning data:")
                    dataManager.saveMonitorData(pod['podName'],d,result)
        except Exception as e:
            print (e)
            print('invalid data,ignore checking')
        time.sleep(inc) 


if __name__ == "__main__":
    intervalTime = 3*7*24*60*60 # in sec
    kpi = 0.001 #  less than 99.9%  pdf value
    init(intervalTime,kpi)
    monitoring()