config = {
    'dbhost':'cloudman.cern.ch',
    'dbname':'cloudman',
    'dbuser':'root',
    'dbpassword':'',
    '':'',

}

def getDBParameters():
    dbHost = config['dbhost']
    dbName = config['dbname']
    dbUser = config['dbuser']
    dbPassword = config['dbpassword']
    dbParameters = [dbHost, dbName, dbUser, dbPassword]
    return dbParameters
