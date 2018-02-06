# coding: utf-8


"""
__init__(n_clusters=8,random_state=None)
fit(X, y=None)  X : array-like or sparse matrix, shape=(n_samples, n_features) Training instances to cluster
kmeans = KMeans(n_clusters=ksize, random_state=0).fit(td)

cluster_centers_(array,Coordinates of cluster centers)
labels_(array,Labels of each point)
inertia_ (Sum of squared distances of samples to their closest cluster center.)

predict()Predict the closest cluster each sample in X belongs to. X : {array-like, sparse matrix}, shape = [n_samples, n_features]
Returns:labels : array, shape [n_samples,] 

"""
import numpy as np
from numpy import *


class KMeans:

	def __init__(self,n_clusters=8,random_state=None):
		self.__k  = n_clusters
		self.cluster_centers_=[]
		self.labels_=[]
		self.inertia_=0.0

	def predict(self,data):
		result = []

		for d in data:
			min = float('inf')
			belongs = 0
			for x in range(len(self.cluster_centers_)):
				dis = self.__distEclud(d,self.cluster_centers_[x])
				if dis <= min:
					min = dis
					belongs=x

			result.append(belongs)
		return result

	def fit(self,x, y=None):
		# centroids,clusterAssment=self.__kMeans(x,self.__k)
		centroids,clusterAssment=self.__newBiKmeans(x,self.__k)
		self.cluster_centers_ = np.array(centroids)

		self.clusterAssment = clusterAssment

		m, n = np.shape(np.array(clusterAssment))
		for i in range(m):
			self.labels_.append(int(np.array(clusterAssment)[i][0]))
			self.inertia_+=np.array(clusterAssment)[i][1]
		return self

	def __distEclud(self,vecA, vecB):
	    """
	    计算两向量的欧氏距离
	    Args:
	        vecA: 向量A
	        vecB: 向量B
	    Returns:
	        欧式距离
	    """
	    return np.sqrt(np.sum(np.power(np.array([float(itemA) for itemA in vecA]) - np.array([float(itemB) for itemB in vecB]), 2)))
	    # return np.sqrt(np.sum(np.power(vecA - vecB[0], 2)))

	def __randCent(self,dataSet, k):
	    """
	    随机生成k个聚类中心
	    Args:
	        dataSet: 数据集
	        k: 簇数目
	    Returns:
	        centroids: 聚类中心矩阵
	    """
	    _, n = dataSet.shape
	    centroids = np.mat(np.zeros((k, n)))
	    for j in range(n):
	        # 随机聚类中心落在数据集的边界之内
	        minJ = np.min(dataSet[:, j])
	        maxJ = np.max(dataSet[:, j])
	        rangeJ = float(maxJ - minJ)
	        centroids[:, j] = float(minJ) + rangeJ * np.random.rand(k, 1)
	    return centroids

	def __kMeans(self,dataSet, k, maxIter = 300):
	    """
	    K-Means
	    Args:
	        dataSet: 数据集
	        k: 聚类数
	    Returns:
	        centroids: 聚类中心
	        clusterAssment: 点分配结果
	    """
	    # 随机初始化聚类中心
	    centroids = self.__randCent(dataSet, k)
	    m, n = np.shape(dataSet)
	    # 点分配结果： 第一列指明样本所在的簇，第二列指明该样本到聚类中心的距离
	    clusterAssment = np.mat(np.zeros((m, 2)))
	    # 标识聚类中心是否仍在改变
	    clusterChanged = True
	    # 直至聚类中心不再变化
	    iterCount = 0
	    while clusterChanged and iterCount < maxIter:
	        iterCount += 1
	        clusterChanged = False
	        # 分配样本到簇
	        for i in range(m):
	            # 计算第i个样本到各个聚类中心的距离
	            minIndex = 0
	            minDist = np.inf
	            for j in range(k):
	                dist = self.__distEclud(dataSet[i, :],  np.array(centroids[j, :])[0])
	                if(dist < minDist):
	                    minIndex = j
	                    minDist = dist
	            # 判断cluster是否改变
	            if(clusterAssment[i, 0] != minIndex):
	                clusterChanged = True
	            clusterAssment[i, :] = minIndex, minDist**2
	        # 刷新聚类中心: 移动聚类中心到所在簇的均值位置
	        for cent in range(k):
	            # 通过数组过滤获得簇中的点
	            ptsInCluster = dataSet[np.nonzero(
	                clusterAssment[:, 0].A == cent)[0]]
	            if ptsInCluster.shape[0] > 0:
	                # 计算均值并移动
	                centroids[cent, :] = np.mean(ptsInCluster, axis=0)
	    # print("|||")             

	    return centroids, clusterAssment	

	# 构建二分k-均值聚类
	def __newBiKmeans(self,dataSet, k):
	    m = shape(dataSet)[0]
	    clusterAssment = mat(zeros((m,2))) # 初始化，簇点都为0
	    centroid0 = mean(dataSet, axis=0).tolist()[0] # 起始第一个聚类点，即所有点的质心

	    centList =[centroid0] # 质心存在一个列表中

	    for j in range(m):#calc initial Error
	        clusterAssment[j,1] = self.__distEclud(mat(centroid0), dataSet[j,:])**2
	        # 计算各点与簇的距离，均方误差，大家都为簇0的群

	    while (len(centList) < k):

	        lowestSSE = inf
	        for i in range(len(centList)):

	            ptsInCurrCluster = dataSet[nonzero(clusterAssment[:,0].A==i)[0],:]#get the data points currently in cluster i
	            # 找出归为一类簇的点的集合，之后再进行二分，在其中的簇的群下再划分簇
	            #第一次循环时，i=0，相当于，一整个数据集都是属于0簇，取了全部的dataSet数据
	            if(len(ptsInCurrCluster)==0):
	            	continue
	            centroidMat, splitClustAss = self.__kMeans(ptsInCurrCluster, 2)
	            #开始正常的一次二分簇点
	            #splitClustAss，类似于[0   2.3243]之类的，第一列是簇类，第二列是簇内点到簇点的误差

	            sseSplit = sum(splitClustAss[:,1]) # 再分后的误差和
	            sseNotSplit = sum(clusterAssment[nonzero(clusterAssment[:,0].A!=i)[0],1]) # 没分之前的误差
	            # print ("sseSplit: ",sseSplit)
	            # print ("sseNotSplit: ",sseNotSplit)
	            #至于第一次运行为什么出现seeNoSplit=0的情况，因为nonzero(clusterAssment[:,0].A!=i)[0]不存在，第一次的时候都属于编号为0的簇

	            if (sseSplit + sseNotSplit) < lowestSSE:
	                bestCentToSplit = i
	                bestNewCents = centroidMat
	                bestClustAss = splitClustAss.copy()
	                lowestSSE = sseSplit + sseNotSplit
	                # copy用法http://www.cnblogs.com/BeginMan/p/3197649.html

	        bestClustAss[nonzero(bestClustAss[:,0].A == 1)[0],0] = len(centList) #change 1 to 3,4, or whatever
	        bestClustAss[nonzero(bestClustAss[:,0].A == 0)[0],0] = bestCentToSplit
	        #至于nonzero(bestClustAss[:,0].A == 1)[0]其中的==1这簇点，由kMeans产生

	        # print ('the bestCentToSplit is: ',bestCentToSplit)
	        # print ('the len of bestClustAss is: ', len(bestClustAss))

	        centList[bestCentToSplit] = bestNewCents[0,:].tolist()[0]#replace a centroid with two best centroids


	        centList.append(bestNewCents[1,:].tolist()[0])

	        clusterAssment[nonzero(clusterAssment[:,0].A == bestCentToSplit)[0],:]= bestClustAss#reassign new clusters, and SSE

	    return mat(centList), clusterAssment




if __name__ == "__main__":
	km = KMeans(4).fit(np.array([[1,2],[3,1],[3,4],[1,4],[2,4]]))
	
	print(km.cluster_centers_)
	print(km.labels_)
	print(km.inertia_)
	print(km.predict(np.array([[1,5],[2,0],[12,0],[0,0]])))

	