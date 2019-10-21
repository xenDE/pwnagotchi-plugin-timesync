__author__ = 'https://github.com/xenDE/pwnagotchi-plugin-timesync'
__version__ = '1.0.0-alpha'
__name__ = 'timesync'
__license__ = 'GPL3'
__description__ = 'calculates an offset after the time of the rasperry pi has been syncronized and can then correct times before the time of the syncronization'


import logging
import os
import json
import hashlib
import time


class RaspiTimeSync:
    """
    Helpe Class for syncing timestamps
    """
    # es sollte nur eine instnz dieser klasse existieren dürfen

    # if time is synced, the time DictObj is shorter: {"ts": 0, "synced" 1}
    time = {"ts": 0, "synced": 0, "boot_uuid": "", "boot_uptime": 0, "boot_ts": 0, "sync": {"offset": 0, "uptime": 0}}
    _is_synced = 0

    def __init__(self):
        try:
          with open("/var/lib/systemd/random-seed","rb") as f:
            random_seed_data = f.read()
          f.close() 
          self.time["boot_uuid"] = hashlib.md5(random_seed_data).hexdigest();
        except Exception as error:
          print("error on reading /var/lib/systemd/random-seed: ", error)
        json_boot = self._getJsonBootDict(self.time["boot_uuid"])
        self.time = {**self.time, **json_boot}
        self._is_synced = self.time["synced"]
        if self._is_synced == 0:
          self._checkSync()
        else:
          self.time = {"ts": 0, "synced": 1}    # make timeDict shorter

    def getTime(self, intime = None):
      if intime is None:
        intime = self.time
        intime["ts"] = int("%.0f" % time.time())
        return intime
      else:
        if intime["synced"] == 1:
          return intime
        else:
          return self._checkSync(intime)

    def _getJsonBootDict(self, boot_uuid):
        file_name = "/var/local/time-sync/" + boot_uuid + ".json"
        try:
            with open(file_name, 'r') as json_file:
                return json.load(json_file)
        except json.JSONDecodeError as js_e:
            raise js_e

    def _getUptime(self):
        with open("/proc/uptime","r") as f:
            uptime = f.read()
        f.close()
        return int("%.0f" % float(uptime.split(' ')[0]))

    def _checkSync(self, intime=None):
        if intime is None:
          check_time = self.time
          if check_time["synced"] == 1:
            return check_time
          uptime = self._getUptime()
          boot_offset = self.time["boot_ts"] - self.time["boot_uptime"]
          now_ts = int("%.0f" % check_time.time())
          now_offset = now_ts - uptime
          offset = now_offset - boot_offset
        else:
          check_time = intime
          if check_time["synced"] == 1:
            return check_time
          boot_time = self._getJsonBootDict(check_time["boot_uuid"])
          if boot_time["synced"] == 1:
            offset = boot_time["sync"]["offset"]
          else:
            return check_time
          uptime = boot_time["boot_uptime"]
          boot_offset = boot_time["boot_ts"] - self.time["boot_uptime"]

#        print("new offset: " + str(offset))

        # wenn zeit differenz über 60 sekunden
        if abs(offset) > 60:
          synced_time = {"ts": check_time + offset, "synced": 1}

        # save calculated offset, if this boot
        if intime is None:
          save_time = check_time
          save_time["synced"] = 1
          save_time["sync"]["offset"] = offset
          save_time["sync"]["uptime"] = uptime
          try:
            file_name = "/var/local/time-sync/" + save_time["boot_uuid"] + ".json"
            with open(file_name, 'w+t') as uuid_json_file:
              json.dump(save_time, uuid_json_file)
          except OSError as os_e:
            logging.error("TIME-SYNC: %s", os_e)
          self.time = save_time


raspi_time_sync = RaspiTimeSync()

print(raspi_time_sync.getTime())

