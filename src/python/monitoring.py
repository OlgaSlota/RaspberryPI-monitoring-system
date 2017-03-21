#Monitoring system for RaspberryPi, created by Olga Słota & Artur Czopek

from gpiozero import DistanceSensor, RGBLED, Button
from signal import pause

from email.mime.multipart import MIMEMultipart, MIMEBase
from email.mime.text import MIMEText
from email import Encoders

import ConfigParser
import subprocess
import smtplib
import datetime
import os
import time

#Devices config
led = RGBLED(13, 19, 26)
button = Button(17)
ultrasonic = DistanceSensor(12, 16, threshold_distance=0.2, max_distance=2)

#Color values
redColor = (1,0,0)
greenColor = (0,1,0)

#Properties for ffmpeg library
recordLib = 'ffmpeg'
codec = 'v4l2'
frames = '25'
resolution = '1024x768'
cameraPath = '/dev/video0'
outputPathTemplate = '/tmp/monitoring_video_{0}.avi'

#Values from monitoring.properties file will be parsed into this variables)
video = {}
email = {}
smtp = {}

def readProps():
    config = ConfigParser.RawConfigParser()
    config.read('monitoring.properties')

    global video
    video = {
     'length': time.strftime("%H:%M:%S", time.gmtime(int(config.get('VideoSection', 'video.length'))))  
    }

    global email
    email = {
     'topic': config.get('EmailSection', 'email.topic'),
     'to': config.get('EmailSection', 'email.to'),
     'from': config.get('EmailSection', 'email.from')
    }

    global smtp
    smtp = {
     'server': config.get('SmtpSection', 'smtp.server'),
     'user': config.get('SmtpSection', 'smtp.user'),
     'password': config.get('SmtpSection', 'smtp.password')
    }

#example call: "ffmpeg -f v4l2 -r 25 -t 00:00:05 -s 1024x768 -i /dev/video0 /tmp/monitoring_video.avi"

def recordVideo():
    led.color = redColor
    print('=============================================')
    print('Recording...')
    date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%s')
    outputPath = outputPathTemplate.format(date)
    subprocess.call([recordLib, '-f', codec, '-r', frames, '-t', video.get('length'), '-s', resolution, '-i', cameraPath, outputPath])
    print('Recorded video')
    sendEmail(outputPath)
    print('=============================================')
    led.color = greenColor


def sendEmail(filePath):
    msg = MIMEMultipart()
    msg['To'] = email.get('email.to')
    msg['From'] = email.get('email.from')
    msg['Subject'] = email.get('topic')

    attachment = MIMEBase('application', "octet-stream")
    attachment.set_payload(open(filePath,"rb").read() )
    Encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(filePath))
    msg.attach(attachment)
 
    smtpClient = smtplib.SMTP(smtp.get('server'))
    smtpClient.login(smtp.get('user'), smtp.get('password'))
    print('Sending email...')
    smtpClient.sendmail(email.get('from'), email.get('to'), msg.as_string())
    print('Sent email')
    smtpClient.quit()

#Main action
def main():
    readProps()
    led.on()
    led.color = greenColor
    button.when_pressed = recordVideo
    ultrasonic.when_in_range = recordVideo
    pause()

if __name__ == '__main__':
    main()   
    

