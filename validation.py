from main import datetime
from main import datastore

client = datastore.Client()


def request_validation_name(name):
    if type(name) is not str or not name.replace(" ", "").isalpha() \
            or not 0 < len(name) <= 100:
        return False
    collections_query = client.query(kind="collections")
    collections = list(collections_query.fetch())
    for collection in collections:
        if str(name) == collection["name"]:
            return "Forbidden"
    return True

def request_validation_capacity(capacity):
    if type(capacity) is not int or not 0 < len(str(capacity)) <= 18:
        return False
    return True

def request_validation_type(typeContent):
    if type(typeContent) is not str or not typeContent.replace(" ", "").isalpha() \
            or not 0 < len(typeContent) <= 50:
        return False
    return True

def request_validation_date(date):
    try:
        datetime.datetime.strptime(date, '%m-%d-%Y')
        return True
    except ValueError:
        return False
