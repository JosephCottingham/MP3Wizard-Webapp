
import pyrebase, os, datetime
from django.conf import settings
from .logger import logger
from django.shortcuts import render, redirect
from django.urls import reverse

from pydub import AudioSegment

import stripe

firebase = pyrebase.initialize_app(settings.FIREBASE_CONFIG)
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

database = firebase.database()
authe = firebase.auth()
storage = firebase.storage()

def upload_firebase_storage(paths_audio, a, idtoken, code, base_path):
    firebase = pyrebase.initialize_app(settings.FIREBASE_CONFIG)
    storage = firebase.storage()
    database = firebase.database()
    combined = None

    for path in paths_audio:
        if path.split('.')[-1] == 'mp3':
            audio = AudioSegment.from_file(os.path.abspath(path), format="mp3")        
            if not combined:
                combined = audio
            else:
                combined = combined + audio
            
    audio_path_mp3 = os.path.abspath(os.path.join(base_path, "audio.mp3"))
    file_handle = combined.export(audio_path_mp3, format="mp3")

    output_path_icon = os.path.abspath(os.path.join(base_path, "icon.png"))

    storage.child('users').child(a).child(code).child(audio_path_mp3.split('/')[-1]).put(audio_path_mp3, token=idtoken)
    storage.child('users').child(a).child(code).child(output_path_icon.split('/')[-1]).put(output_path_icon, token=idtoken)

    data = {
        'finish_upload' : datetime.datetime.timestamp(datetime.datetime.now()),
        'uploading' : False
    }

    database.child(a).child(code).update(data, token=idtoken)

def get_subscription(stripe_id):
    subscription = stripe.Subscription.list(limit=1,
    customer=stripe_id,
    status='active',
    price="price_1JFkqpGKcKkOnV80GnyqxiV7")
    if subscription:
        return subscription['data'][0]

def get_user(func):
    def inner(*args, **kwargs):
        idtoken = args[0].session['uid']
        try:
            a = authe.get_account_info(idtoken)
        except Exception:
            return redirect(reverse('signIn'))
        a = authe.get_account_info(idtoken)
        a = a['users']
        a = a[0]
        email = a['email']
        localId = a['localId']
        user = {
            'localId':localId,
            'email':email,
            'idtoken':idtoken
        }
        print(args)
        return func(*args, user, **kwargs)
    return inner
