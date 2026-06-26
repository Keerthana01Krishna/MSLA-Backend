from sqlalchemy import create_engine

# Replace YOUR_PASSWORD with your MySQL password
DATABASE_URL = "mysql+pymysql://root:Keerthi%406362@localhost:3306/msla"

engine = create_engine(DATABASE_URL)

try:
    connection = engine.connect()
    print("Database Connected Successfully!")
    connection.close()
except Exception as e:
    print("Database Connection Failed!")
    print(e)