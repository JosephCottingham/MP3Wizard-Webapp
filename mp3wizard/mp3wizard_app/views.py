from django.shortcuts import render, redirect
from django.contrib import auth
import pyrebase, os, uuid, threading, datetime
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from . import utils
from .logger import logger
from django.http import HttpResponse

firebase = pyrebase.initialize_app(settings.FIREBASE_CONFIG)

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
    return render(request, 'signIn.html', {'current_user':current_user, 'page':'signin'})

def postSignIn(request):
    email = request.POST.get('email')
    passw = request.POST.get('pass')
    print(email)
    print(passw)
    try:
        user = authe.sign_in_with_email_and_password(email, passw)
    except:
        message = 'invalid credentials'
        return render(request, 'signIn.html', {"messg":message})
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
    return render(request, 'signIn.html')

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
    return render(request, 'signUp.html', {'current_user':current_user, 'page':'signup'})

def postSignUp(request):
    email = request.POST.get('email')
    passw = request.POST.get('pass')
    try:
        user = authe.create_user_with_email_and_password(email, passw)
    except:
        message = 'unable to create account try again'
        return render(request, 'signUp.html', {"messg":message})

    uid = user['localId']
    # name = database.child('users').document(uid)

    # data = {'name': name, "status":"1"}
    # mssg = "you may now sign in"
    return render(request, 'signIn.html')

def create(request):
    idtoken = request.session['uid']
    try:
        a = authe.get_account_info(idtoken)
    except Exception:
        return redirect(reverse('signIn'))
    a = authe.get_account_info(idtoken)
    a = a['users'] 
    a = a[0]
    current_user = a['email']
    a = a['localId']
    return render(request, 'create.html', {'current_user':current_user, 'page':'create'})


def post_create(request):

    title = request.POST.get('title')
    idtoken = request.session['uid']
    try:
        a = authe.get_account_info(idtoken)
    except Exception:
        return redirect(reverse('signIn'))

    a = authe.get_account_info(idtoken)
    a = a['users']
    a = a[0]
    a = a['localId']

    fs = FileSystemStorage()

    paths_audio = []
    for index, file_upload_name in enumerate(request.FILES):
        ext = '.mp3'
        if file_upload_name =='icon':
            ext = '.png'
        path = os.path.join(title.replace(' ', ''), str(file_upload_name+ext))
        path = os.path.join(a, path)
        path = os.path.join('media', path)
        fs.save(path, request.FILES[file_upload_name])
        paths_audio.append(path)

    code = uuid.uuid4().hex

    logger.info('test')
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


    database.child(a).child(code).set(data, token=idtoken)

    upload_firebase_thread = threading.Thread(target=utils.upload_firebase_storage, args=[paths_audio, a, idtoken, code], daemon=True)
    upload_firebase_thread.start()

    return redirect(reverse('panel'))

def panel(request):

    import time
    import datetime
    from datetime import timezone

    idtoken = request.session['uid']
    try:
        a = authe.get_account_info(idtoken)
    except Exception:
        return redirect(reverse('signIn'))
    a = authe.get_account_info(idtoken)
    a = a['users']
    a = a[0]
    current_user = a['email']
    a = a['localId']
    books_children=[]
    try:
        books_children = database.child(a).get(token=idtoken).val()
        if books_children == None:
            books_children = []
    except:
        pass 
    books_details = {}
    for book_title in books_children:
        books_details[book_title] = dict()
        books_details[book_title]['url'] = storage.child('users').child(a).child(book_title).child('icon.png').get_url(token=idtoken)
        book_details = database.child(a).child(book_title).get(token=idtoken).val()
        for key in book_details.keys():
            books_details[book_title][key] = book_details[key]
    return render(request, 'panel.html', {'current_user':current_user, 'page':'panel', 'books_details':books_details})

def player(request, book_code):

    idtoken = request.session['uid']
    try:
        a = authe.get_account_info(idtoken)
    except Exception:
        return redirect(reverse('signIn'))

    a = a['users']
    a = a[0]
    current_user = a['email']
    a = a['localId']

    book = database.child(a).child(book_code).get(token=idtoken).val()
    print(book)
    # files_list = storage.child('users').child(a).child(book.get('title')).list_files()
    # for file in files_list:
    #     print(str(file.metadata))
    book['url'] = storage.child('users').child(a).child(book_code).child('icon.png').get_url(token=idtoken)
    book['audio_urls'] = list()
    for audio_file in range(int(book['fileNum'])+1):
        print(audio_file)
        book['audio_urls'].append(storage.child('users').child(a).child(book_code).child(f'{audio_file}.mp3').get_url(token=idtoken))
    book['currentFile'] = int(book['currentFile'])
    return render(request, 'player.html', { 'current_user':current_user,'page':'player','book':book })


def postDeleteBook(request):
    bookCode = request.POST.get('bookCode')
    idtoken = request.session['uid']

    a = authe.get_account_info(idtoken)
    a = a['users']
    a = a[0]
    a = a['localId']
    
    # storage.child('users').child(a).child(bookCode).remove(token=idtoken)
    database.child(a).child(bookCode).remove(token=idtoken)

    return redirect(reverse('panel'))

def postTimeUpdate(request):


    idtoken = request.session['uid']
    try:
        a = authe.get_account_info(idtoken)
    except Exception:
        return redirect(reverse('signIn'))
    a = authe.get_account_info(idtoken)
    a = a['users']
    a = a[0]
    a = a['localId']

    book_code = request.POST.get('bookCode')
    locSec = request.POST.get('locSec')

    database.child(a).child(book_code).update({'locSec':locSec}, token=idtoken)
    

    return HttpResponse("OK")

