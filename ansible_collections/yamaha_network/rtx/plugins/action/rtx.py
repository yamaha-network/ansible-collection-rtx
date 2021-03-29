# Copyright (C) Yamaha Corporation.
#
# (c) 2016 Red Hat Inc.
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

import re
import sys
import copy

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.utils.display import Display
from ansible_collections.ansible.netcommon.plugins.action.network import ActionModule as ActionNetworkModule

display = Display()


class ActionModule(ActionNetworkModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        module_name = self._task.action.split('.')[-1]
        self._config_module = (
            True if module_name in ['rtx_config'] else False
        )

        socket_path = None

        if self._play_context.connection == 'network_cli':
            provider = self._task.args.get('provider', {})
            if any(provider.values()):
                display.warning('provider is unnecessary when using network_cli and will be ignored')
                del self._task.args['provider']
        else:
            return {'failed': True, 'msg': 'Connection type %s is not valid for this module' % self._play_context.connection}

        result = super(ActionModule, self).run(task_vars=task_vars)
        return result
