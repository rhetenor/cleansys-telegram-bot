import argparse

from bot import CleansysTelegramBot

def main():
  parser = argparse.ArgumentParser("A TelegramBot for CleanSys")
  parser.add_argument('token', nargs=1)
  args = parser.parse_args()

  bot = CleansysTelegramBot(args.token[0])
  bot.start_bot()

if __name__ == '__main__':
  main()