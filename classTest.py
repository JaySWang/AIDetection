class Feature:
	name = ""

	def __init__(self,name):
		self.name=name

	def getName(self):
		return self.name


if  __name__  == "__main__":
	f1 = Feature("CPU")
	f2 = Feature("File_System")
	print (f1.getName())
	print (Feature.name)