"""securitySystem URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from securitySystem.views import contact, aboutUs, lockmanage, current_datetime, hours_ahead, getData, storeData, home, sendImage, getImage, sendIntruderImage, getIntruderImage, sendMotionOn, sendMotionOff, getMotionCurrent, turnOnLED, turnOffLED, LEDstatus, login, restart, getIntruderTime, getPassword, updatePassword, getDoorStatus, sendDoorStatusOn, sendDoorStatusOff, intruderOn, intruderOff, getIntruderStatus

urlpatterns = [
    path('', admin.site.urls),
    path('admin/', admin.site.urls),
    path('time/currentTime/', current_datetime),
    re_path('time/currentTime/plus/(\d{1,2})/', hours_ahead),
    path('getData', getData),
    re_path('storeData/', storeData),

    re_path('home/', home),
    re_path('lockmanage/', lockmanage),
	re_path('contact', contact),
	re_path('aboutus', aboutUs),
	
    re_path('loginsecure/', login),
	

    re_path('restart/', restart),
    re_path('sendImage/', sendImage),
    re_path('getImage', getImage),
    re_path('sendMotionOn', sendMotionOn),
    re_path('sendMotionOff', sendMotionOff),
    re_path('getMotionCurrent', getMotionCurrent),

    re_path('turnOnLED', turnOnLED),
    re_path('turnOffLED', turnOffLED),
    re_path('LEDstatus', LEDstatus),

    re_path('sendIntruderImage', sendIntruderImage),
    re_path('getIntruderImage/(\d{1})', getIntruderImage),
    re_path('getIntruderTime/(\d{1})', getIntruderTime),
    re_path('intruderOn', intruderOn),
    re_path('intruderOff', intruderOff),
    re_path('getIntruderStatus', getIntruderStatus),

    re_path('updatePassword/(\d{4})', updatePassword),
    re_path('getPassword', getPassword),

    re_path('getDoorStatus', getDoorStatus),
    re_path('sendDoorStatusOn', sendDoorStatusOn),
    re_path('sendDoorStatusOff', sendDoorStatusOff)
]
