from django.shortcuts import render, redirect
from django.contrib import auth
import pyrebase, os, uuid, threading, datetime, json
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from . import utils
from .logger import logger
from django.http import HttpResponse
import stripe


firebase = pyrebase.initialize_app(settings.FIREBASE_CONFIG)
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

database = firebase.database()
authe = firebase.auth()
storage = firebase.storage()


def home(request):
    current_user = None
    try:
        idtoken = request.session['uid']
        a = authe.get_account_info(idtoken)
        a = a['users'] 
        a = a[0]
        current_user = a['email']
        a = a['localId']
    except:
        pass
    return render(request, 'home.html', {'current_user':current_user, 'page':'MP3Wizard Home'})

def signIn(request):
    current_user = None
    try:
        idtoken = request.session['uid']
        a = authe.get_account_info(idtoken)
        a = a['users'] 
        a = a[0]
        current_user = a['email']
        a = a['localId']
    except:
        pass
    return render(request, 'signin.html', {'current_user':current_user, 'page':'signin'})

def postSignIn(request):
    if request.method == 'GET':
        return redirect(reverse('signIn'))

    email = request.POST.get('email')
    passw = request.POST.get('pass')
    print(email)
    print(passw)
    try:
        user = authe.sign_in_with_email_and_password(email, passw)
    except Exception as e:
        message = json.loads(e.args[1])['error']['message'].replace('_', ' ')
        return render(request, 'signin.html', {"messg":message})

    print(user['idToken'])
    session_id = user['idToken']
    request.session['uid'] = str(session_id)

    idtoken = request.session['uid']
    print("id" +" " + ' : ' + str(idtoken))
    a = authe.get_account_info(idtoken)
    print(a)
    a = a['users'] 
    a = a[0]
    current_user = a['email']
    a = a['localId']

    # name = database.child('users').child(a).get().val()
    # print(name)
    return redirect(reverse('panel'))


def logout(request):
    auth.logout(request)
    return render(request, 'signin.html')

def signUp(request):
    current_user = None
    try:
        idtoken = request.session['uid']

        a = authe.get_account_info(idtoken)
        a = a['users'] 
        a = a[0]
        current_user = a['email']
        a = a['localId']
    except:
        pass
    return render(request, 'signup.html', {'current_user':current_user, 'page':'signup'})

def postSignUp(request):
    if request.method == 'GET':
        return redirect(reverse('signUp'))

    email = request.POST.get('email')
    passw = request.POST.get('pass')
    name = request.POST.get('name')
    try:
        user = authe.create_user_with_email_and_password(email, passw)
    except Exception as e:
        message = json.loads(e.args[1])['error']['message'].replace('_', ' ')
        print(message)
        return render(request, 'signup.html', {"messg":message})

    session_id = user['idToken']
    request.session['uid'] = str(session_id)
    idtoken = request.session['uid']

    strip_user = stripe.Customer.create(
        email=email,
        name=name
    )

    stripe_user_id = strip_user['id']

    data = {'name': name, "stripe_id":stripe_user_id}

    a = authe.get_account_info(idtoken)
    a = a['users'] 
    a = a[0]
    current_user = a['email']
    print(current_user)
    a = a['localId']

    database.child(a).child('user_info').set(data, token=idtoken)

    # mssg = "you may now sign in"
    return redirect(reverse('panel'))

@utils.get_user
def create(request, user):

    user_info = database.child(user['localId']).child('user_info').get(token=user['idtoken']).val()
    print(user_info)
    books_children = database.child(user['localId']).get(token=user['idtoken']).val()
    # del books_children['user_info']
    
    subscription = None

    if (len(books_children) > 0):
        subscription = utils.get_subscription(user_info['stripe_id'])

    if not subscription or subscription['status'] != 'active':
        success_url = reverse('create')
        stripe_session = stripe.checkout.Session.create(
            success_url='https://google.com',
            cancel_url="https://example.com/cancel",
            payment_method_types=["card"],
            line_items=[
                {
                    "price": "price_1JFkqpGKcKkOnV80GnyqxiV7",
                    "quantity":1
                },
            ],
            mode="subscription",
            customer=user_info['stripe_id']
        )
        return redirect(stripe_session['url'])


    return render(request, 'create.html', {'current_user':user['email'], 'page':'create'})

