from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name = 'home'),
    path('signIn/', views.signIn, name = 'signIn'),
    path('postSignIn/', views.postSignIn, name = 'postSignIn'),
    path('logout/', views.logout, name = 'logout'),
    path('signUp/', views.signUp, name = 'signUp'),
    path('postSignUp/', views.postSignUp, name = 'postSignUp'),
    path('create/', views.create, name = 'create'),
    path('post_create/', views.post_create, name = 'post_create'),
    path('panel', views.panel, name = 'panel'),
    path('player/<book_code>', views.player, name = 'player'),
    path('postTimeUpdate/', views.postTimeUpdate, name = 'postTimeUpdate'),
    path('postDeleteBook/', views.postDeleteBook, name = 'postDeleteBook'),
]