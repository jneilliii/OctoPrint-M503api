# -*- coding: utf-8 -*-
from __future__ import absolute_import

import time

import flask
import octoprint.plugin


class M503apiPlugin(
    octoprint.plugin.SimpleApiPlugin, octoprint.plugin.RestartNeedingPlugin
):
    def __init__(self):
        self.processing = False
        self.collection_started = False
        self.collecting = False
        self.M503_data = []

    ##~~ SimpleApiPlugin mixin

    def get_api_commands(self):
        return {"M503": []}

    def on_api_get(self, request):
        self.processing = True
        self.M503_data = []

        if not self._printer.is_operational():
            return flask.jsonify({"error": "printer is busy or disconnected"})

        self._printer.commands("M503")
        while self.processing:
            time.sleep(5)
        return flask.jsonify({"data": self.M503_data})

    ##~~ gcode received hook

    def process_gcode(self, comm, line, *args, **kwargs):
        if not self.processing:
            return line
        if self.collection_started and line.strip() == "ok":
            self.collection_started = False
            return line
        if line.strip() == "m503_collection":
            self.collection_started = True
        if line.strip() == "ok":
            self.collecting = False
            self.processing = False
            return line
        self.M503_data.append(line.strip())
        return line

    ##~~ Softwareupdate hook

    def get_update_information(self):
        return {
            "m503api": {
                "displayName": "M503api Plugin",
                "displayVersion": self._plugin_version,
                # version check: github repository
                "type": "github_release",
                "user": "jneilliii",
                "repo": "OctoPrint-M503api",
                "current": self._plugin_version,
                # update method: pip
                "pip": "https://github.com/jneilliii/OctoPrint-M503api/archive/{target_version}.zip",
            }
        }


__plugin_name__ = "M503API"
__plugin_pythoncompat__ = ">=2.7,<4"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = M503apiPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.received": __plugin_implementation__.process_gcode,
    }
