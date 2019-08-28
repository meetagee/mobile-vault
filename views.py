from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import Template, Context
from django.template.loader import get_template
from django.shortcuts import render
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
import datetime
import os
import shutil
from os import path

# returns a list of lines from the file
def read_file(filename):
    with open(os.path.join(settings.MEDIA_ROOT, filename), 'r') as f:
        lines = f.read().splitlines()
    return lines

# writes string to file (w for overwrite)
def write_file_string(filename, data, protocol):
    with open(os.path.join(settings.MEDIA_ROOT, filename), protocol) as f:
        f.write(data)

####################################
# ENDPOINTS
####################################

def current_datetime(request):
    now = datetime.datetime.now()
    return render(request, 'current_datetime.html', {'current_date': now})

def hours_ahead(request, offset):
    try:
        offset = int(offset)
    except ValueError:
        raise Http404()
    dt = datetime.datetime.now() + datetime.timedelta(hours=offset)
    return render(request, 'hours_ahead.html', {'offset': offset, 'new_date': dt})

def getData(request):
    with open(os.path.join(settings.MEDIA_ROOT, 'data.txt'), 'r') as f:
        lines = f.read().splitlines()
        last_line = lines[-1]
    return HttpResponse(str(last_line))

@csrf_exempt
def storeData(request):
    save_path = os.path.join(settings.MEDIA_ROOT, '')
    with open(os.path.join(settings.MEDIA_ROOT, 'data.txt'), 'ab+') as dest:
        for chunk in request.FILES['file'].chunks():
            dest.write(chunk)
        dest.write(b'\n')

    return HttpResponse("uploaded data")

def restart(request):
    write_file_string("motion.txt", "off", "w+")

    return HttpResponse("restarted server data")

@csrf_exempt
def sendImage(request):
    save_path = os.path.join(settings.MEDIA_ROOT, '')
    with open(os.path.join(settings.MEDIA_ROOT, 'snapshot.jpg'), 'wb+') as dest:
        for chunk in request.FILES['file'].chunks():
            dest.write(chunk)

    return HttpResponse("uploaded image")


@csrf_exempt
def sendIntruderImage(request):

    if path.exists("/home/pi/Documents/securitySystem/media/intruder" + str(5) + ".jpg"):
        os.remove("/home/pi/Documents/securitySystem/media/intruder" + str(5) + ".jpg")
    i=4
    while i > 0:
        if path.exists("/home/pi/Documents/securitySystem/media/intruder" + str(i) + ".jpg"):
            os.rename("/home/pi/Documents/securitySystem/media/intruder" + str(i)+ ".jpg", "/home/pi/Documents/securitySystem/media/intruder"+str(i+1)+".jpg")
        i -= 1

    save_path = os.path.join(settings.MEDIA_ROOT, '')
    with open(os.path.join(settings.MEDIA_ROOT, 'intruder1.jpg'), 'wb+') as dest:
        for chunk in request.FILES['file'].chunks():
            dest.write(chunk)

    updateIntruderLog()
    return HttpResponse("uploaded image")

def getIntruderImage(request, imageNumber):
    with open(os.path.join(settings.MEDIA_ROOT, 'intruder'+str(imageNumber)+'.jpg'), 'rb') as f:
        data = f.read()

    response = HttpResponse(data, content_type='image/jpeg')
    response['Content-Disposition'] = 'attachment; filename="intruder"+str(imageNumber)+".jpg"'

    return response

def updateIntruderLog():
    timed = str(datetime.datetime.now() - datetime.timedelta(hours=7))
    #timed = '{%Y-%m-%d %H:%M:%S}'.format(timed)
    #timed = str(datetime.datetime.now())  #.strftime('%Y-%m-%d %H:%M:%S')
    # timed = "test"
    with open(os.path.join(settings.MEDIA_ROOT, 'intruderLog.txt'), 'r') as f:
        lines = f.read().splitlines()

    if (len(lines) == 5):
        lines = lines[0:4]

    lines.insert(0, timed)

    with open(os.path.join(settings.MEDIA_ROOT, 'intruderLog.txt'), 'w+') as f:
        for line in lines:
            f.write(line + "\n")


def getIntruderTime(request, intruderNumber):
    try:
        return HttpResponse(str(read_file('intruderLog.txt')[int(intruderNumber) - 1]))
    except IndexError:
        return HttpResponse("Time not updated")

def intruderOn(request):
    write_file_string("intruderStatus.txt", "on", "w+")
    return HttpResponse("updated intruder status")

def intruderOff(request):
    write_file_string("intruderStatus.txt", "off", "w+")
    return HttpResponse("updated intruder status")

def getIntruderStatus(request):
    return HttpResponse(str(read_file('intruderStatus.txt')[-1]))

def getImage(request):
    with open(os.path.join(settings.MEDIA_ROOT, 'snapshot.jpg'), 'rb') as f:
        data = f.read()

    response = HttpResponse(data, content_type='image/jpeg')
    response['Content-Disposition'] = 'attachment; filename="snapshot.jpg"'

    return response

def sendMotionOn(request):
    change_from_off_to_on = (read_file("motion.txt")[-1] != "on")
    if (change_from_off_to_on):
        write_file_string("motion.txt", "on", "w+")

    return HttpResponse("updated motion data")

def sendMotionOff(request):
    change_from_on_to_off = (read_file("motion.txt")[-1] != "off")
    if (change_from_on_to_off):
        write_file_string("motion.txt", "off", "w+")

    return HttpResponse("updated motion data")

def getMotionCurrent(request):
    return HttpResponse(str(read_file("motion.txt")[-1]))

def turnOnLED(request):
    with open(os.path.join(settings.MEDIA_ROOT, 'ledStatus.txt'), 'w+') as f:
        f.write("on")

    return HttpResponse("success")

def turnOffLED(request):
    with open(os.path.join(settings.MEDIA_ROOT, 'ledStatus.txt'), 'w+') as f:
        f.write("off")

    return HttpResponse("success")

def LEDstatus(request):
    with open(os.path.join(settings.MEDIA_ROOT, 'ledStatus.txt'), 'r') as f:
        lines = f.read().splitlines()
        last_line = lines[-1]
    return HttpResponse(str(last_line))

def updatePassword(request, passW):
    write_file_string("password.txt", passW, 'w+')
    return HttpResponse("updated password")

def getPassword(request):
    return HttpResponse(read_file('password.txt')[-1])

def getDoorStatus(request):
    return HttpResponse(read_file('doorstatus.txt')[-1])

def sendDoorStatusOn(request):
    write_file_string("doorstatus.txt", "on", 'w+')
    return HttpResponse('updated door status')

def sendDoorStatusOff(request):
    write_file_string("doorstatus.txt", "off", 'w+')
    return HttpResponse('updated door status')

def home(request):
    return render(request, 'index.html')

def login(request):
    return render(request, 'login.html')

def lockmanage(request):
    return render(request, 'lockManagement.html')

def contact(request):
    return render(request, 'contact.html')

def aboutUs(request):
    return render(request, 'aboutUs.html')
