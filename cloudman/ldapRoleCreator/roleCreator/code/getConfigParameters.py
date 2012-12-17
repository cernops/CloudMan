#Test code to return database parameters while the code of reading configuration file is not available......

dbHost = "localhost"
dbUser = "root"
dbPassword = ""
dbName = "cloudman"
maxInsertsInOneCommit = 100

def getDBConnectionParameters():
    return dbHost, dbUser, dbPassword, dbName

def getMaxInsertsInOneCommit():
    return maxInsertsInOneCommit


