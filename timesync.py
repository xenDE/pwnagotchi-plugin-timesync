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

    def __init__(self):
        try:
            with open("/var/lib/systemd/random-seed","rb") as f:
                random_seed_data = f.read()
            f.close() 
            self._boot_uuid = hashlib.md5(random_seed_data).hexdigest();

            self._uuid_json_file = "/var/local/time-sync/" + self._boot_uuid + ".json"
            with open(self._uuid_json_file, 'r') as json_file:
                self._json = json.load(json_file)
        except json.JSONDecodeError as js_e:
            raise js_e
        self._boot_uptime = self._json['boot_uptime']
        self._boot_ts = self._json['boot_ts']
        self._is_synced = self._json['synced']
        self.checkSync()

    def checkSync(self):
        if self._is_synced == 0:
            now_ts = int("%.0f" % time.time())
            with open("/proc/uptime","r") as f:
                uptime = f.read()
            f.close()
            now_uptime = int("%.0f" % float(uptime.split(' ')[0]))
            boot_offset = self._boot_ts - self._boot_uptime
            now_offset = now_ts - now_uptime
            self._offset = now_offset - boot_offset
#            print("offset: " + str(self._offset))
            # wenn zeit differenz über 60 sekunden
            if abs(self._offset) > 60:
                self._json['synced'] = 1
                self._json['sync']['uptime'] = now_uptime
                self._json['sync']['offset'] = self._offset
                try:
                    with open(self._uuid_json_file, 'w+t') as uuid_json_file:
                        json.dump(self._json, uuid_json_file)
                except OSError as os_e:
                    logging.error("TIME-SYNC: %s", os_e)



raspi_time_sync = RaspiTimeSync()


