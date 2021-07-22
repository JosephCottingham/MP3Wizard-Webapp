
import pyrebase, os, datetime
from django.conf import settings
from .logger import logger
from django.shortcuts import render, redirect
from django.urls import reverse

import stripe

firebase = pyrebase.initialize_app(settings.FIREBASE_CONFIG)
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

database = firebase.database()
authe = firebase.auth()
storage = firebase.storage()

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

def get_subscription(stripe_id):
    subscription = stripe.Subscription.list(limit=1,
    customer=stripe_id,
    status='active',
    price="price_1JFkqpGKcKkOnV80GnyqxiV7")
    return subscription['data'][0]

def get_user(func):
    def inner(*args, **kwargs):
        print(args[0])
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
        return func(*args, user)
    return inner
