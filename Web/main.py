import os

from flask import (
    Blueprint,
    Response,
    abort,
    make_response,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import redirect

from . import xml_feed_handler as XFH

from EAS2Text.EAS2Text import EAS2Text

senderkeys = [] # Provide Sender Header Keys here

pins = []  # Provide PINS here.

main = Blueprint("main", __name__)


@main.route("/favicon.ico")
def layout():
    try:
        return send_from_directory(
            directory="static", path="favicon.ico", mimetype="image/x-icon"
        )
    except Exception as E:
        return make_response(f"System Errror: {str(E)}", 500)


@main.route("/", methods=["GET"])
def redToCap():
    try:
        return redirect(url_for("main.CAPSERV"), code=302)
    except Exception as E:
        return make_response(f"System Errror: {str(E)}", 500)


@main.route("/media/<path:filename>", methods=["GET"])
def download(filename):
    try:
        return send_from_directory(os.path.join(os.getcwd(), 'media'), path=filename)
    except Exception as E:
        return make_response(f"System Errror: {str(E)}", 500)


@main.route("/IPAWSOPEN_EAS_SERVICE/rest/eas/<path:filename>", methods=["GET"])
def download2(filename):
    try:
        if request.args.get("pin") != None:
            if request.args.get("pin") in pins:
                with open(f"Web/alerts/{filename}") as f:
                    x = f.read()
                return Response(x, mimetype="application/xml")
            else:
                return make_response("Invalid PIN", 403)
        else:
            return make_response("Required String parameter 'pin' is not present", 400)
    except Exception as E:
        return make_response(f"System Errror: {str(E)}", 500)


@main.route("/IPAWSOPEN_EAS_SERVICE/rest/feed", methods=["GET"])
def IPAWSFEED():
    try:
        if request.args.get("pin") != None:
            if request.args.get("pin") in pins:
                with open("api_feed.xml") as f:
                    x = f.read()
                return Response(x, mimetype="application/xml")
            else:
                return make_response("Invalid PIN", 403)
        else:
            return make_response("Required String parameter 'pin' is not present", 400)
    except Exception as E:
        return make_response(f"System Errror: {str(E)}", 500)


@main.route("/IPAWSOPEN_EAS_SERVICE/rest/update", methods=["GET"])
def IPAWSUPDATE():
    try:
        if request.args.get("pin") != None:
            if request.args.get("pin") in pins:
                with open("api_update.xml") as f:
                    x = f.read()
                    return Response(x, mimetype="application/xml")
            else:
                return make_response("Invalid PIN", 403)
        else:
            return make_response("Required String parameter 'pin' is not present", 400)
    except Exception as E:
        return make_response(f"System Errror: {str(E)}", 500)


@main.route("/IPAWSOPEN_EAS_SERVICE/rest/eas/recent", methods=["GET"])
def RECENTSERV():
    env = request.args.get("env")
    try:
        if request.args.get("pin") != None:
            if request.args.get("pin") in pins:
                with open("CAP/recent.xml", "r") as f:
                    resp = f.read()
                    return Response(resp, mimetype="text/xml")
            else:
                return make_response("Invalid PIN", 403)
        else:
            return make_response("Required String parameter 'pin' is not present", 400)
    except FileNotFoundError:
        return abort(404)
    except Exception as E:
        return make_response(f"System Errror: {str(E)}", 500)
    
@main.route("/IPAWSOPEN_EAS_SERVICE/rest/public/xml", methods=["GET"])
def CAPSERV():
    env = request.args.get("env")
    try:
        if request.args.get("pin") != None:
            if request.args.get("pin") in pins:
                if env == "dev":
                    with open("CAP/dev/alerts.xml", "r") as f:
                        resp = f.read()
                        return Response(resp, mimetype="text/xml")
                else:
                    with open("CAP/alerts.xml", "r") as f:
                        resp = f.read()
                        return Response(resp, mimetype="text/xml")
            else:
                return make_response("Invalid PIN", 403)
        else:
            return make_response("Required String parameter 'pin' is not present", 400)
    except FileNotFoundError:
        return abort(404)
    except Exception as E:
        return make_response(f"System Errror: {str(E)}", 500)


@main.route("/POST/new", methods=["POST"])
def CAPAPI():
    try:
        if request.headers["CogID"] in cogs:
            if request.headers["AuthKey"] in senderkeys:
                event = request.json["event"]

                events = EAS2Text(listMode=True).evntList

                # Create the event_dict with reversed key-value pairs and remove 'a ' or 'an ' from the start
                event_dict = {v.lstrip("a ").lstrip("an "): k for k, v in events.items()}
                
                event_code = event_dict.get(event)
                if event_code == None:
                    event = list(event_dict.keys())[list(event_dict.values()).index(event)]
                    event_code = event_dict.get(event)

                if not event and not event_code:
                    return make_response(
                        f"Event Code is Invalid. Valid event codes are {', '.join(list(event_dict.keys())[:-1])}, and {list(event_dict.keys())[-1:][0]}",
                        422,
                    )
                else:
                    env = request.json["env"]

                    try:
                        if request.json["audio"] == "True":
                            audio_exists = True
                        elif request.json["audio"] == "False":
                            audio_exists = False
                    except KeyError:
                        audio_exists = False

                    try:
                        if request.json["base64"] != None:
                            b64Aud = request.json["base64"]
                        else:
                            b64Aud = None
                    except KeyError:
                        b64Aud = None


                    try:
                        if request.json["description"] != None:
                            description = request.json["description"]
                        else:
                            description = None
                    except:
                        description = None
                    
                    try:
                        if request.json["instruction"] != None:
                            instruction = request.json["instruction"]
                        else:
                            instruction = None
                    except:
                        instruction = None

                    try:
                        if request.json["easorg"] != None:
                            easorg = request.json["easorg"]
                        else:
                            easorg = None
                    except:
                        easorg = None

                    try:
                        if request.json["stnid"] != None:
                            if len(request.json["stnid"]) > 8:
                                stnid = request.json["stnid"][:8]
                            else:
                                stnid = request.json["stnid"]
                        else:
                            stnid = "None"
                    except:
                        stnid = None

                    area = request.json["area"]
                    duration = request.json["duration"]

                    try:
                        if request.json["zczc"] != None:
                            zczc = request.json["zczc"]
                        else:
                            zczc = "None"
                    except:
                        zczc = None

                    try:
                        if request.json["startTime"] != None:
                            startTime = request.json["startTime"]
                        else:
                            startTime = "None"
                    except:
                        startTime = None

                    try:
                        if request.json["endTime"] != None:
                            endTime = request.json["endTime"]
                        else:
                            endTime = "None"
                    except:
                        endTime = None    

                    if "dev" in env and not "live" in env:
                        XFH.createCAPAlert(
                            event,
                            area,
                            description,
                            instruction,
                            # duration,
                            stnid,
                            easorg,
                            duration=duration,
                            zczc=zczc,
                            startTime=startTime,
                            endTime=endTime,
                            audio=audio_exists,
                            dev=True,
                            base64=b64Aud,
                        )
                    else:
                        XFH.createCAPAlert(
                            event,
                            area,
                            description,
                            instruction,
                            # duration,
                            stnid,
                            easorg,
                            duration=duration,
                            zczc=zczc,
                            startTime=startTime,
                            endTime=endTime,
                            audio=audio_exists,
                            dev=False,
                            base64=b64Aud,
                        )

                    if "live" in env and not "dev" in env:
                        with open("api.xml", "r") as f:
                            resp = f.read()
                            os.system("cp api.xml CAP/alerts.xml")
                            return Response(resp, mimetype="text/xml")
                    elif "live" in env and "dev" in env:
                        with open("api.xml", "r") as f:
                            resp = f.read()
                            os.system("cp api.xml CAP/alerts.xml")
                            os.system("cp api.xml CAP/dev/alerts.xml")
                            return Response(resp, mimetype="text/xml")
                    elif "live" not in env and "dev" in env:
                        with open("api.xml", "r") as f:
                            resp = f.read()
                            os.system("cp api.xml CAP/dev/alerts.xml")
                            return Response(resp, mimetype="text/xml")
                    else:
                        return make_response(
                            "Environment not specified, please use 'live', 'dev', or both.",
                            400,
                        )
            else:
                return make_response("Invalid KEY", 403)
        else:
            return make_response("Invalid KEY", 403)
    except Exception as E:
        return make_response(f"System Errror: {str(E)}", 500)
