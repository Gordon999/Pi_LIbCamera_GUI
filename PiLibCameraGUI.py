#!/usr/bin/env python3

"""Copyright (c) 2022
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

import time
import pygame
from pygame.locals import *
import os, sys
import datetime
import subprocess
import signal
import cv2
import glob

# version v1.4

# set displayed preview image size (must be less than screen size to allow for menu!!)
# recommended 640x480, 800x600, 1280x960
preview_width  = 800 
preview_height = 600

# set default values (see limits below)
mode        = 1       # set camera mode ['manual','normal','sport'] 
speed       = 13      # position in shutters list
gain        = 0       # set gain 
brightness  = 0       # set camera brightness
contrast    = 70      # set camera contrast 
ev          = 0       # eV correction 
blue        = 12      # blue balance 
red         = 15      # red balance 
extn        = 0       # still file type
vlen        = 10      # video length in seconds
fps         = 25      # video fps
vformat     = 4       # set video format
codec       = 0       # set video codec
tinterval   = 5       # time between timelapse shots in seconds
tshots      = 5       # number of timelapse shots
frame       = 0       # set to 1 for no frame (i.e. if using Pi 7" touchscreen)
saturation  = 10      # picture colour saturation
meter       = 0       # metering mode
awb         = 1       # auto white balance mode, off, auto etc
sharpness   = 1       # set sharpness level
denoise     = 0       # set denoise level

# NOTE if you change any of the above defaults you need to delete the config_file and restart.

# default directories and files
pic_dir     = "/home/pi/Pictures/"
vid_dir     = "/home/pi/Videos/"
config_file = "/home/pi/PiLCConfig3.txt"

# Camera max exposure (Note v1 is currently 1 second not the raspistill 6 seconds)
# whatever value set it MUST be in shutters list !!
max_v1      = 1
max_v2      = 10
max_hq      = 239
max_ar      = 10 # ???

# inital parameters
zx          = int(preview_width/2)
zy          = int(preview_height/2)
zoom        = 0
igw         = 2592
igh         = 1944
zwidth      = igw 
zheight     = igh
if tinterval > 0:
    tduration  = tshots * tinterval
else:
    tduration = 5

# set button sizes
bw = int(preview_width/8)
bh = int(preview_height/13)
ft = int(preview_width/52)
fv = int(preview_width/52)

# data
modes        = ['manual','normal','sport']
extns        = ['jpg','png','bmp','rgb','yuv420','raw']
extns2       = ['jpg','png','bmp','data','data','jpg']
vwidths      = [640,800,1280,1280,1920,2592,3280,4056,4656]
vheights     = [480,600, 720, 960,1080,1944,2464,3040,3496]
v_max_fps    = [90 , 40,  40,  40,  30,  20,  20,  20,  20]
shutters     = [-2000,-1600,-1250,-1000,-800,-640,-500,-400,-320,-288,-250,-240,-200,-160,-144,-125,-120,-100,-96,-80,-60,-50,-48,-40,-30,-25,-20,-15,-13,-10,-8,-6,-5,-4,-3,
                0.4,0.5,0.6,0.8,1,1.1,1.2,2,3,4,5,6,7,8,9,10,15,20,25,30,40,50,60,75,100,120,150,200,220,230,239]
codecs       = ['h264','mjpeg','yuv420']
codecs2      = ['h264','mjpeg','data']
meters       = ['centre','spot','average']
awbs         = ['off','auto','incandescent','tungsten','fluorescent','indoor','daylight','cloudy']
denoises     = ['off','cdn_off','cdn_fast','cdn_hq']
still_limits = ['mode',0,len(modes)-1,'speed',0,len(shutters)-1,'gain',0,20,'brightness',-100,100,'contrast',0,200,'ev',-10,10,'blue',1,80,'red',1,80,'extn',0,len(extns)-1,'saturation',0,20,'meter',0,len(meters)-1,'awb',0,len(awbs)-1]
video_limits = ['vlen',1,999,'fps',1,40,'vformat',0,4,'0',0,0,'sharpness',0,4,'denoise',0,len(denoises)-1,'zoom',0,4,'Focus',0,1,'tduration',1,9999,'tinterval',0,999,'tshots',1,999,'flicker',0,3,'codec',0,len(codecs)-1]

# check config_file exists, if not then write default values
if not os.path.exists(config_file):
    points = [mode,speed,gain,brightness,contrast,frame,red,blue,ev,vlen,fps,vformat,codec,tinterval,tshots,extn,zx,zy,zoom,saturation,meter,awb,sharpness,denoise]
    with open(config_file, 'w') as f:
        for item in points:
            f.write("%s\n" % item)

# read config_file
config = []
with open(config_file, "r") as file:
   line = file.readline()
   while line:
      config.append(line.strip())
      line = file.readline()
config = list(map(int,config))

mode        = config[0]
speed       = config[1]
gain        = config[2]
brightness  = config[3]
contrast    = config[4]
fullscreen  = config[5]
red         = config[6]
blue        = config[7]
ev          = config[8]
vlen        = config[9]
fps         = config[10]
vformat     = config[11]
codec       = config[12]
tinterval   = config[13]
tshots      = config[14]
extn        = config[15]
zx          = config[16]
zy          = config[17]
zoom        = config[18]
saturation  = config[19]
meter       = config[20]
awb         = config[21]
sharpness   = config[22]
denoise     = config[23]

# Check for Pi Camera version
if os.path.exists('test.jpg'):
   os.rename('test.jpg', 'oldtest.jpg')
rpistr = "libcamera-jpeg -n -t 1000 -e jpg -o test.jpg "
os.system(rpistr)
rpistr = ""
time.sleep(2)
if os.path.exists('test.jpg'):
   imagefile = 'test.jpg'
   image = pygame.image.load(imagefile)
   igw = image.get_width()
   igh = image.get_height()
   if igw == 2592:
      Pi_Cam = 1
      max_shutter = max_v1
   elif igw == 3280:
      Pi_Cam = 2
      max_shutter = max_v2
   elif igw == 4056:
      Pi_Cam = 3
      max_shutter = max_hq
   elif igw == 4656:
      Pi_Cam = 4
      max_shutter = max_ar
else:
   Pi_Cam = 0
   max_shutter = max_v1

if codec > 0 and Pi_Cam == 4: # Arducam IMX519 16MP
    max_vformat = 8
elif codec > 0 and Pi_Cam == 3:
    max_vformat = 7
elif codec > 0 and Pi_Cam == 2:
    max_vformat = 6
elif codec > 0 and Pi_Cam == 1:
    max_vformat = 5
else:
    max_vformat = 4
if vformat > max_vformat:
    vformat = max_vformat
vwidth    = vwidths[vformat]
vheight   = vheights[vformat]
vfps      = v_max_fps[vformat]
if tinterval > 0:
    tduration = tinterval * tshots
else:
    tduration = 5

shutter = shutters[speed]
if shutter < 0:
    shutter = abs(1/shutter)
sspeed = int(shutter * 1000000)
if (shutter * 1000000) - int(shutter * 1000000) > 0.5:
    sspeed +=1

pygame.init()
if frame == 0:
   windowSurfaceObj = pygame.display.set_mode((preview_width + (bw*2),preview_height ), 0, 24)
else:
   windowSurfaceObj = pygame.display.set_mode((preview_width + bw,preview_height), pygame.NOFRAME, 24)
pygame.display.set_caption('Pi LibCamera GUI')

global greyColor, redColor, greenColor, blueColor, dgryColor, lgrnColor, blackColor, whiteColor, purpleColor, yellowColor,lpurColor,lyelColor
bredColor =   pygame.Color(255,   0,   0)
lgrnColor =   pygame.Color(162, 192, 162)
lpurColor =   pygame.Color(192, 162, 192)
lyelColor =   pygame.Color(192, 192, 162)
blackColor =  pygame.Color(  0,   0,   0)
whiteColor =  pygame.Color(200, 200, 200)
greyColor =   pygame.Color(128, 128, 128)
dgryColor =   pygame.Color( 64,  64,  64)
greenColor =  pygame.Color(  0, 255,   0)
purpleColor = pygame.Color(255,   0, 255)
yellowColor = pygame.Color(255, 255,   0)
blueColor =   pygame.Color(  0,   0, 255)
redColor =    pygame.Color(200,   0,   0)

def button(col,row, bkgnd_Color,border_Color):
    global preview_width,bw,bh
    colors = [greyColor, dgryColor,yellowColor,purpleColor,greenColor,whiteColor,lgrnColor,lpurColor,lyelColor]
    Color = colors[bkgnd_Color]
    bx = preview_width + (col * bw)
    by = row * bh
    pygame.draw.rect(windowSurfaceObj,Color,Rect(bx,by,bw-1,bh))
    pygame.draw.line(windowSurfaceObj,colors[border_Color],(bx,by),(bx+bw,by))
    pygame.draw.line(windowSurfaceObj,greyColor,(bx+bw-1,by),(bx+bw-1,by+bh))
    pygame.draw.line(windowSurfaceObj,colors[border_Color],(bx,by),(bx,by+bh-1))
    pygame.draw.line(windowSurfaceObj,dgryColor,(bx,by+bh-1),(bx+bw-1,by+bh-1))
    pygame.display.update(bx, by, bw, bh)
    return

def text(col,row,fColor,top,upd,msg,fsize,bkgnd_Color):
    global bh,preview_width,fv
    colors =  [dgryColor, greenColor, yellowColor, redColor, purpleColor, blueColor, whiteColor, greyColor, blackColor, purpleColor,lgrnColor,lpurColor,lyelColor]
    Color  =  colors[fColor]
    bColor =  colors[bkgnd_Color]
    bx = preview_width + (col * bw)
    by = row * bh
    if os.path.exists ('/usr/share/fonts/truetype/freefont/FreeSerif.ttf'): 
        fontObj = pygame.font.Font('/usr/share/fonts/truetype/freefont/FreeSerif.ttf', int(fsize))
    else:
        fontObj = pygame.font.Font(None, int(fsize))
    msgSurfaceObj = fontObj.render(msg, False, Color)
    msgRectobj = msgSurfaceObj.get_rect()
    if top == 0:
        pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+1,by+10,bw-4,int(bh/2.8)))
        msgRectobj.topleft = (bx + 5, by + 8)
    elif msg == "Timelapse" or msg == "Config" or msg == "Video   T'Lapse":
        pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+2,by+int(bh/1.8),int(bw/2),int(bh/2.2)-1))
        msgRectobj.topleft = (bx+5,  by + int(bh/1.8))
    elif top == 1:
        pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+20,by+int(bh/1.8),int(bw-21),int(bh/2.2)-1))
        msgRectobj.topleft = (bx + 20, by + int(bh/1.8)) 
    elif top == 2:
        if bkgnd_Color == 1:
            pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,0,preview_width,fv*2))
        msgRectobj.topleft = (0,row * fsize)
    windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
    if upd == 1 and top == 2:
        pygame.display.update(0,0,preview_width,fv*2)
    if upd == 1:
        pygame.display.update(bx, by, bw, bh)

def draw_bar(col,row,color,msg,value):
    global bw,bh,preview_width,still_limits,max_speed
    for f in range(0,len(still_limits)-1,3):
        if still_limits[f] == msg:
            pmin = still_limits[f+1]
            pmax = still_limits[f+2]
    if msg == "speed":
        pmax = max_speed
    pygame.draw.rect(windowSurfaceObj,color,Rect(preview_width + col*bw,row * bh,bw-1,10))
    if pmin > -1: 
        j = value / (pmax - pmin)  * bw
    else:
        j = int(bw/2) + (value / (pmax - pmin)  * bw)
    j = min(j,bw-5)
    pygame.draw.rect(windowSurfaceObj,(0,200,0),Rect(preview_width + (col*bw) + 2,row * bh,j+1,10))
    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(preview_width + (col*bw) + j ,row * bh,4,10))
    pygame.display.update()

def draw_Vbar(col,row,color,msg,value):
    global bw,bh,preview_width,video_limits
    for f in range(0,len(video_limits)-1,3):
        if video_limits[f] == msg:
            pmin = video_limits[f+1]
            pmax = video_limits[f+2]
    if msg == "vformat":
        pmax = max_vformat
    pygame.draw.rect(windowSurfaceObj,color,Rect(preview_width + col*bw,row * bh,bw-1,10))
    if pmin > -1: 
        j = value / (pmax - pmin)  * bw
    else:
        j = int(bw/2) + (value / (pmax - pmin)  * bw)
    j = min(j,bw-5)
    pygame.draw.rect(windowSurfaceObj,(150,120,150),Rect(preview_width + (col*bw) + 2,row * bh,j+1,10))
    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(preview_width + (col*bw) + j ,row * bh,4,10))
    pygame.display.update()

def preview():
    global restart,rpistr,count,p, brightness,contrast,modes,mode,red,blue,gain,sspeed,ev,preview_width,preview_height,zoom,igw,igh,zx,zy,awbs,awb,saturations,saturation,meters,meter,flickers,flicker,sharpnesss,sharpness
    files = glob.glob('/run/shm/*')
    for f in files:
        os.remove(f)
    speed2 = sspeed
    if speed2 > 6000000:
        speed2 = 6000000
    rpistr = "libcamera-vid -n --codec mjpeg -t 0 --segment 100"
    if Pi_Cam == 4:
        rpistr += " --width 1920 --height 1440 -o /run/shm/test%d.jpg "
    else:
        if preview_width == 640 and preview_height == 480:
            rpistr += " --width 720 --height 540 -o /run/shm/test%d.jpg "
        else:
            rpistr += " --width " + str(preview_width) + " --height " + str(preview_height) + " -o /run/shm/test%d.jpg "
    rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
    if mode == 0:
        rpistr += " --shutter " + str(speed2) + " --framerate " + str(1000000/speed2)
    else:
        rpistr += " --exposure " + str(modes[mode])
    if ev != 0:
        rpistr += " --ev " + str(ev)
    if sspeed > 5000000 and mode == 0:
        rpistr += " --gain 1 --awbgain 1,1 --immediate"
    else:
        rpistr += " --gain " + str(gain)
        if awb == 0:
            rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
        else:
            rpistr += " --awb " + awbs[awb]
    rpistr += " --metering "   + meters[meter]
    rpistr += " --saturation " + str(saturation/10)
    rpistr += " --sharpness "  + str(sharpness)
    rpistr += " --denoise "    + denoises[denoise]
    if Pi_Cam == 4:
        rpistr += " --autofocus "
    if zoom > 0 and zoom < 10:
        zwidth = preview_width * (5-zoom)
        if zwidth > igw:
            zwidth = igw - int(igw/20) 
        zheight = preview_height * (5-zoom)
        #print (zwidth,zheight)
        if zheight > igh:
            zheight = igh - int(igh/20)
        zxo = ((igw-zwidth)/2)/igw
        zyo = ((igh-zheight)/2)/igh
        rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(zwidth/igw) + "," + str(zheight/igh)
    if zoom == 10:
        zxo = ((zx -((preview_width/2) / (igw/preview_width)))/preview_width)
        zyo = ((zy -((preview_height/2) / (igh/preview_height)))/preview_height)
        rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
    #print (rpistr)
    p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
    restart = 0
    time.sleep(2)

# draw buttons
for d in range(1,13):
        button(0,d,6,4)
for d in range(1,5):
        button(1,d,7,3)
for d in range(7,10):
        button(1,d,8,2)
button(0,0,0,4)
button(1,0,0,3)
button(1,5,0,6)
button(1,6,0,6)
button(1,6,0,2)
button(1,10,6,4)
button(1,11,6,4)
button(1,12,0,5)

# write button texts
text(0,0,1,0,1,"CAPTURE",ft,7)
text(0,0,1,1,1,"Still",ft,7)
text(1,0,1,0,1,"CAPTURE",ft,7)
text(1,0,1,1,1,"Video",ft,7)
text(0,1,5,0,1,"Mode",ft,10)
text(0,1,3,1,1,modes[mode],fv,10)
text(0,2,5,0,1,"Shutter S",ft,10)
if mode == 0:
    if shutters[speed] < 0:
        text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
    else:
        text(0,2,3,1,1,str(shutters[speed]),fv,10)
else:
    if shutters[speed] < 0:
        text(0,2,0,1,1,"1/" + str(abs(shutters[speed])),fv,10)
    else:
        text(0,2,0,1,1,str(shutters[speed]),fv,10)
text(0,3,5,0,1,"Gain",ft,10)
text(0,3,3,1,1,str(gain),fv,10)
text(0,4,5,0,1,"Brightness",ft,10)
text(0,4,3,1,1,str(brightness/100)[0:4],fv,10)
text(0,5,5,0,1,"Contrast",ft,10)
text(0,5,3,1,1,str(contrast/100)[0:4],fv,10)
text(0,6,5,0,1,"eV",ft,10)
if mode != 0:
    text(0,6,3,1,1,str(ev),fv,10)
else:
    text(0,6,0,1,1,str(ev),fv,10)
text(0,7,5,0,1,"Blue",ft,10)
text(0,8,5,0,1,"Red",ft,10)
if awb == 0:
    text(0,8,3,1,1,str(red/10)[0:3],fv,10)
    text(0,7,3,1,1,str(blue/10)[0:3],fv,10)
else:
    text(0,8,0,1,1,str(red/10)[0:3],fv,10)
    text(0,7,0,1,1,str(blue/10)[0:3],fv,10)
text(0,9,5,0,1,"File Format",ft,10)
text(0,9,3,1,1,extns[extn],fv,10)
if zoom == 0:
    button(1,5,0,4)
    text(1,5,5,0,1,"Focus  /  Zoom",ft,7)
    text(1,5,3,1,1,"",fv,7)
    text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
elif zoom < 10:
    button(1,5,1,4)
    text(1,5,2,0,1,"ZOOMED",ft,0)
    text(1,5,3,1,1,str(zoom),fv,0)
    text(1,3,3,1,1,str(preview_width) + "x" + str(preview_height),fv,11)
else:
    button(1,5,1,4)
    text(1,5,3,0,1,"FOCUS",ft,0)
    text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
text(0,10,5,0,1,"AWB",ft,10)
text(0,10,3,1,1,awbs[awb],fv,10)
text(0,11,5,0,1,"Saturation",fv,10)
text(0,11,3,1,1,str(saturation/10),fv,10)
text(0,12,5,0,1,"Metering",fv,10)
text(0,12,3,1,1,meters[meter],fv,10)

text(1,1,5,0,1,"V_Length S",ft,11)
text(1,1,3,1,1,str(vlen),fv,11)
text(1,2,5,0,1,"V_FPS",ft,11)
text(1,2,3,1,1,str(fps),fv,11)
text(1,3,5,0,1,"V_Format",ft,11)
text(1,4,5,0,1,"V_Codec",ft,11)
text(1,4,3,1,1,codecs[codec],fv,11)
text(1,6,1,0,1,"CAPTURE",ft,7)
text(1,6,1,1,1,"Timelapse",ft,7)
text(1,7,5,0,1,"Duration S",ft,12)
text(1,7,3,1,1,str(tduration),fv,12)
text(1,8,5,0,1,"Interval S",ft,12)
text(1,8,3,1,1,str(tinterval),fv,12)
text(1,9,5,0,1,"No. of Shots",ft,12)
if tinterval > 0:
    text(1,9,3,1,1,str(tshots),fv,12)
else:
    text(1,9,3,1,1," ",fv,12)
text(1,10,5,0,1,"Denoise",fv,10)
text(1,10,3,1,1,denoises[denoise],fv,10)
text(1,11,5,0,1,"Sharpness",fv,10)
text(1,11,3,1,1,str(sharpness),fv,10)
text(1,12,2,0,1,"Save      EXIT",fv,7)
text(1,12,2,1,1,"Config",fv,7)

# draw sliders
draw_bar(0,1,lgrnColor,'mode',mode)
draw_bar(0,3,lgrnColor,'gain',gain)
draw_bar(0,4,lgrnColor,'brightness',brightness)
draw_bar(0,5,lgrnColor,'contrast',contrast)
draw_bar(0,6,lgrnColor,'ev',ev)
draw_bar(0,7,lgrnColor,'blue',blue)
draw_bar(0,8,lgrnColor,'red',red)
draw_bar(0,9,lgrnColor,'extn',extn)
draw_bar(0,10,lgrnColor,'awb',awb)
draw_bar(0,11,lgrnColor,'saturation',saturation)
draw_bar(0,12,lgrnColor,'meter',meter)
draw_Vbar(1,1,lpurColor,'vlen',vlen)
draw_Vbar(1,2,lpurColor,'fps',fps)
draw_Vbar(1,3,lpurColor,'vformat',vformat)
draw_Vbar(1,4,lpurColor,'codec',codec)
draw_Vbar(1,7,lyelColor,'tduration',tduration)
draw_Vbar(1,8,lyelColor,'tinterval',tinterval)
draw_Vbar(1,9,lyelColor,'tshots',tshots)
draw_Vbar(1,10,lgrnColor,'denoise',denoise)
draw_Vbar(1,11,lgrnColor,'sharpness',sharpness)


text(0,0,6,2,1,"Please Wait, checking camera",int(fv* 1.7),1)
pygame.display.update()

# determine max speed for camera
max_speed = 0
while max_shutter > shutters[max_speed]:
    max_speed +=1
    
if Pi_Cam > 0:
    if Pi_Cam < 4:
        text(0,0,6,2,1,"Found Pi Camera v" + str(Pi_Cam),int(fv*1.7),1)
    else:
        text(0,0,6,2,1,"Found Arducam 16MP Autofocus",int(fv*1.7),1)
    time.sleep(1)
else:
    text(0,0,6,2,1,"No Pi Camera found",int(fv*1.7),1)
    time.sleep(1)
    
# set maximum speed, based on camera version
if speed > max_speed:
    speed = max_speed
    shutter = shutters[speed]
    if shutter < 0:
        shutter = abs(1/shutter)
    sspeed = int(shutter * 1000000)
    if mode == 0:
        if shutters[speed] < 0:
            text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
        else:
            text(0,2,3,1,1,str(shutters[speed]),fv,10)
    else:
        if shutters[speed] < 0:
            text(0,2,0,1,1,"1/" + str(abs(shutters[speed])),fv,10)
        else:
            text(0,2,0,1,1,str(shutters[speed]),fv,10)
draw_bar(0,2,lgrnColor,'speed',speed)
pygame.display.update()
time.sleep(.25)

# start preview
text(0,0,6,2,1,"Please Wait for preview...",int(fv*1.7),1)
preview()

# main loop
while True:
    time.sleep(0.1)
    pics = glob.glob('/run/shm/*.jpg')
    if len(pics) > 1:
        try:
            image = pygame.image.load(pics[1])
            #os.remove(pics[len(pics)-1])
            for tt in range(1,len(pics)):
                 os.remove(pics[tt])
        except pygame.error:
            pass
        image = pygame.transform.scale(image, (preview_width,preview_height))
        windowSurfaceObj.blit(image, (0, 0))
        if zoom > 0:
            image2 = pygame.surfarray.pixels3d(image)
            crop2 = image2[zx-50:zx+50,zy-50:zy+50]
            gray = cv2.cvtColor(crop2,cv2.COLOR_RGB2GRAY)
            foc = cv2.Laplacian(gray, cv2.CV_64F).var()
            text(20,0,3,2,0,"Focus: " + str(int(foc)),fv* 2,0)
            xx = int(preview_width/2)
            xy = int(preview_height/2)
            pygame.draw.line(windowSurfaceObj,redColor,(xx-25,xy),(xx+25,xy),1)
            pygame.draw.line(windowSurfaceObj,redColor,(xx,xy-25),(xx,xy+25),1)
        else:
            text(0,0,6,2,0,"Preview",fv* 2,0)
            zxp = (zx -((preview_width/2) / (igw/preview_width)))
            zyp = (zy -((preview_height/2) / (igh/preview_height)))
            zxq = (zx - zxp) * 2
            zyq = (zy - zyp) * 2
            if zxp + zxq > preview_width:
                zx = preview_width - int(zxq/2)
                zxp = (zx -((preview_width/2) / (igw/preview_width)))
                zxq = (zx - zxp) * 2
            if zyp + zyq > preview_height:
                zy = preview_height - int(zyq/2)
                zyp = (zy -((preview_height/2) / (igh/preview_height)))
                zyq = (zy - zyp) * 2
            if zxp < 0:
                zx = int(zxq/2) + 1
                zxp = 0
                zxq = (zx - zxp) * 2
            if zyp < 0:
                zy = int(zyq/2) + 1
                zyp = 0
                zyq = (zy - zyp) * 2
            if zoom == 0:
                pygame.draw.rect(windowSurfaceObj,redColor,Rect(zxp,zyp,zxq,zyq),1)
            pygame.draw.line(windowSurfaceObj,redColor,(zx-25,zy),(zx+25,zy),1)
            pygame.draw.line(windowSurfaceObj,redColor,(zx,zy-25),(zx,zy+25),1)
            if Pi_Cam == 4:
                if vwidth == 1280 and vheight == 960:
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(preview_width * 0.20,preview_height * 0.22,preview_width * 0.62,preview_height * 0.57),1)
                elif vwidth == 1280 and vheight == 720:
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(preview_width * 0.22,preview_height * 0.30,preview_width * 0.56,preview_height * 0.41),1)
                elif vwidth == 800 and vheight == 600:
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(preview_width * 0.30,preview_height * 0.30,preview_width * 0.41,preview_height * 0.41),1)
                elif vwidth == 640 and vheight == 480:
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(preview_width * 0.30,preview_height * 0.30,preview_width * 0.41,preview_height * 0.41),1)
                elif vwidth == 1920 and vheight == 1080:
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(preview_width * 0.09,preview_height * 0.20,preview_width * 0.82,preview_height * 0.62),1)
            elif (vwidth == 1920 and vheight == 1080) or (vwidth == 1280 and vheight == 720):
                pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(preview_width * 0.13,preview_height * 0.22,preview_width * 0.74,preview_height * 0.57),1)
        pygame.display.update()
    
    # continuously read mouse buttons
    buttonx = pygame.mouse.get_pressed()
    if buttonx[0] != 0 :
        #time.sleep(0.1)
        pos = pygame.mouse.get_pos()
        mousex = pos[0]
        mousey = pos[1]
        if mousex > preview_width:
          button_column = int((mousex-preview_width)/bw) + 1
          button_row = int((mousey)/bh) + 1
          if button_column == 1:
            if button_row == 2:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'mode':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    mode = int(((mousex-preview_width) / bw) * ((pmax+1)-pmin))
                    
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + (bw/2):
                        mode +=1
                        mode = min(mode,pmax)
                    else:
                        mode -=1
                        mode = max(mode,pmin)
                if mode != 0:
                    text(0,6,3,1,1,str(ev),fv,10)
                else:
                    text(0,6,0,1,1,str(ev),fv,10)
                if mode == 0:
                    if shutters[speed] < 0:
                        text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
                    else:
                        text(0,2,3,1,1,str(shutters[speed]),fv,10)
                else:
                    if shutters[speed] < 0:
                        text(0,2,0,1,1,"1/" + str(abs(shutters[speed])),fv,10)
                    else:
                        text(0,2,0,1,1,str(shutters[speed]),fv,10)
                text(0,1,3,1,1,modes[mode],fv,10)
                draw_bar(0,1,lgrnColor,'mode',mode)
                draw_bar(0,2,lgrnColor,'speed',speed)
                if mode == 0 and sspeed < 6000001 and tinterval != 0:
                    tinterval = max(tinterval,int((sspeed/1000000) * 6.33))
                if mode == 0 and sspeed > 6000000 and tinterval != 0:
                    tinterval = max(tinterval,int((sspeed/1000000)))
                text(1,8,3,1,1,str(tinterval),fv,12)
                draw_Vbar(1,9,lyelColor,'tinterval',tinterval)
                if tinterval > 0:
                    tduration = tinterval * tshots
                #else:
                #    tduration = 1
                text(1,7,3,1,1,str(tduration),fv,12)
                draw_Vbar(1,8,lyelColor,'tduration',tduration)
                time.sleep(.25)
                restart = 1

            elif button_row == 3:
                if mode == 0 :
                    for f in range(0,len(still_limits)-1,3):
                        if still_limits[f] == 'speed':
                            pmin = still_limits[f+1]
                            pmax = still_limits[f+2]
                    if mousey < ((button_row-1)*bh) + 10:
                        speed = int(((mousex-preview_width) / bw) * (max_speed-pmin))
                        shutter = shutters[speed]
                        if shutter < 0:
                            shutter = abs(1/shutter)
                        sspeed = int(shutter * 1000000)
                    elif mousey < ((button_row-1)*bh) + (bh/1.2): 
                        if mousex > preview_width + (bw/2):
                            speed +=1
                            speed = min(speed,max_speed)
                        else:
                            speed -=1
                            speed = max(pmin,speed)
                        shutter = shutters[speed]
                        if shutter < 0:
                            shutter = abs(1/shutter)
                        sspeed = int(shutter * 1000000)
                        if (shutter * 1000000) - int(shutter * 1000000) > 0.5:
                            sspeed +=1
   
                    if shutters[speed] < 0:
                        text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
                    else:
                        text(0,2,3,1,1,str(shutters[speed]),fv,10)
                    draw_bar(0,2,lgrnColor,'speed',speed)
                    if mode == 0 and sspeed < 6000001 and tinterval != 0:
                        tinterval = max(tinterval,int((sspeed/1000000) * 6.33))
                    if mode == 0 and sspeed > 6000000 and tinterval != 0:
                        tinterval = max(tinterval,int((sspeed/1000000)))
                    text(1,8,3,1,1,str(tinterval),fv,12)
                    draw_Vbar(1,9,lyelColor,'tinterval',tinterval)
                    if tinterval != 0:
                        tduration = tinterval * tshots
                    text(1,7,3,1,1,str(tduration),fv,12)
                    draw_Vbar(1,8,lyelColor,'tduration',tduration)
                    time.sleep(.25)
                    restart = 1
               
            elif button_row == 4:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'gain':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    gain = int(((mousex-preview_width) / bw) * (pmax+1-pmin))

                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex < preview_width + (bw/2):
                        gain -=1
                        gain = max(gain,pmin)
                    else:
                        gain +=1
                        gain = min(gain,pmax)
                text(0,3,3,1,1,str(gain),fv,10)
                time.sleep(.25)
                draw_bar(0,3,lgrnColor,'gain',gain)
                restart = 1
                
            elif button_row == 5:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'brightness':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    brightness = int(((mousex-preview_width) / bw) * (pmax+1-pmin)) + pmin 
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + (bw/2):
                        brightness +=1
                        brightness = min(brightness,pmax)
                    else:
                        brightness -=1
                        brightness = max(brightness,pmin)
                text(0,4,3,1,1,str(brightness/100),fv,10)
                draw_bar(0,4,lgrnColor,'brightness',brightness)
                time.sleep(0.25)
                restart = 1
                
            elif button_row == 6:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'contrast':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    contrast = int(((mousex-preview_width) / bw) * (pmax+1-pmin)) + pmin
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + (bw/2):
                        contrast +=1
                        contrast = min(contrast,pmax)
                    else:
                        contrast -=1
                        contrast = max(contrast,pmin)
                text(0,5,3,1,1,str(contrast/100)[0:4],fv,10)
                draw_bar(0,5,lgrnColor,'contrast',contrast)
                time.sleep(0.25)
                restart = 1
                
            elif button_row == 7 and mode != 0:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'ev':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    ev = int(((mousex-preview_width) / bw) * (pmax+1-pmin)) + pmin
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + (bw/2):
                        ev +=1
                        ev = min(ev,pmax)
                    else:
                        ev -=1
                        ev = max(ev,pmin)
                text(0,6,3,1,1,str(ev),fv,10)
                draw_bar(0,6,lgrnColor,'ev',ev)
                time.sleep(0.25)
                restart = 1
                
            elif button_row == 8 and awb == 0:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'blue':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    blue = (((mousex-preview_width) / bw) * (pmax+1-pmin)) 
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex < preview_width + (bw/2):
                        blue -=1
                        blue = max(blue,pmin)
                    else:
                        blue +=1
                        blue = min(blue,pmax)
                text(0,7,3,1,1,str(blue/10)[0:3],fv,10)
                draw_bar(0,7,lgrnColor,'blue',blue)
                time.sleep(.25)
                restart = 1

            elif button_row == 9 and awb == 0 :
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'red':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    red = (((mousex-preview_width) / bw) * (pmax+1-pmin)) 
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex < preview_width + (bw/2):
                        red -=1
                        red = max(red,pmin)
                    else:
                        red +=1
                        red = min(red,pmax)
                text(0,8,3,1,1,str(red/10)[0:3],fv,10)
                draw_bar(0,8,lgrnColor,'red',red)
                time.sleep(.25)
                restart = 1

            elif button_row == 10:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'extn':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    extn = int(((mousex-preview_width) / bw) * (pmax+1-pmin)) + pmin 
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex < preview_width + (bw/2):
                        extn -=1
                        extn = max(extn,pmin)
                    else:
                        extn +=1
                        extn = min(extn,pmax) 
                text(0,9,3,1,1,extns[extn],fv,10)
                draw_bar(0,9,lgrnColor,'extn',extn)
                time.sleep(.25)
                
            elif button_row == 11:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'awb':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    awb = int(((mousex-preview_width) / bw) * (pmax+1-pmin)) + pmin 
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + (bw/2):
                        awb +=1
                        awb = min(awb,pmax)
                    else:
                        awb -=1
                        awb = max(awb,pmin)
                text(0,10,3,1,1,awbs[awb],fv,10)
                draw_bar(0,10,lgrnColor,'awb',awb)
                if awb == 0:
                    text(0,8,3,1,1,str(red/10)[0:3],fv,10)
                    text(0,7,3,1,1,str(blue/10)[0:3],fv,10)
                else:
                    text(0,8,0,1,1,str(red/10)[0:3],fv,10)
                    text(0,7,0,1,1,str(blue/10)[0:3],fv,10)
                time.sleep(.25)
                restart = 1
                
            elif button_row == 12:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'saturation':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    saturation = int(((mousex-preview_width) / bw) * (pmax+1-pmin)) + pmin 
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + (bw/2):
                        saturation +=1
                        saturation = min(saturation,pmax)
                    else:
                        saturation -=1
                        saturation = max(saturation,pmin)
                text(0,11,3,1,1,str(saturation/10),fv,10)
                draw_bar(0,11,lgrnColor,'saturation',saturation)
                time.sleep(.25)
                restart = 1
                
            elif button_row == 13:
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'meter':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    meter = int(((mousex-preview_width) / bw) * (pmax+1-pmin)) + pmin 
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + (bw/2):
                        meter +=1
                        meter = min(meter,pmax)
                    else:
                        meter -=1
                        meter = max(meter,pmin)
                text(0,12,3,1,1,meters[meter],fv,10)
                draw_bar(0,12,lgrnColor,'meter',meter)
                time.sleep(.25)
                restart = 1
                
          elif button_column == 2:
            if button_row == 2:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'vlen':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    vlen = int(((mousex-preview_width - bw) / bw) * (pmax+1-pmin))
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + bw + (bw/2):
                        vlen +=1
                        vlen = min(vlen,pmax)
                    else:
                        vlen -=1
                        vlen = max(vlen,pmin)
                text(1,1,3,1,1,str(vlen),fv,11)
                draw_Vbar(1,1,lpurColor,'vlen',vlen)
                time.sleep(.25)
 
            elif button_row == 3:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'fps':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    fps = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                    fps = min(fps,vfps)
                    fps = max(fps,pmin)
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + bw + (bw/2):
                        fps +=1
                        fps = min(fps,vfps)
                    else:
                        fps -=1
                        fps = max(fps,pmin)
                text(1,2,3,1,1,str(fps),fv,11)
                draw_Vbar(1,2,lpurColor,'fps',fps)
                time.sleep(.25)
                   
            elif button_row == 4 and zoom == 0:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'vformat':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    vformat = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex < preview_width + bw + (bw/2):
                        vformat -=1
                        if codec > 0 and Pi_Cam == 3:
                            max_vformat == len(vwidths)-1
                        elif codec > 0 and Pi_Cam == 2:
                            max_vformat = 6
                        elif codec > 0 and Pi_Cam == 1:
                            max_vformat = 5
                        else:
                            max_vformat = 4
                        vformat = min(vformat,max_vformat)
                        vformat = max(vformat,pmin)
                    else:
                        vformat +=1
                        if codec > 0 and Pi_Cam == 3:
                            max_vformat == len(vwidths)-1
                        elif codec > 0 and Pi_Cam == 2:
                            max_vformat = 6
                        elif codec > 0 and Pi_Cam == 1:
                            max_vformat = 5
                        else:
                            max_vformat = 4
                        vformat = min(vformat,max_vformat)
                draw_Vbar(1,3,lpurColor,'vformat',vformat)
                vwidth  = vwidths[vformat]
                vheight = vheights[vformat]
                vfps    = v_max_fps[vformat]
                fps = min(fps,vfps)
                video_limits[5] = vfps
                text(1,2,3,1,1,str(fps),fv,11)
                draw_Vbar(1,2,lpurColor,'fps',fps)
                text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
                time.sleep(.25)

            elif button_row == 5 and zoom == 0:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'codec':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    codec = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + bw + (bw/2):
                        codec +=1
                        codec = min(codec,pmax)
                    else:
                        codec -=1
                        codec = max(codec,pmin)
                if codec > 0 and Pi_Cam == 3:
                    max_vformat == len(vwidths)-1
                elif codec > 0 and Pi_Cam == 2:
                    max_vformat = 6
                elif codec > 0 and Pi_Cam == 1:
                    max_vformat = 5
                else:
                    max_vformat = 4
                vformat = min(vformat,max_vformat)
                text(1,4,3,1,1,codecs[codec],fv,11)
                draw_Vbar(1,4,lpurColor,'codec',codec)
                draw_Vbar(1,3,lpurColor,'vformat',vformat)
                vwidth  = vwidths[vformat]
                vheight = vheights[vformat]
                vfps    = v_max_fps[vformat]
                fps = min(fps,vfps)
                video_limits[5] = vfps
                text(1,2,3,1,1,str(fps),fv,11)
                draw_Vbar(1,2,lpurColor,'fps',fps)
                text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
                time.sleep(.25)

            elif button_row == 6:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'zoom':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                
                if mousex >  preview_width + bw + (bw/2) and zoom == 0:
                    zoom +=1
                    zoom = min(zoom,pmax)
                    button(1,5,1,4)
                    text(1,5,2,0,1,"ZOOMED",ft,0)
                    text(1,5,3,1,1,str(zoom),fv,0)
                    text(1,3,3,1,1,str(preview_width) + "x" + str(preview_height),fv,11)
                elif mousex >  preview_width + bw + (bw/2) and zoom > 0 and zoom != 10:
                    zoom +=1
                    zoom = min(zoom,pmax)
                    button(1,5,1,4)
                    text(1,5,2,0,1,"ZOOMED",ft,0)
                    text(1,5,3,1,1,str(zoom),fv,0)
                    text(1,3,3,1,1,str(preview_width) + "x" + str(preview_height),fv,11)
                elif mousex <  preview_width + bw + (bw/2) and zoom > 0 and zoom < 10:
                    zoom -=1
                    if zoom == 0:
                       button(1,5,0,4)
                       text(1,5,5,0,1,"Focus  /  Zoom",ft,7)
                       text(1,5,3,1,1,"",fv,7)
                       text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
                    else:
                       button(1,5,1,4)
                       text(1,5,2,0,1,"ZOOMED",ft,0)
                       text(1,5,3,1,1,str(zoom),fv,0)
                       text(1,3,3,1,1,str(preview_width) + "x" + str(preview_height),fv,11)
                elif mousex <  preview_width + bw + (bw/2) and zoom == 0:
                    if Pi_Cam < 4:
                        zoom = 10
                        button(1,5,1,6)
                        text(1,5,3,0,1,"FOCUS",ft,0)
                        text(1,3,3,1,1,str(preview_width) + "x" + str(preview_height),fv,11)
                elif zoom == 10:
                    zoom = 0
                    button(1,5,0,4)
                    text(1,5,5,0,1,"Focus  /  Zoom",ft,7)
                    text(1,5,3,1,1,"",fv,7)
                    text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
                        
                time.sleep(.25)
                restart = 1

            elif button_row == 8:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'tduration':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    tduration = int(((mousex-preview_width - bw) / bw) * (pmax+1-pmin)) 
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + bw + (bw/2):
                        tduration +=1
                        tduration = min(tduration,pmax)
                    else:
                        tduration -=1
                        tduration = max(tduration,pmin)
                text(1,7,3,1,1,str(tduration),fv,12)
                draw_Vbar(1,7,lyelColor,'tduration',tduration)
                if tinterval > 0:
                    tshots = int(tduration / tinterval)
                    text(1,9,3,1,1,str(tshots),fv,12)
                else:
                    text(1,9,3,1,1," ",fv,12)
                #text(1,9,3,1,1,str(tshots),fv,12)
                draw_Vbar(1,9,lyelColor,'tshots',tshots)
                time.sleep(.25)

            elif button_row == 9:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'tinterval':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    tinterval = int(((mousex-preview_width-bw) / bw) * (pmax - pmin))
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + bw + (bw/2):
                        tinterval +=1
                        tinterval = min(tinterval,pmax)
                        if mode == 0 and sspeed < 6000001:
                            tinterval = max(tinterval,int((sspeed/1000000) * 6.33))
                        if mode == 0 and sspeed > 6000000:
                            tinterval = max(tinterval,int((sspeed/1000000)))
                    else:
                        tinterval -=1
                        tinterval = max(tinterval,pmin)
                text(1,8,3,1,1,str(tinterval),fv,12)
                draw_Vbar(1,8,lyelColor,'tinterval',tinterval)
                if tinterval != 0:
                    tduration = tinterval * tshots
                if tinterval == 0:
                    text(1,9,3,1,1," ",fv,12)
                else:
                    text(1,9,3,1,1,str(tshots),fv,12)
                text(1,7,3,1,1,str(int(tduration)),fv,12)
                draw_Vbar(1,7,lyelColor,'tduration',tduration)
                time.sleep(.25)
                
            elif button_row == 10 and tinterval > 0:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'tshots':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    tshots = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + bw + (bw/2):
                        tshots +=1
                        tshots = min(tshots,pmax)
                    else:
                        tshots -=1
                        tshots = max(tshots,pmin)
                text(1,9,3,1,1,str(tshots),fv,12)
                draw_Vbar(1,9,lyelColor,'tshots',tshots)
                if tduration > 0:
                    tduration = tinterval * tshots
                if tduration == 0:
                    tduration = 1
                text(1,7,3,1,1,str(tduration),fv,12)
                draw_Vbar(1,7,lyelColor,'tduration',tduration)
                time.sleep(.25)

            elif button_row == 11:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'denoise':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    denoise = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + bw + (bw/2):
                        denoise +=1
                        denoise = min(denoise,pmax)
                    else:
                        denoise -=1
                        denoise = max(denoise,pmin)
                text(1,10,3,1,1,denoises[denoise],fv,10)
                draw_Vbar(1,10,lgrnColor,'denoise',denoise)
                time.sleep(.25)
                restart = 1

            elif button_row == 12:
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'sharpness':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if mousey < ((button_row-1)*bh) + 10:
                    sharpness = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                elif mousey < ((button_row-1)*bh) + (bh/1.2):
                    if mousex > preview_width + bw + (bw/2):
                        sharpness +=1
                        sharpness = min(sharpness,pmax)
                    else:
                        sharpness -=1
                        sharpness = max(sharpness,pmin)
                text(1,11,3,1,1,str(sharpness),fv,10)
                draw_Vbar(1,11,lgrnColor,'sharpness',sharpness)
                time.sleep(.25)
                restart = 1
                
            elif button_row == 13:
                if mousex < preview_width + bw + (bw/2):
                   # save config
                   text(1,12,3,1,1,"Config",fv,7)
                   config[0] = mode
                   config[1] = speed
                   config[2] = gain
                   config[3] = int(brightness)
                   config[4] = int(contrast)
                   config[5] = frame
                   config[6] = int(red)
                   config[7] = int(blue)
                   config[8] = ev
                   config[9] = vlen
                   config[10] = fps
                   config[11] = vformat
                   config[12] = codec
                   config[13] = tinterval
                   config[14] = tshots
                   config[15] = extn
                   config[16] = zx
                   config[17] = zy
                   config[18] = zoom
                   config[19] = int(saturation)
                   config[20] = meter
                   config[21] = awb
                   config[22] = sharpness
                   config[23] = int(denoise)
                   with open(config_file, 'w') as f:
                       for item in config:
                           f.write("%s\n" % item)
                   time.sleep(1)
                   text(1,12,2,1,1,"Config",fv,7)
                else: 
                   os.killpg(p.pid, signal.SIGTERM)
                   pygame.display.quit()
                   sys.exit()
              
    if restart > 0 and buttonx[0] == 0:
        os.killpg(p.pid, signal.SIGTERM)
        time.sleep(0.25)
        text(0,0,6,2,1,"Waiting for preview ...",int(fv*1.7),1)
        preview()
        
    #check for any mouse button presses
    for event in pygame.event.get():
        if event.type == QUIT:
            os.killpg(p.pid, signal.SIGTERM)
            pygame.quit()
        elif (event.type == MOUSEBUTTONUP):
            #restart = 0
            mousex, mousey = event.pos
            if mousex < preview_width and zoom == 0:
                zx = mousex
                zy = mousey
            if mousex > preview_width:
                button_column = int((mousex-preview_width)/bw) + 1
                button_row = int((mousey)/bh) + 1
                y = button_row-1
                if button_column == 1:    
                    if button_row == 1:
                        # take still
                        os.killpg(p.pid, signal.SIGTERM)
                        button(0,0,1,4)
                        text(0,0,2,0,1,"CAPTURE",ft,0)
                        text(1,0,0,0,1,"CAPTURE",ft,7)
                        text(1,0,0,1,1,"Video",ft,7)
                        text(1,6,0,0,1,"CAPTURE",ft,7)
                        text(1,6,0,1,1,"Timelapse",ft,7)
                        text(0,0,6,2,1,"Please Wait, taking still ...",int(fv*1.7),1)
                        now = datetime.datetime.now()
                        timestamp = now.strftime("%y%m%d%H%M%S")
                        if extns[extn] != 'raw':
                            fname =  pic_dir + str(timestamp) + '.' + extns2[extn]
                            rpistr = "libcamera-still -e " + extns[extn] + " -n -t 5000 -o " + fname
                        else:
                            fname =  pic_dir + str(timestamp) + '.' + extns2[extn]
                            rpistr = "libcamera-still -r -n -t 5000 -o " + fname
                            if preview_width == 640 and preview_height == 480 and zoom == 10:
                                rpistr += " --rawfull"
                        rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
                        if zoom > 0:
                            rpistr += " --width " + str(preview_width) + " --height " + str(preview_height)
                        if extns[extn] == "jpg" and preview_width == 640 and preview_height == 480 and zoom == 10:
                            rpistr += " -r --rawfull"
                        if mode == 0:
                            rpistr += " --shutter " + str(sspeed)
                        else:
                            rpistr += " --exposure " + str(modes[mode])
                        if ev != 0:
                            rpistr += " --ev " + str(ev)
                        if sspeed > 5000000 and mode == 0:
                            rpistr += " --gain 1 --awbgain 1,1 --immediate "
                        else:    
                            rpistr += " --gain " + str(gain)
                            if awb == 0:
                                rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
                            else:
                                rpistr += " --awb " + awbs[awb]
                        rpistr += " --metering " + meters[meter]
                        rpistr += " --saturation " + str(saturation/10)
                        rpistr += " --sharpness " + str(sharpness)
                        rpistr += " --denoise "    + denoises[denoise]
                        if Pi_Cam == 4:
                            rpistr += " --autofocus "
                        if zoom > 0 and zoom < 10:
                            zwidth = preview_width * (5-zoom)
                            if zwidth > igw:
                                zwidth = igw - int(igw/20) 
                            zheight = preview_height * (5-zoom)
                            if zheight > igh:
                                zheight = igh - int(igh/20)
                            zxo = ((igw-zwidth)/2)/igw
                            zyo = ((igh-zheight)/2)/igh
                            rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(zwidth/igw) + "," + str(zheight/igh)
                        if zoom == 10:
                            zxo = ((zx -((preview_width/2) / (igw/preview_width)))/preview_width)
                            zyo = ((zy -((preview_height/2) / (igh/preview_height)))/preview_height)
                            rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
                        #print (rpistr)
                        os.system(rpistr)

                        while not os.path.exists(fname):
                            pass
                        if extns2[extn] == 'jpg' or extns2[extn] == 'bmp' or extns2[extn] == 'png':
                            image = pygame.image.load(fname)
                            catSurfacesmall = pygame.transform.scale(image, (preview_width,preview_height))
                            windowSurfaceObj.blit(catSurfacesmall, (0, 0))
                        text(0,0,6,2,1,fname,int(fv*1.5),1)
                        pygame.display.update()
                        time.sleep(2)
                        button(0,0,0,4)
                        text(0,0,1,0,1,"CAPTURE",ft,7)
                        text(1,0,1,0,1,"CAPTURE",ft,7)
                        text(1,0,1,1,1,"Video",ft,7)
                        text(0,0,1,1,1,"Still",ft,7)
                        text(1,6,1,0,1,"CAPTURE",ft,7)
                        text(1,6,1,1,1,"Timelapse",ft,7)
                        restart = 2
 
                if button_column == 2:                       
                    if button_row == 1:
                        # take video
                        os.killpg(p.pid, signal.SIGTERM)
                        button(1,0,1,3)
                        text(1,0,3,0,1,"STOP ",ft,0)
                        text(1,0,3,1,1,"Record",ft,0)
                        text(0,0,0,0,1,"CAPTURE",ft,7)
                        text(0,0,0,1,1,"Still",ft,7)
                        text(1,6,0,0,1,"CAPTURE",ft,7)
                        text(1,6,0,1,1,"Timelapse",ft,7)
                        text(0,0,6,2,1,"Please Wait, taking video ...",int(fv*1.7),1)
                        now = datetime.datetime.now()
                        timestamp = now.strftime("%y%m%d%H%M%S")
                        vname =  vid_dir + str(timestamp) + "." + codecs2[codec]
                        rpistr = "libcamera-vid -t " + str(vlen * 1000) + " -o " + vname + " --framerate " + str(fps)
                        if codecs[codec] != 'h264':
                            rpistr += " --codec " + codecs[codec]
                        rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
                        if zoom > 0:
                            rpistr += " --width " + str(preview_width) + " --height " + str(preview_height)
                        else:
                            rpistr += " --width " + str(vwidth) + " --height " + str(vheight)
                        if mode == 0:
                            rpistr += " --shutter " + str(sspeed)
                        else:
                            rpistr += " --exposure " + modes[mode]
                        rpistr += " --gain " + str(gain)
                        if ev != 0:
                            rpistr += " --ev " + str(ev)
                        if awb == 0:
                            rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
                        else:
                            rpistr += " --awb " + awbs[awb]
                        rpistr += " --metering " + meters[meter]
                        rpistr += " --saturation " + str(saturation/10)
                        rpistr += " --sharpness " + str(sharpness)
                        rpistr += " --denoise "    + denoises[denoise]
                        if Pi_Cam == 4:
                            rpistr += " --autofocus "
                        rpistr += " -p 0,0," + str(preview_width) + "," + str(preview_height)
                   
                        if zoom > 0 and zoom < 10:
                            zwidth = preview_width * (5-zoom)
                            if zwidth > igw:
                                zwidth = igw - int(igw/20) 
                            zheight = preview_height * (5-zoom)
                            if zheight > igh:
                                zheight = igh - int(igh/20)
                            zxo = ((igw-zwidth)/2)/igw
                            zyo = ((igh-zheight)/2)/igh
                            rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(zwidth/igw) + "," + str(zheight/igh)
                        if zoom == 10:
                            zxo = ((zx -((preview_width/2) / (igw/preview_width)))/preview_width)
                            zyo = ((zy -((preview_height/2) / (igh/preview_height)))/preview_height)
                            rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
                        p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
                        #os.system(rpistr)
                        #print (rpistr)
                        start_video = time.monotonic()
                        stop = 0
                        while time.monotonic() - start_video < vlen and stop == 0:
                            for event in pygame.event.get():
                                if (event.type == MOUSEBUTTONUP):
                                    mousex, mousey = event.pos
                                    # stop video recording
                                    button_column = int((mousex-preview_width)/bw) + 1
                                    button_row = int((mousey)/bh) + 1
                                    if button_column == 2 and button_row == 1:
                                       os.killpg(p.pid, signal.SIGTERM)
                                       stop = 1
                        #print (rpistr)
                        text(0,0,6,2,1,vname,int(fv*1.5),1)
                        time.sleep(1)
                        button(1,0,0,3)
                        text(0,0,1,0,1,"CAPTURE",ft,7)
                        text(0,0,1,1,1,"Still",ft,7)
                        text(1,0,1,0,1,"CAPTURE",ft,7)
                        text(1,0,1,1,1,"Video",ft,7)
                        text(1,6,1,0,1,"CAPTURE",ft,7)
                        text(1,6,1,1,1,"Timelapse",ft,7)
                        restart = 2
                   
                    elif button_row == 7:
                        # take timelapse
                        os.killpg(p.pid, signal.SIGTERM)
                        button(1,6,1,2)
                        text(1,6,3,0,1,"STOP",ft,0)
                        text(1,6,3,1,1,"Timelapse",ft,0)
                        text(0,0,0,0,1,"CAPTURE",ft,7)
                        text(1,0,0,0,1,"CAPTURE",ft,7)
                        text(1,0,0,1,1,"Video",ft,7)
                        text(0,0,0,1,1,"Still",ft,7)
                        tcount = 0
                        if tinterval < 20 and tinterval > 0:
                            text(1,6,3,0,1,"STOP",ft,0)
                            text(1,6,3,1,1,"Timelapse",ft,0)
                            text(0,0,6,2,1,"Please Wait, taking Timelapse ...",int(fv*1.7),1)
                            now = datetime.datetime.now()
                            timestamp = now.strftime("%y%m%d%H%M%S")
                            if extns[extn] != 'raw':
                                rpistr = "libcamera-still -e " + extns[extn] + " -n -t " + str((tduration+1) * 1000) + " --timelapse " + str(tinterval * 1000) + " -o /home/pi/Pictures/" + timestamp + "_%04d." + extns2[extn]
                            else:
                                rpistr = "libcamera-still -r -n -t " + str(tduration * 1000) + " --timelapse " + str(tinterval * 1000) + " -o /home/pi/Pictures/" + timestamp + "_%04d.jpg" 
                                if preview_width == 640 and preview_height == 480 and zoom == 10:
                                    rpistr += " --rawfull"
                            rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
                            if extns[extn] == "jpg" and preview_width == 640 and preview_height == 480 and zoom == 10:
                                rpistr += " -r --rawfull"
                            if zoom > 0:
                                rpistr += " --width " + str(preview_width) + " --height " + str(preview_height) 
                            if mode == 0:
                                rpistr += " --shutter " + str(sspeed)
                            else:
                                rpistr += " --exposure " + modes[mode]
                            if ev != 0:
                                rpistr += " --ev " + str(ev)
                            if sspeed > 5000000 and mode == 0:
                                rpistr += " --gain 1 --awbgain 1,1 --immediate"
                            else:
                                rpistr += " --gain " + str(gain)
                                if awb == 0:
                                    rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
                                else:
                                    rpistr += " --awb " + awbs[awb]
                            rpistr += " --metering " + meters[meter]
                            rpistr += " --saturation " + str(saturation/10)
                            rpistr += " --sharpness " + str(sharpness)
                            rpistr += " --denoise "    + denoises[denoise]
                            if Pi_Cam == 4:
                                 rpistr += " --autofocus "
                            if zoom > 0 and zoom < 10:
                                zwidth = preview_width * (5-zoom)
                                if zwidth > igw:
                                    zwidth = igw - int(igw/20) 
                                zheight = preview_height * (5-zoom)
                                if zheight > igh:
                                    zheight = igh - int(igh/20)
                                zxo = ((igw-zwidth)/2)/igw
                                zyo = ((igh-zheight)/2)/igh
                                rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(zwidth/igw) + "," + str(zheight/igh)
                            if zoom == 10:
                                zxo = ((zx -((preview_width/2) / (igw/preview_width)))/preview_width)
                                zyo = ((zy -((preview_height/2) / (igh/preview_height)))/preview_height)
                                rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
                            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
                            #print (rpistr)
                            start_timelapse = time.monotonic()
                            stop = 0
                            while time.monotonic() - start_timelapse < tduration+1 and stop == 0:
                                for event in pygame.event.get():
                                    if (event.type == MOUSEBUTTONUP):
                                        mousex, mousey = event.pos
                                        # stop timelapse
                                        button_column = int((mousex-preview_width)/bw) + 1
                                        button_row = int((mousey)/bh) + 1
                                        if button_column == 2 and button_row == 7:
                                            os.killpg(p.pid, signal.SIGTERM)
                                            stop = 1
                      
                        elif tinterval > 19:
                            text(1,6,3,0,1,"STOP",ft,0)
                            text(1,6,3,1,1,"Timelapse",ft,0)
                            stop = 0
                            while tcount < tshots and stop == 0:
                                tstart = time.monotonic()
                                text(0,0,6,2,1,"Please Wait, taking Timelapse ...",int(fv*1.7),1)
                                now = datetime.datetime.now()
                                timestamp = now.strftime("%y%m%d%H%M%S")
                                if extns[extn] != 'raw':
                                    fname =  pic_dir + str(timestamp) + '_' + str(tcount) + '.' + extns2[extn]
                                    rpistr = "libcamera-still -e " + extns[extn] + " -n -t 1000 -o " + fname
                                else:
                                    fname =  pic_dir + str(timestamp) + '_' + str(tcount) + '.' + extns2[extn]
                                    rpistr = "libcamera-still -r -n -t 1000 -o " + fname
                                    if preview_width == 640 and preview_height == 480 and zoom == 10:
                                        rpistr += " --rawfull"
                                rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
                                if extns[extn] == "jpg" and preview_width == 640 and preview_height == 480 and zoom == 10:
                                    rpistr += " -r --rawfull"
                                if zoom > 0:
                                    rpistr += " --width " + str(preview_width) + " --height " + str(preview_height) 
                                if mode == 0:
                                    rpistr += " --shutter " + str(sspeed)
                                else:
                                    rpistr += " --exposure " + modes[mode]
                                if ev != 0:
                                    rpistr += " --ev " + str(ev)
                                if sspeed > 5000000 and mode == 0:
                                    rpistr += " --gain 1 --awbgain 1,1 --immediate"
                                else:
                                    rpistr += " --gain " + str(gain)
                                    if awb == 0:
                                        rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
                                    else:
                                        rpistr += " --awb " + awbs[awb]
                                rpistr += " --metering " + meters[meter]
                                rpistr += " --saturation " + str(saturation/10)
                                rpistr += " --sharpness " + str(sharpness)
                                rpistr += " --denoise "    + denoises[denoise]
                                if Pi_Cam == 4:
                                    rpistr += " --autofocus "
                                if zoom > 0 and zoom < 10:
                                    zwidth = preview_width * (5-zoom)
                                    if zwidth > igw:
                                        zwidth = igw - int(igw/20) 
                                    zheight = preview_height * (5-zoom)
                                    if zheight > igh:
                                        zheight = igh - int(igh/20)
                                    zxo = ((igw-zwidth)/2)/igw
                                    zyo = ((igh-zheight)/2)/igh
                                    rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(zwidth/igw) + "," + str(zheight/igh)
                                if zoom == 10:
                                    zxo = ((zx -((preview_width/2) / (igw/preview_width)))/preview_width)
                                    zyo = ((zy -((preview_height/2) / (igh/preview_height)))/preview_height)
                                    rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
                                p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
                                #print (rpistr)
                                start_timelapse = time.monotonic()
                                stop = 0
                                while time.monotonic() - start_timelapse < tduration+1 and stop == 0:
                                    for event in pygame.event.get():
                                        if (event.type == MOUSEBUTTONUP):
                                            mousex, mousey = event.pos
                                            # stop timelapse
                                            button_column = int((mousex-preview_width)/bw) + 1
                                            button_row = int((mousey)/bh) + 1
                                            #print (button_column,button_row)
                                            if button_column == 2 and button_row == 7:
                                                os.killpg(p.pid, signal.SIGTERM)
                                                stop = 1
                                while not os.path.exists(fname):
                                    pass
                                if extns2[extn] == 'jpg' or extns2[extn] == 'bmp' or extns2[extn] == 'png':
                                    image = pygame.image.load(fname)
                                    catSurfacesmall = pygame.transform.scale(image, (preview_width,preview_height))
                                    windowSurfaceObj.blit(catSurfacesmall, (0, 0))
                                text(0,0,6,2,1,fname,int(fv*1.5),1)
                                pygame.display.update()
                                tcount +=1
                                while time.monotonic() - tstart < tinterval and tcount < tshots:
                                    for event in pygame.event.get():
                                        if (event.type == MOUSEBUTTONUP):
                                           mousex, mousey = event.pos
                                           if mousex > preview_width:
                                               button_column = int((mousex-preview_width)/bw) + 1
                                               button_row = int((mousey)/bh) + 1
                                               #print (button_column,button_row)
                                               if button_column == 2 and button_row == 7:
                                                    tcount = tshots

                        else:
                            if tduration == 0:
                                tduration = 1
                            text(0,0,6,2,1,"Please Wait, taking Timelapse ...",int(fv*1.7),1)
                            now = datetime.datetime.now()
                            timestamp = now.strftime("%y%m%d%H%M%S")
                            rpistr = "libcamera-vid -n --codec mjpeg -t " + str(tduration*1000) + " --segment 1 -o /home/pi/Pictures/" + timestamp + "_%04d.jpg "
                            if vwidth == 640 and vheight == 480:
                                rpistr += " --width 720 --height 540 "
                            else:
                                rpistr += " --width " + str(vwidth) + " --height " + str(vheight)
                            rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
                            if mode == 0:
                                rpistr += " --shutter " + str(sspeed) + " --framerate " + str(1000000/sspeed)
                            else:
                                rpistr += " --exposure " + str(modes[mode]) + " --framerate " + str(fps)
                            if ev != 0:
                                rpistr += " --ev " + str(ev)
                            if sspeed > 5000000 and mode == 0:
                                rpistr += " --gain 1 --awbgain 1,1 --immediate"
                            else:
                                rpistr += " --gain " + str(gain)
                                if awb == 0:
                                    rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
                                else:
                                    rpistr += " --awb " + awbs[awb]
                            rpistr += " --metering "   + meters[meter]
                            rpistr += " --saturation " + str(saturation/10)
                            rpistr += " --sharpness "  + str(sharpness)
                            rpistr += " --denoise "    + denoises[denoise]
                            if Pi_Cam == 4:
                                rpistr += " --autofocus "
                            if zoom > 0 and zoom < 10:
                                zwidth = preview_width * (5-zoom)
                                if zwidth > igw:
                                    zwidth = igw - int(igw/20) 
                                zheight = preview_height * (5-zoom)
                                if zheight > igh:
                                    zheight = igh - int(igh/20)
                                zxo = ((igw-zwidth)/2)/igw
                                zyo = ((igh-zheight)/2)/igh
                                rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(zwidth/igw) + "," + str(zheight/igh)
                            if zoom == 10:
                                zxo = ((zx -((preview_width/2) / (igw/preview_width)))/preview_width)
                                zyo = ((zy -((preview_height/2) / (igh/preview_height)))/preview_height)
                                rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
                            #print (rpistr)
                            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
                            #print (rpistr)
                            start_timelapse = time.monotonic()
                            stop = 0
                            while time.monotonic() - start_timelapse < tduration+1 and stop == 0:
                                for event in pygame.event.get():
                                    if (event.type == MOUSEBUTTONUP):
                                        mousex, mousey = event.pos
                                        # stop timelapse
                                        button_column = int((mousex-preview_width)/bw) + 1
                                        button_row = int((mousey)/bh) + 1
                                        #print (button_column,button_row)
                                        if button_column == 2 and button_row == 7:
                                            os.killpg(p.pid, signal.SIGTERM)
                                            stop = 1
                        button(1,6,0,2)
                        text(0,0,1,0,1,"CAPTURE",ft,7)
                        text(1,0,1,0,1,"CAPTURE",ft,7)
                        text(1,0,1,1,1,"Video",ft,7)
                        text(0,0,1,1,1,"Still",ft,7)
                        text(1,6,1,0,1,"CAPTURE",ft,7)
                        text(1,6,1,1,1,"Timelapse",ft,7)
                        restart = 2
        if restart > 0:
            ##print (rpistr)
            poll = p.poll()
            if poll == None:
                os.killpg(p.pid, signal.SIGTERM)
            text(0,0,6,2,1,"Waiting for preview ...",int(fv*1.7),1)
            preview()






                      

