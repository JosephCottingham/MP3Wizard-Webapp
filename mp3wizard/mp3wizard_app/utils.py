
import pyrebase, os, datetime
from django.conf import settings
from .logger import logger

def upload_firebase_storage(paths_audio, a, idtoken, code):
    firebase = pyrebase.initialize_app(settings.FIREBASE_CONFIG)
    storage = firebase.storage()
    database = firebase.database()
    for path in paths_audio:
        storage.child('users').child(a).child(code).child(path.split('/')[-1]).put(path, token=idtoken)

    data = {
        'finish_upload' : datetime.datetime.timestamp(datetime.datetime.now()),
        'uploading' : False
    }

    database.child(a).child(code).update(data, token=idtoken)