# Copyright (C) Yamaha Corporation.
#
# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <https://www.gnu.org/licenses/gpl-3.0.txt>.
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
authors:
  - Yamaha Corporation
cliconf: rtx
short_description: Use rtx cliconf to run command on Yamaha RTX/NVR/FWX/vRX devices.
description:
  - This rtx plugin provides low level abstraction apis for
    sending and receiving CLI commands from Yamaha RTX/NVR/FWX/vRX devices.
version_added: "2.10"
"""

import re
import time
import json

from itertools import chain

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.six import iteritems
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import NetworkConfig, dumps
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase, enable_mode


class Cliconf(CliconfBase):

    @enable_mode
    def get_config(self, source='running', flags=None, format=None):
        if source not in ('running', 'startup'):
            raise ValueError("fetching configuration from %s is not supported" % source)

        if format:
            raise ValueError("'format' value %s is not supported for get_config" % format)

        if not flags:
            flags = []

        cmd = 'show config '

        cmd += ' '.join(to_list(flags))
        cmd = cmd.strip()

        return self.send_command(cmd)

    def get_diff(self, candidate=None, running=None, diff_match='line', diff_ignore_lines=None, path=None, diff_replace='line'):
        """
        Generate diff between candidate and running configuration. If the
        remote host supports onbox diff capabilities ie. supports_onbox_diff in that case
        candidate and running configurations are not required to be passed as argument.
        In case if onbox diff capability is not supported candidate argument is mandatory
        and running argument is optional.
        :param candidate: The configuration which is expected to be present on remote host.
        :param running: The base configuration which is used to generate diff.
        :param diff_match: Instructs how to match the candidate configuration with current device configuration
                      Valid values are 'line', 'strict', 'exact', 'none'.
                      'line' - commands are matched line by line
                      'strict' - command lines are matched with respect to position
                      'exact' - command lines must be an equal match
                      'none' - will not compare the candidate configuration with the running configuration
        :param diff_ignore_lines: Use this argument to specify one or more lines that should be
                                  ignored during the diff.  This is used for lines in the configuration
                                  that are automatically updated by the system.  This argument takes
                                  a list of regular expressions or exact line matches.
        :param path: The ordered set of parents that uniquely identify the section or hierarchy
                     the commands should be checked against.  If the parents argument
                     is omitted, the commands are checked against the set of top
                    level or global commands.
        :param diff_replace: Instructs on the way to perform the configuration on the device.
                        If the replace argument is set to I(line) then the modified lines are
                        pushed to the device in configuration mode.  If the replace argument is
                        set to I(block) then the entire command block is pushed to the device in
                        configuration mode if any line is not correct.
        :return: Configuration diff in  json format.
               {
                   'config_diff': '',
               }

        """
        diff = {}
        device_operations = self.get_device_operations()
        option_values = self.get_option_values()

        if candidate is None and device_operations['supports_generate_diff']:
            raise ValueError("candidate configuration is required to generate diff")

        if diff_match not in option_values['diff_match']:
            raise ValueError("'match' value %s in invalid, valid values are %s" % (diff_match, ', '.join(option_values['diff_match'])))

        if diff_replace not in option_values['diff_replace']:
            raise ValueError("'replace' value %s in invalid, valid values are %s" % (diff_replace, ', '.join(option_values['diff_replace'])))

        # prepare candidate configuration
        candidate_obj = NetworkConfig(indent=1)
        candidate_obj.load(candidate)

        if running and diff_match != 'none':
            # running configuration
            running_obj = NetworkConfig(indent=1, contents=running, ignore_lines=diff_ignore_lines)
            configdiffobjs = candidate_obj.difference(running_obj, path=path, match=diff_match, replace=diff_replace)

        else:
            configdiffobjs = candidate_obj.items

        diff['config_diff'] = dumps(configdiffobjs, 'commands') if configdiffobjs else ''
        return diff

    @enable_mode
    def edit_config(self, candidate=None, commit=True, replace=None, comment=None):
        resp = {}
        operations = self.get_device_operations()
        self.check_edit_config_capability(operations, candidate, commit, replace, comment)

        results = []
        requests = []
        if commit:
            for line in to_list(candidate):
                if not isinstance(line, Mapping):
                    line = {'command': line}

                cmd = line['command']
                if cmd != 'exit':
                    results.append(self.send_command(**line))
                    requests.append(cmd)

        else:
            raise ValueError('check mode is not supported')

        resp['request'] = requests
        resp['response'] = results
        return resp

    def edit_macro(self, candidate=None, commit=True, replace=None, comment=None):
        resp = {}
        operations = self.get_device_operations()
        self.check_edit_config_capability(operations, candidate, commit, replace, comment)

        results = []
        requests = []
        if commit:
            commands = ''
            for line in candidate:
                if line != 'None':
                    commands += (line + '\n')
                obj = {'command': commands, 'sendonly': True}
            results.append(self.send_command(**obj))
            requests.append(commands)
            self.send_command('EOM', sendonly=True)
            time.sleep(0.1)
            results.append(self.send_command('\n'))
            requests.append('\n')

        resp['request'] = requests
        resp['response'] = results
        return resp

    def get(self, command=None, prompt=None, answer=None, sendonly=False, output=None, newline=True, check_all=False):
        if not command:
            raise ValueError('must provide value of command to execute')
        if output:
            raise ValueError("'output' value %s is not supported for get" % output)

        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'rtx'

        reply = self.get(command='show environment | grep Rev')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'(Rev.(\S+\s\(.*\)))', data)
        if match:
            device_info['network_os_version'] = match.group(1)

        match = re.search(r'((RTX|NVR|FWX)\d{3,5}|vRX)', data)
        if match:
            device_info['network_os_model'] = match.group(1)

        reply = self.get(command='show config | grep prompt')
        data = to_text(reply, errors='surrogate_or_strict').strip()
        match = re.search(r'console prompt (.+)', data)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        return device_info

    def get_device_operations(self):
        return {
            'supports_diff_replace': True,
            'supports_commit': False,
            'supports_rollback': False,
            'supports_defaults': False,
            'supports_onbox_diff': False,
            'supports_commit_comment': False,
            'supports_multiline_delimiter': False,
            'supports_diff_match': True,
            'supports_diff_ignore_lines': True,
            'supports_generate_diff': True,
            'supports_replace': False
        }

    def get_option_values(self):
        return {
            'format': ['text'],
            'diff_match': ['line', 'strict', 'exact', 'none'],
            'diff_replace': ['line', 'block'],
            'output': []
        }

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        result['rpc'] += ['get_diff', 'run_commands']
        result['device_operations'] = self.get_device_operations()
        result.update(self.get_option_values())
        return json.dumps(result)

    def run_commands(self, commands=None, check_rc=True):
        if commands is None:
            raise ValueError("'commands' value is required")

        responses = list()
        for cmd in to_list(commands):
            if not isinstance(cmd, Mapping):
                cmd = {'command': cmd}

            output = cmd.pop('output', None)
            if output:
                raise ValueError("'output' value %s is not supported for run_commands" % output)

            try:
                out = self.send_command(**cmd)
            except AnsibleConnectionFailure as e:
                if check_rc:
                    raise
                out = getattr(e, 'err', to_text(e))

            responses.append(out)

        return responses
