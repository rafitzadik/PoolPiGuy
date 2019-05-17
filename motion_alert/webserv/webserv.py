#move to the correct virtualenv
activate_this_file = "/home/pi/.virtualenvs/webserv/bin/activate_this.py"
exec(open(activate_this_file).read(), {'__file__': activate_this_file})

from flask import Flask, render_template, send_file, make_response
from pathlib import Path
import glob
import os
import datetime

app = Flask(__name__)

@app.route("/")
def home():
    water_running_filename = '/home/pi/poolpi/water_level/water_running_runs'
    water_level_filename = '/home/pi/poolpi/water_level/status.txt'
    water_running_file = Path(water_running_filename)
    water_level_file = open(water_level_filename, "r")
    water_running = "Faucet Running" if water_running_file.exists() else "Faucet Off"
    water_level = water_level_file.readline()
    
    water_status_str = "Water Status: {}, {}".format(water_level, water_running)
    response = make_response(render_template("home.html", water_status = water_status_str))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

#not used in new template
@app.route("/curpic")
def curpic():
    response = make_response(render_template("curpic.html"))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

#not used in new template
@app.route("/lastdet")
def lastdet():
    response = make_response(render_template("lastdet.html"))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

def getDets():
    detFiles = glob.glob('/home/pi/poolpi/output/*.jpg')
    dets = []
    for file in detFiles:
        filename = os.path.basename(file)
        if (filename != 'cur_img.jpg') and (filename != 'cur_tmp.jpg') and (filename != 'last_det.jpg'):
            time = datetime.datetime.fromtimestamp(os.path.getmtime(file))
            rounded_time = datetime.datetime(time.year, time.month, time.day, time.hour, time.minute, time.second)
            title = rounded_time.strftime("%m/%d/%Y %H:%M:%S") + ' - ' + filename.split('-', 1)[0]
            link = "browsepic/"+filename
            dets.append((link, title, time, filename))
    dets.sort(key= lambda det: det[2], reverse=True)
    return dets

@app.route("/listdet")
def listdet():
    dets = getDets()
    response = make_response(render_template("listdet.html", detections = dets))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

@app.route("/browsepic/<filename>")
def browsepic(filename):
    if (len(filename) < 3) or (len(filename) > 80) or ('/' in filename) or ('\\' in filename):
        return "Badly formatted filename"
    dets = getDets()
    for i in range(len(dets)):
        if (dets[i][3] == filename):
            break
    if (len(dets) == 0) or (i >= len(dets)):
        return make_response("Error, navigate back")
        
    cur = dets[i][3]
    title = dets[i][1]
    time = dets[i][2]
    if (i > 0):
        next = dets[i-1][3]
    else:
        next = dets[i][3]
    if (i < len(dets)-1):
        prev = dets[i+1][3]
    else:
        prev = dets[i][3]
    response = make_response(render_template("browsepic.html", prev=prev, next=next, cur=cur, title=title, time=time))
    return response
    
@app.route("/pic/<filename>")
def pic(filename):
    if (len(filename) < 3) or (len(filename) > 80) or ('/' in filename) or ('\\' in filename):
        return "Badly formatted filename"
    response = make_response(send_file(os.path.join('/home/pi/poolpi/output', filename), mimetype='image/gif'))
    if (filename == "cur_img.jpg") or (filename == "last_det.jpg"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
    return response

@app.route("/waterstartstop")
def waterstartstop():
    water_running_filename = '/home/pi/poolpi/water_level/water_running_runs'
    water_running_file = Path(water_running_filename)
    if (water_running_file.exists()):
        os.remove(water_running_filename)
        return make_response("Stopped Water")
    else:
        os.system('python3 /home/pi/poolpi/water_level/run_water.py &')
        return make_response("Started Water")

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=10000,debug=False)
