import telebot
from telebot import types
from urllib.request import urlopen, URLError
from cleansys_api import CleansysAPI
from threading import Timer
from datetime import datetime, timedelta
import requests

class User:
  def __init__(self, cid):
    self.cid = cid
    self.api = None
    self.api_token = None
    self.schedule_print_interval = None
    self.reminder_interval = None

  def set_api(self, api_url):
    self.api = CleansysAPI(api_url)

  def set_api_token(self, api_token):
    self.api_token = api_token

  def set_schedule_print_interval(self, schedule_print_interval_in_days, cb):

    self.schedule_print_interval = Timer()

  def set_reminder(self, days_before, expiration_date):

    self.reminder_interval = Timer()


class CleansysTelegramBot:
  def __init__(self, token):
    self.bot = telebot.TeleBot(token)
    self.users = {}

    self.register_handlers()

  # Need to register functions in a class function to access self for decorator. python ney?
  def register_handlers(self):
    @self.bot.message_handler(commands=['start'])
    def _start(m):
      self.start(m)

    @self.bot.message_handler(commands=['schedule'])
    def _getSchedule(m):
      self.getSchedule(m)

    @self.bot.message_handler(commands=['settings'])
    def _settings(m):
      self.settings(m)

    @self.bot.message_handler(commands=['cleaned'])
    def _cleaned(m):
      self.cleaned(m)

    @self.bot.message_handler(commands=['help'])
    def _help(m):
      self.help(m)

  def start_bot(self):
    self.bot.polling()

  def start(self, m):
    cid = m.chat.id

    self.bot.send_message(cid, """Hey there,\n\
This is a bot for controlling CleanSys.\n\
CleanSys is an open source cleaning schedule management system available at\n\
https://github.com/monoclecat/cleansys
""")
    self.users[cid] = User(cid)

    msg = self.bot.reply_to(m, "To start please give me a link to your API (https://example.com/api):")
    self.bot.register_next_step_handler(msg, self.reply_start)

  def reply_start(self, m):

    self.reply_api_url(m)

    self.bot.send_message(m.chat.id, "To checkout cleanings provide an API Token found in the admin section of CleanSys to the bot via /settings.")

  def reply_api_url(self, m):
    api_url = m.text
    user = self.getUser(m)

    if not user:
      return

    try:
      urlopen(api_url)
    except ValueError:
      msg = self.bot.reply_to(m, "This is no valid URL. Try again!")
      self.bot.register_next_step_handler(msg, self.reply_api_url)
      return
    except URLError:
      msg = self.bot.reply_to(m, "The API seems down from here. Try again!")
      self.bot.register_next_step_handler(msg, self.reply_api_url)
      return

    user.set_api(api_url)
    self.bot.send_message(m.chat.id, "Set API Location to " + api_url)

  def reply_api_token(self, m):
    api_token = m.text
    user = self.getUser(m)

    if not user:
      return

    user.set_api_token(api_token)

    self.bot.send_message(m.chat.id, "Set API Token to " + api_token)

  def settings(self, m):
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    keyboard.add(types.InlineKeyboardButton("Set API Url"))
    keyboard.add(types.InlineKeyboardButton("Set API Token"))
    keyboard.add(types.InlineKeyboardButton("Set Schedule Print Interval"))
    keyboard.add(types.InlineKeyboardButton("Set Reminder"))

    msg = self.bot.reply_to(m, "Settings", reply_markup=keyboard)
    self.bot.register_next_step_handler(msg, self.settings_choice)

  def settings_choice(self, m):
    reply = m.text
    if reply == "Set API Url":
      self.settings_url(m)
    elif reply == "Set API Token":
      self.settings_token(m)
    elif reply == "Set Schedule Print Interval":
      self.settings_print_interval(m)
    elif reply == "Set Reminder":
      self.settings_reminder(m)
    else:
      self.bot.reply_to(m, "Sorry, I did not understand that!")

  def settings_url(self, m):
    msg = self.bot.reply_to(m, "Please provide an API url!")
    self.bot.register_next_step_handler(msg, self.reply_api_url)

  def settings_token(self, m):
    msg = self.bot.reply_to(m, "Please provide an API Token found in the admin section!")
    self.bot.register_next_step_handler(msg, self.reply_api_token)

  def settings_reminder(self, m):
    pass

  def settings_print_interval(self, m):
    pass

  def cleaned(self, m):
    user = self.getUser(m)

    if not user.api_token:
      self.bot.reply_to(m, "You must first provide an API Token via /settings before accessing this functionality!")
      return

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    locations = user.api.getLocations()
    if not locations:
      self.bot.reply_to(m, "Seems that there is no schedule this week! You've cleaned for no reason ;-)")
      return

    for location in locations:
      markup.add(types.InlineKeyboardButton(location))

    msg = self.bot.reply_to(m, "What have you cleaned?", reply_markup=markup)
    self.bot.register_next_step_handler(msg, self.location_cleaned)

  def location_cleaned(self, m):
    user = self.getUser(m)
    location = m.text
    try:
      user.api.checkOutAssignmentForLocation(location, user.api_token)
    except LookupError:
      self.bot.reply_to(m, "Could not find this schedule, sorry!")
      return
    except requests.RequestException:
      self.bot.reply_to(m, "There was a problem accessing the resource. Have you set the right token?")
      return

    self.bot.reply_to(m, location + " was cleaned! Good Job!")

  def getSchedule(self, m):
    cid = m.chat.id
    user = self.getUser(m)

    if not user:
      return

    schedule = user.api.getCurrentSchedule()
    if not schedule:
      self.bot.send_message(cid, "Nothing to clean! :-)")
      return

    schedule_message = "\n".join(map(str, [name + ": " + appointment for name, appointment in schedule.items()]))

    self.bot.send_message(cid, schedule_message)


  def help(self, m):
    self.bot.send_message(m.chat.id, """Available commands:\n\
/help Print this help\n\
/start Start the bot\n\
/schedule Print out the current weeks schedule
/settings Configure the bot
    """)
    pass


  def getUser(self, m):
    cid = m.chat.id
    user = None
    try:
      user = self.users[cid]
    except KeyError:
      self.bot.send_message(cid, "Sorry, I do not know you yet :-( \n Type /start to begin chatting with me")
      return

    return user

