from sqlalchemy import Column,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.dialects.mysql import \
        BIGINT, BINARY, BIT, BLOB, BOOLEAN, CHAR, DATE, \
        DATETIME, DECIMAL, DECIMAL, DOUBLE, ENUM, FLOAT, INTEGER, \
        LONGBLOB, LONGTEXT, MEDIUMBLOB, MEDIUMINT, MEDIUMTEXT, NCHAR, \
        NUMERIC, NVARCHAR, REAL, SET, SMALLINT, TEXT, TIME, TIMESTAMP, \
        TINYBLOB, TINYINT, TINYTEXT, VARBINARY, VARCHAR, YEAR


Base = declarative_base()

class Feature(Base):
      __tablename__ = 'feature'
      name = Column(NVARCHAR(length=50), primary_key=True)

class TaskModel(Base):
     __tablename__ = 'task_model'
     id = Column(INTEGER, primary_key=True)
     task_id = Column(INTEGER, ForeignKey("task.id"))
     model_id = Column(INTEGER, ForeignKey("model.id"))


class Model(Base):
      __tablename__ = 'model'
      id = Column(INTEGER, primary_key=True)
      data_time_from = Column(TIMESTAMP)
      data_time_to = Column(TIMESTAMP)
      kpi_index = Column(DOUBLE)
      max_pdf = Column(DOUBLE)
      min_pdf = Column(DOUBLE)
      mean_pdf = Column(DOUBLE)
      kpi_pdf = Column(DOUBLE(asdecimal=False))
      description = Column(NVARCHAR(200))

      features = relationship("ModelFeature")

class Task(Base):
      __tablename__ = 'task'
      id = Column(INTEGER, primary_key=True)
      models = relationship("Model",secondary="task_model")
      start_time = Column(TIMESTAMP)
      end_time = Column(TIMESTAMP)

class ModelFeature(Base):
      __tablename__ = 'model_feature'
      id = Column(INTEGER, primary_key=True)
      value_from = Column(DOUBLE)
      value_to = Column(DOUBLE)
      max_value = Column(DOUBLE)
      min_value = Column(DOUBLE)
      process_method = Column(NVARCHAR(length=200))
      model_id = Column(INTEGER, ForeignKey(Model.id))
      model = relationship(Model,backref="model")  

      feature_name = Column(NVARCHAR(50), ForeignKey(Feature.name))
      feature = relationship(Feature)  

class Data(Base):
      __tablename__ = 'data'
      id = Column(INTEGER, primary_key=True)
      time = Column(TIMESTAMP)
      monitoring = Column(BOOLEAN)
      pod = Column(NVARCHAR(length=100))
      featureData = relationship("FeatureData")

class Record(Base):
      __tablename__ = 'record'
      id = Column(INTEGER, primary_key=True)
      pdf = Column(DOUBLE)
      result = Column(BOOLEAN)

      data_id = Column(INTEGER, ForeignKey(Data.id))
      data = relationship(Data,backref="rawData")  

      model_id = Column(INTEGER, ForeignKey(Model.id))
      # model = relationship(Model) 

      task_id = Column(INTEGER, ForeignKey(Task.id))
      # task = relationship(Task) 
      time = Column(TIMESTAMP)


class FeatureData(Base):
      __tablename__ = 'feature_data'
      id = Column(INTEGER, primary_key=True)
      value = Column(DOUBLE)

      feature_name = Column(NVARCHAR(50), ForeignKey(Feature.name))
      # feature = relationship(Feature)  

      data_id = Column(INTEGER, ForeignKey(Data.id))
      data = relationship(Data,backref="dataItem")  


def init():
    global engine

    #engine = create_engine('mysql://root:@127.0.0.1:3306/monitor_system',echo=True)
    engine = create_engine('mysql://root:@127.0.0.1:3306/monitor_system')


def createDB():
    Base.metadata.create_all(engine)

def dropDB():
    Base.metadata.drop_all(engine)

def getSession():
    if not 'engine' in globals():
      print ("--------init session--------")
      init()
    session = sessionmaker()
    session.configure(bind=engine)
    s = session()
    return s 

def close():
	getSession().close()

if __name__ == "__main__":
   init()
   #dropDB()
   createDB()
   close()
