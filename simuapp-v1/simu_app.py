# Copyright 2019, Google, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Flask app to be used as an interactive demonstration of loadbalancing/healthchecks/autohealing.

Exposes a simple UI showing basic server stats and a toggle button to
simulate a healthy/unhealthy server status for any attached health check.

Attached health checks should query the '/health' path.

Original code by Google (OSS), adapted by Nirmallya to run on AWS.
"""

from ctypes import c_bool
from multiprocessing import Process, Value
from random import random
from re import sub
from socket import gethostname
from time import sleep

from flask import Flask, make_response, render_template
import requests



PORT_NUMBER = 80

app = Flask(__name__)
_is_healthy = None
_cpu_burner = None


@app.before_first_request
def init():
    global _is_healthy, _cpu_burner
    _is_healthy = True
    _cpu_burner = CpuBurner()


@app.route('/')
@app.route('/<path:path>')
def index(path=""):
    """Returns the demo UI as the home page and any other path that does not match.
        This is the default and catch all route
    """
    global _cpu_burner, _is_healthy
    return render_template('index.html',
                           hostname=get_instanceid(),
                           healthy=_is_healthy,
                           working=_cpu_burner.is_running())


@app.route('/health')
def health():
    """Returns the simulated 'healthy'/'unhealthy' status of the server.
    Returns:
        HTTP status 200 if 'healthy', HTTP status 500 if 'unhealthy'
    """
    global _is_healthy
    template = render_template('health.html', healthy=_is_healthy)
    return make_response(template, 200 if _is_healthy else 500)


@app.route('/makeHealthy')
def make_healthy():
    """Sets the server to simulate a 'healthy' status."""
    global _cpu_burner, _is_healthy
    _is_healthy = True
    template = render_template('index.html',
                                hostname=get_instanceid(),
                                healthy=True,
                                working=_cpu_burner.is_running())
    response = make_response(template, 302)
    response.headers['Location'] = '/'
    return response


@app.route('/makeUnhealthy')
def make_unhealthy():
    """Sets the server to simulate an 'unhealthy' status."""
    global _cpu_burner, _is_healthy
    _is_healthy = False
    template = render_template('index.html',
                                hostname=get_instanceid(),
                                healthy=False,
                                working=_cpu_burner.is_running())
    response = make_response(template, 302)
    response.headers['Location'] = '/'
    return response


@app.route('/startLoad')
def start_load():
    """Sets the server to simulate high CPU load."""
    global _cpu_burner, _is_healthy
    _cpu_burner.start()
    template = render_template('index.html',
                                hostname=get_instanceid(),
                                healthy=_is_healthy,
                                working=True)
    response = make_response(template, 302)
    response.headers['Location'] = '/'
    return response


@app.route('/stopLoad')
def stop_load():
    """Sets the server to stop simulating CPU load."""
    global _cpu_burner, _is_healthy
    _cpu_burner.stop()
    template = render_template('index.html',
                                hostname=get_instanceid(),
                                healthy=_is_healthy,
                                working=False)
    response = make_response(template, 302)
    response.headers['Location'] = '/'
    return response


def get_instanceid():
    """Gets the instance ip.
    Returns:
        str: The instance id if it was successfully determined.
        Empty string otherwise.
        v1 Private IP - http://169.254.169.254/1.0/meta-data/local-ipv4
        v2 Private IP - IP_ADDR=$(TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"` \
                        && curl -H "X-aws-ec2-metadata-token: $TOKEN" -v http://169.254.169.254/latest/meta-data/public-ipv4)
    """

    """Get the metadata token"""
    url = "http://169.254.169.254/latest/api/token"
    headers = { "X-aws-ec2-metadata-token-ttl-seconds": "21600"}
    response = requests.put(url, headers=headers)
    if response.status_code == 200:
        meta_token = response.text
        """Now using the metadata token get the public IP from metadata server v2"""
        url = "http://169.254.169.254/latest/meta-data/public-ipv4"
        headers = {"X-aws-ec2-metadata-token": f"{meta_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            return ''
    else:
        return ''


class CpuBurner:
    """
    Object to asynchronously burn CPU cycles to simulate high CPU load.
    Burns CPU in a separate process and can be toggled on and off.
    """
    def __init__(self):
        self._toggle = Value(c_bool, False, lock=True)
        self._process = Process(target=self._burn_cpu)
        self._process.start()

    def start(self):
        """Start burning CPU."""
        self._toggle.value = True

    def stop(self):
        """Stop burning CPU."""
        self._toggle.value = False

    def is_running(self):
        """Returns true if currently burning CPU."""
        return self._toggle.value

    def _burn_cpu(self):
        """Burn CPU cycles if work is toggled, otherwise sleep."""
        while True:
            random()*random() if self._toggle.value else sleep(1)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=PORT_NUMBER)


