import requests
import json
import calendar
import datetime

class CleansysAPI:
  def __init__(self, api_uri):
    self.api_uri = api_uri

  def getCurrentSchedule(self):
    cleaningWeeks = self.getCleaningWeeksForWeekNumberUnix(self.__getCurrentUnixWeek__())

    result = {}
    for cleaningWeek in cleaningWeeks:
      assignment_set_uri = cleaningWeek["assignment_set"][0]
      assignment_set = self.__getRequest__(assignment_set_uri)
      schedule = self.__getRequest__(assignment_set["schedule"])
      cleaner = self.__getRequest__(assignment_set["cleaner"])
      result[cleaner["name"]] = schedule["name"]

    return result

  def getCleaners(self, iteration=1):
    response = self.__getApiRequest__("/cleaners/?page=" + str(iteration))
    result = response["results"]

    if response["next"]:
      result += self.getCleaners(iteration + 1)

    return result

  def getCleaningWeeks(self, page=1):
    return self.__getApiRequest__("/cleaningweeks/?page=" + str(page))

  def getCleaningWeeksForWeekNumberUnix(self, weekNumberUnix):
    cleaningWeeks = self.getCleaningWeeks()
    cleaningWeeksWithWeekNumber = []
    page = 1
    while cleaningWeeks["next"]:
      for cleaningWeek in cleaningWeeks["results"]:
        if cleaningWeek["week"] == weekNumberUnix:
          cleaningWeeksWithWeekNumber.append(cleaningWeek)
        elif cleaningWeek["week"] > weekNumberUnix:
          return cleaningWeeksWithWeekNumber
      page += 1
      cleaningWeeks = self.getCleaningWeeks(page)

  def getAssignment(self, assignment_number):
    return self.__getApiRequest__(assignment_number)

  def __getApiRequest__(self, endpoint):
    return self.__getRequest__(self.api_uri + endpoint)

  def __getRequest__(self, request):
    response = None
    try:
      response = requests.get(request).text
    except BaseException:
      print("error")

    return json.loads(response)

  def __getCurrentUnixWeek__(self):
    epoch_seconds = calendar.timegm(datetime.date.today().timetuple())
    return int(((epoch_seconds / 60 / 60 / 24) + 3) / 7)