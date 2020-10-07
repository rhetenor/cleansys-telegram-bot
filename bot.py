import telebot
from telebot import TeleBot
from urllib.request import urlopen, URLError
from cleansys_api import CleansysAPI

class User:
  def __init__(self, cid):
    self.cid = cid
    self.api = None

  def set_api(self, api_url):
    self.api = CleansysAPI(api_url)


class CleansysTelegramBot:
  def __init__(self, token):
    self.bot = telebot.TeleBot(token)
    self.users = {}

    self.register_handlers()

  # Need to register functions in a class function to access self for decorator
  def register_handlers(self):
    @self.bot.message_handler(commands=['start'])
    def _start(m):
      self.start(m)

    @self.bot.message_handler(commands=['schedule'])
    def _getSchedule(m):
      self.getSchedule(m)

    @self.bot.message_handler(commands=['help'])
    def _help(m):
      self.getSchedule(m)

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

    msg = self.bot.reply_to(m, "To start please give me a link to your API:")
    self.bot.register_next_step_handler(msg, self.reply_start)

  def reply_start(self, m):
    api_url = m.text
    user = self.getUser(m)

    try:
      urlopen(api_url)
    except ValueError:
      msg = self.bot.reply_to(m, "This is no valid URL. Try again!")
      self.bot.register_next_step_handler(msg, self.reply_start)
      return
    except URLError:
      msg = self.bot.reply_to(m, "The API seems down from here. Try again!")
      self.bot.register_next_step_handler(msg, self.reply_start)
      return

    self.bot.send_message(m.chat.id, "Set API Location to " + api_url)
    user.set_api(api_url)

  def getSchedule(self, m):
    cid = m.chat.id
    user = self.getUser(m)

    if not user:
      return

    schedule = user.api.getCurrentSchedule()
    schedule_message = "\n".join(map(str, [name + ": " + appointment for name, appointment in schedule.items()]))

    self.bot.send_message(cid, schedule_message)


  def help(self, m):
    self.bot.send_message(m.chat.id, """Available commands:\n\
/help Print this help\n\
/start Start the bot\n\
/schedule Print out the current weeks schedule
    """)
    pass


  def getUser(self, m):
    cid = m.chat.id
    user = self.users[cid]

    if not user:
      self.bot.send_message(cid, "Sorry, I do not know you :-( \n Type /start to begin chatting with me")

    return user

