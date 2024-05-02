# from configparser import ConfigParser


# def config(filename="database.ini", section="postgresql"):
#     # create a parser
#     parser = ConfigParser()
#     # read config file
#     parser.read(filename)
#     db = {}
#     if parser.has_section(section):
#         params = parser.items(section)
#         for param in params:
#             db[param[0]] = param[1]
#     else:
#         raise Exception(
#             'Section {0} is not found in the {1} file.'.format(section, filename))
#     return db

def config():
    db = {
        "host": "databasepg.c92a6coycpya.us-east-1.rds.amazonaws.com",
        "database": "postgres",
        "user": "postgres",
        "password": "postgres",
        "port": 5432
    }
    return db