@utils.get_user
def post_create(request, user):

    title = request.POST.get('title')

    fs = FileSystemStorage()

    base_path = os.path.join('media', user['localId'])
    base_path = os.path.join(base_path, title.replace(' ', ''))
    paths_audio = []
    for index, file_upload_name in enumerate(request.FILES):
        ext = '.mp3'
        if file_upload_name =='icon':
            ext = '.png'
        path = os.path.join(base_path, str(file_upload_name+ext))

        fs.save(path, request.FILES[file_upload_name])
        if file_upload_name !='icon':
            paths_audio.append(path)

    code = uuid.uuid4().hex


    data = {
        'title': title,
        'currentFile': '0',
        'downloaded' : 'Cloud',
        'fileNum': '0',
        'locSec': '0',
        'code': code,
        'uploading' : True,
        'start_upload' : datetime.datetime.timestamp(datetime.datetime.now())
    }


    database.child(user['localId']).child(code).set(data, token=user['idtoken'])

    # utils.upload_firebase_storage(paths_audio, user['localId'], user['idtoken'], code, base_path)
    upload_firebase_thread = threading.Thread(target=utils.upload_firebase_storage, args=[paths_audio, user['localId'], user['idtoken'], code, base_path], daemon=True)
    upload_firebase_thread.start()

    return redirect(reverse('panel'))

@utils.get_user
def panel(request, user):

    import time
    import datetime
    from datetime import timezone

    books_children=[]
    print(user['localId'])
    print(user['idtoken'])
    try:
        books_children = database.child(user['localId']).get(token=user['idtoken']).val()
    except Exception as e:
        print(e) 
    print(books_children)
    del books_children['user_info']
    books_details = {}
    for book_title in books_children:
        books_details[book_title] = dict()
        books_details[book_title]['url'] = storage.child('users').child(user['localId']).child(book_title).child('icon.png').get_url(token=user['idtoken'])
        book_details = database.child(user['localId']).child(book_title).get(token=user['idtoken']).val()

        for key in book_details.keys():
            books_details[book_title][key] = book_details[key]

        totalSec = int(float(books_details[book_title]['locSec']))
        sec = int(totalSec % 60)
        totalSec -= sec
        if sec < 10:
            sec = f'0{sec}'
        minute = int((totalSec / 60) % 60)
        totalSec -= minute*60
        if minute < 10:
            minute = f'0{minute}'
        hour = int((totalSec / 60 / 60))
        if hour < 10:
            hour = f'0{hour}'
        books_details[book_title]['loc'] = f'{hour}:{minute}:{sec}'
    print('')
    print('')
    print(books_details)
    return render(request, 'panel.html', {'current_user':user['email'], 'page':'panel', 'books_details':books_details})

@utils.get_user
def player(request, user, book_code):

    book = database.child(user['localId']).child(book_code).get(token=user['idtoken']).val()

    book['url'] = storage.child('users').child(user['localId']).child(book_code).child('icon.png').get_url(token=user['idtoken'])
    book['audio_url'] = storage.child('users').child(user['localId']).child(book_code).child(f'audio.mp3').get_url(token=user['idtoken'])
    book['currentFile'] = int(book['currentFile'])
    return render(request, 'player.html', { 'current_user':user['email'],'page':'player','book':book })

@utils.get_user
def postDeleteBook(request, user):
    bookCode = request.POST.get('bookCode')

    # storage.child('users').child(a).child(bookCode).remove(token=idtoken)
    database.child(user['localId']).child(bookCode).remove(token=user['idtoken'])

    return redirect(reverse('panel'))

@utils.get_user
def postTimeUpdate(request, user):

    book_code = request.POST.get('bookCode')
    locSec = request.POST.get('locSec')

    books_children = database.child(user['localId']).get(token=user['idtoken']).val()
    if book_code in books_children:
        database.child(user['localId']).child(book_code).update({'locSec':locSec}, token=user['idtoken'])
    

    return HttpResponse("OK")

@utils.get_user
def customerStripePortal(request, user):

    user_info = database.child(user['localId']).child('user_info').get(token=user['idtoken']).val()

    session = stripe.billing_portal.Session.create(
        customer=user_info['stripe_id'],
        return_url='https://google.com',
    )
    
    return redirect(session.url, code=303)


