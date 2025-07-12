from dotenv import load_dotenv
import os

load_dotenv()  

MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_URI = os.getenv("MONGO_URI")

print("MONGO_DB_NAME =", MONGO_DB_NAME)
print("MONGO_URI =", MONGO_URI)

from pymongo import MongoClient

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
