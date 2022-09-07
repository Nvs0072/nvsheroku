#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0613, C0116
# type: ignore[union-attr]
# This program is dedicated to the public domain under the CC0 license.

from pyrogram import Client, filters, idle
from pyromod import listen
from pyrogram.errors.exceptions.bad_request_400 import MessageEmpty, MessageNotModified, MessageTooLong
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date
import asyncio, json, logging, os
from datetime import date, datetime
from pytz import timezone
import asyncio, requests, psycopg2, json, os, random, time, re, subprocess, logging, sys

import time
import itertools
import heroku3
from requests.exceptions import Timeout, ConnectionError

logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

#BOT_TOKEN = "5092828192:AAH-m1G7hPi1qIVeYJG0w_NNIXVUXcqQX_s"

UPDATES_CHANNEL = -1001605863973
LOG_CHANNEL = "rlakkdksksoowkwksksospsodo983301"
BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "5579576216:AAEf10lnPyRpB_YezXtcJCyAkOlEYhTKpeE")
AUTH_GROUP = [-789282762]
OWNER_ID = [5662337726]

db_bsaec = {
    "apikey": [],
    "all_apikey": [],
    "user": []
    # "user": {}
}
try:
    db_h = open("db.json", "r")
    db_h = json.load(db_h)
except:
    db_h = open("db.json", "w")
    json_object = json.dumps(db_bsaec, indent=4)
    db_h.write(json_object)
    db_h.close()
db_h = open("db.json", "r")
db_h = json.load(db_h)
db_h = open("db.json", "r")
db_h = json.load(db_h)

loop = asyncio.get_event_loop()
app = Client(
                "rxyzbot",
                bot_token="5712914098:AAE9zFqmJB267aLW8vZcsT12Si8y5TaXQMw",
                api_id=3910389,
                api_hash="86f861352f0ab76a251866059a6adbd6"
            )
heroku_conn = None
status = False

def get_configuration(user_id, bot_token):
    git_name = "heroku_live"
    data = {
        "app": {
            "region": "us",
        },
        "source_blob": {
            "url": "https://drive.google.com/uc?id=125Ti8TW7DmWHqGi2r6lbC2_bPdBsiZn5&export=download"
        },
        "overrides": {
            "env": {
                "TG_BOT_TOKEN": bot_token,
                "AUTH_USERS": user_id,
                "WEBHOOK": "ANYTHING"
            }
        },
    }
    return data, git_name

def wait_for_status_event(appsetup_id, time_checkpoint):
    time_check = time.time()
    if (time_check - time_checkpoint) > 5:
        time_checkpoint = time_check
        print("checking status", end="\r")
        appsetup = heroku_conn.get_appsetup(appsetup_id)
        if appsetup.build:
            print("Build Available", appsetup.build)
            return True, time_checkpoint
        if appsetup.status in ["failed", "succeeded"]:
            print(appsetup.status)
            return True, time_checkpoint
    return False, time_checkpoint

def stream_build_logs(appsetup_id):
    appsetup = heroku_conn.get_appsetup(appsetup_id)
    build_iterator = appsetup.build.stream(timeout=5)
    try:
        for line in build_iterator:
            if line:
                print("{0}".format(line.decode("utf-8")))
    except Timeout:
        appsetup = heroku_conn.get_appsetup(appsetup_id)
        if appsetup.build.status == "pending":
            return stream_build_logs(appsetup_id)
        else:
            return
    except ConnectionError:
        appsetup = heroku_conn.get_appsetup(appsetup_id)
        if appsetup.build.status == "pending":
            return stream_build_logs(appsetup_id)
        else:
            return

def stream_app_logs(appsetup_id, app_id):
    apps = heroku_conn.app(app_id)
    iterator = apps.stream_log(timeout=5)
    try:
        for line in iterator:
            if line:
                print("{0}".format(line.decode("utf-8")))
    except ConnectionError:
        appsetup = heroku_conn.get_appsetup(appsetup_id)
        if appsetup.status == "pending":
            return stream_app_logs(appsetup_id, app_id)
        else:
            return

async def createAppAndDeploy(user_id, bot_token, message, client, typ):
    #m = await message.reply_text("please wait...")
    m = await client.send_message(
        chat_id=message.chat.id,
        text="please wait..."
    )
    data, git_name = get_configuration(user_id, bot_token)
    heroku_appsetup = heroku_conn.create_appsetup(**data)
    apps = heroku_conn.app(heroku_appsetup.app.id)
    time_checkpoint = time.time()
    waiting = True
    while True:
        success, time_checkpoint = wait_for_status_event(heroku_appsetup.id, time_checkpoint)
        if success:
            break
    #stream_app_logs(heroku_appsetup.id, heroku_appsetup.app.id)
    #stream_build_logs(heroku_appsetup.id)
    
    stream_build_logs(heroku_appsetup.id)
    stream_app_logs(heroku_appsetup.id, heroku_appsetup.app.id)
    
    appsetup = heroku_conn.get_appsetup(heroku_appsetup.id)
    if appsetup.status == "succeeded":
        await m.edit("enabling heroku labs runtime dyno metrics")
        apps.enable_feature("runtime-dyno-metadata")
        await m.edit("success enabling dyno metrics")
        await asyncio.sleep(5)
        if typ == "create":
            db_h["user"].append({
                "id": user_id,
                "token": bot_token,
                "apikey": db_h["apikey"][0]
            })
            db_h["apikey"].remove(db_h["apikey"][0])
            await m.edit(f"bot is ready to use!\navailable heroku account: {len(db_h['apikey'])}")
        elif typ == "update":
            await m.edit("bot is ready to use!")
    else:
        await m.edit("failed")

def restartBot():
    print("[ INFO ] BOT RESTARTED")
    python = sys.executable
    os.execl(python, python, *sys.argv)

@app.on_message(filters.command(["reboot"]))
async def rebootCmd(client):
    if message.from_user.id in OWNER_ID:
        await message.reply_text("OK!")
        restartBot()

@app.on_message(filters.command(["start"]))
async def startCommand(client, message):
    if message.from_user.id in OWNER_ID:
    #if message.chat.id in AUTH_GROUP:
        await message.reply_text("ok!")

@app.on_message(filters.command("add"))
async def addApikey(client, message):
    if message.from_user.id in OWNER_ID: # [2106139440]:
        n_api = await app.ask(message.chat.id,
                                    f"send heroku apikey for add to database!"
                                )
        if n_api.text in db_h["apikey"]:return
        if n_api.text in db_h["all_apikey"]:return
        db_h["apikey"].append(n_api.text)
        db_h["all_apikey"].append(n_api.text)
        await message.reply_text("done")
        with open(f"db.json", "w") as fp:
            json_object = json.dumps(db_h, indent=4)
            fp.write(json_object)
            fp.close()

@app.on_message(filters.command("del"))
async def deleteApikey(client, message):
    if message.from_user.id in OWNER_ID:
        n_api = await app.ask(message.chat.id,
                                    f"send heroku apikey for del from database!"
                                )
        if n_api.text in db_h["apikey"]:db_h["apikey"].remove(n_api.text)
        if n_api.text in db_h["all_apikey"]:db_h["all_apikey"].remove(n_api.text)
        await message.reply_text("done")
        with open(f"db.json", "w") as fp:
            json_object = json.dumps(db_h, indent=4)
            fp.write(json_object)
            fp.close()

@app.on_message(filters.command("available"))
async def checkAvailable(client, message):
    if message.from_user.id in OWNER_ID:
        await client.send_message(
            chat_id=message.chat.id,
            text=f"available {len(db_h['apikey'])} from {len(db_h['all_apikey'])}"
        )
        #await message.reply_text(f"available {len(db_h['apikey'])} from {len(db_h['all_apikey'])}")

@app.on_message(filters.command("reboot"))
async def restartBot(client, message):
    if message.from_user.id in OWNER_ID:
        restartBot()
                        
@app.on_message(filters.command("new"))
async def createNew(client, message):
  #if message.chat.id in AUTH_GROUP and message.from_user.id in OWNER_ID:
  if message.from_user.id in OWNER_ID:
    global status, heroku_conn
    if status != True and len(db_h["apikey"]) != 0:
      user_id = message.text.split(" ")
      if len(user_id) == 2:
        status = True
        #global heroku_conn
        user_id = message.text.replace("/new ","")
        bot_token = await app.ask(message.chat.id,
                                    f"send bot token for user _{user_id}_"
                                )
        heroku_conn = heroku3.from_key(db_h["apikey"][0])
        await createAppAndDeploy(user_id, bot_token.text, message, client, "create")
        with open(f"db.json", "w") as fp:
            json_object = json.dumps(db_h, indent=4)
            fp.write(json_object)
            fp.close()
        status = False
        return
    elif status == True:
        await client.send_message(
            chat_id=message.chat.id,
            text="another proccess already running, please wait until done!"
        )
        return
        #await message.reply_text("another proccess already running, please wait until done!")
    elif len(db_h["apikey"]) == 0:
        await client.send_message(
            chat_id=message.chat.id,
            text="heroku account isn't available"
        )
        return
        #await message.reply_text("heroku account isn't available")

@app.on_message(filters.command("update"))
async def updateBot(client, message):
    if message.from_user.id in OWNER_ID:
        global status, heroku_conn
        if status != True:
            user_id = message.text.split(" ")
            if len(user_id) == 2:
                status = True
                user_id = message.text.replace("/update ","")
                for x in db_h["user"]:
                    if x["id"] == user_id:
                      try:
                        heroku_conn = heroku3.from_key(x["apikey"])
                        apps = heroku_conn.apps()[0]
                        m = await client.send_message(
                            chat_id=message.chat.id,
                            text="updating bot version..."
                        )
                        apps = heroku_conn.apps()[apps.id]
                        apps.delete()
                        await createAppAndDeploy(user_id, x["token"], message, client, "update")
                        await m.delete()
                      except:
                        pass
                status = False
                return

@app.on_message(filters.command("restart"))
async def restartBot(client, message):
    userr_ids = [int(x["id"]) for x in db_h["user"]]
    if message.from_user.id in OWNER_ID + userr_ids:
        print(userr_ids)
    #if message.from_user.id in OWNER_ID:
        global status, heroku_conn
        if status != True:
            user_id = message.text.split(" ")
            if len(user_id) == 2:
                status = True
                user_id = message.text.replace("/restart ","")
                for x in db_h["user"]:
                  if message.from_user.id == int(x["id"]) or message.from_user.id in OWNER_ID:
                    if x["token"] == user_id:
                        try:
                            m = await client.send_message(
                                chat_id=message.chat.id,
                                text="restarting bot..."
                            )
                            heroku_conn = heroku3.from_key(x["apikey"])
                            apps = heroku_conn.apps()[0]
                            apps = heroku_conn.apps()[apps.id]
                            apps.restart()
                            await m.edit("success restarting...")
                        except:
                            pass
                        #m.delete()
                status = False
                return

async def start_services():
    print('\n')
    print('------------------- Initalizing Telegram Bot -------------------')
    await app.start()
    #if LOG_CHANNEL:
            #await app.join_chat(LOG_CHANNEL)
    print('----------------------------- DONE -----------------------------')
    print('\n')
    await idle()

if __name__ == "__main__":
    try:
        loop.run_until_complete(start_services())
    except KeyboardInterrupt:
        print('----------------------- Service Stopped -----------------------')
