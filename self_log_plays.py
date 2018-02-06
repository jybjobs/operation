################################
###  callback_plugins
###  jinyubing@yihecloud.com
################################

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: self_log_plays
    type: notification
    short_description: write playbook output to a file per host
    version_added: historical
    description:
      - This callback writes playbook output to a file per host in the `/var/log/ansible/hosts` directory
      - "TODO: make this configurable"
    requirements:
     - Whitelist in configuration
     - A writeable /var/log/ansible/hosts directory by the user executing Ansbile on the controller
'''

import os
import time
import json
from collections import MutableMapping

from ansible import constants as C
from ansible.module_utils._text import to_bytes
from ansible.plugins.callback import CallbackBase


# NOTE: in Ansible 1.2 or later general logging is available without
# this plugin, just set ANSIBLE_LOG_PATH as an environment variable
# or log_path in the DEFAULTS section of your ansible configuration
# file.  This callback is an example of per hosts logging for those
# that want it.


class CallbackModule(CallbackBase):
    """
    logs playbook results, per host, in /var/log/ansible/hosts
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'log_plays'
    CALLBACK_NEEDS_WHITELIST = True

    TIME_FORMAT = "%b %d %Y %H:%M:%S"
    MSG_FORMAT = "%(now)s - %(category)s - %(task)s - %(data)s\n\n"

    def __init__(self):

        super(CallbackModule, self).__init__()

        if not os.path.exists("/var/log/ansible/hosts"):
            os.makedirs("/var/log/ansible/hosts")

    def log(self, host, category,task, data):
        if isinstance(data, MutableMapping):
            if '_ansible_verbose_override' in data:
                # avoid logging extraneous data
                data = 'omitted'
            else:
                data = data.copy()
                invocation = data.pop('invocation', None)
                data = json.dumps(data)
                if invocation is not None:
                    data = json.dumps(invocation) + " => %s " % data

        path = os.path.join("/var/log/ansible/hosts", host)
        now = time.strftime(self.TIME_FORMAT, time.localtime())

        msg = to_bytes(self.MSG_FORMAT % dict(now=now, category=category,task=task, data=data))
        with open(path, "ab") as fd:
            fd.write(msg)

    def runner_on_failed(self, host,task,res, ignore_errors=False):
        self.log(host, 'FAILED',task, res)

    def runner_on_ok(self, host,task, res):
        self.log(host, 'OK',task, res)

    def runner_on_skipped(self, host,task, item=None):
        self.log(host, 'SKIPPED',task, '...')

    def runner_on_unreachable(self, host,task, res):
        self.log(host, 'UNREACHABLE',task, res)

    def runner_on_async_failed(self, host, res, jid):
        self.log(host, 'ASYNC_FAILED', res)

    def playbook_on_import_for_host(self, host, imported_file):
        self.log(host, 'IMPORTED', imported_file)

    def playbook_on_not_import_for_host(self, host, missing_file):
        self.log(host, 'NOTIMPORTED', missing_file)



    # V2 METHODS, by default they call v1 counterparts if possible
    def v2_on_any(self, *args, **kwargs):
        self.on_any(args, kwargs)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        task = result._task.get_name().strip()
        self.runner_on_failed(host,task,result._result, ignore_errors)

    def v2_runner_on_ok(self, result):
        host = result._host.get_name()
        task = result._task.get_name().strip()
        self.runner_on_ok(host,task, result._result)

    def v2_runner_on_skipped(self, result):
        if C.DISPLAY_SKIPPED_HOSTS:
            host = result._host.get_name()
            task = result._task.get_name().strip()
            self.runner_on_skipped(host,task, self._get_item(getattr(result._result, 'results', {})))

    def v2_runner_on_unreachable(self, result):
        host = result._host.get_name()
        task = result._task.get_name().strip()
        self.runner_on_unreachable(host, task,result._result)

    def v2_runner_on_no_hosts(self, task):
        self.runner_on_no_hosts()

    def v2_runner_on_async_poll(self, result):
        host = result._host.get_name()

        jid = result._result.get('ansible_job_id')
        # FIXME, get real clock
        clock = 0
        self.runner_on_async_poll(host, result._result, jid, clock)

    def v2_runner_on_async_ok(self, result):
        host = result._host.get_name()
        jid = result._result.get('ansible_job_id')
        self.runner_on_async_ok(host, result._result, jid)

    def v2_runner_on_async_failed(self, result):
        host = result._host.get_name()
        jid = result._result.get('ansible_job_id')
        self.runner_on_async_failed(host, result._result, jid)

    def v2_runner_on_file_diff(self, result, diff):
        pass  # no v1 correspondence

    def v2_playbook_on_start(self, playbook):
        self.playbook_on_start()

    def v2_playbook_on_notify(self, result, handler):
        host = result._host.get_name()
        self.playbook_on_notify(host, handler)

    def v2_playbook_on_no_hosts_matched(self):
        self.playbook_on_no_hosts_matched()

    def v2_playbook_on_no_hosts_remaining(self):
        self.playbook_on_no_hosts_remaining()

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.playbook_on_task_start(task.name, is_conditional)

    def v2_playbook_on_cleanup_task_start(self, task):
        pass  # no v1 correspondence

    def v2_playbook_on_handler_task_start(self, task):
        pass  # no v1 correspondence

    def v2_playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        self.playbook_on_vars_prompt(varname, private, prompt, encrypt, confirm, salt_size, salt, default)

    def v2_playbook_on_setup(self):
        self.playbook_on_setup()

    def v2_playbook_on_import_for_host(self, result, imported_file):
        host = result._host.get_name()
        self.playbook_on_import_for_host(host, imported_file)

    def v2_playbook_on_not_import_for_host(self, result, missing_file):
        host = result._host.get_name()
        self.playbook_on_not_import_for_host(host, missing_file)

    def v2_playbook_on_play_start(self, play):
        self.playbook_on_play_start(play.name)

    def v2_playbook_on_stats(self, stats):
        self.playbook_on_stats(stats)

    def v2_on_file_diff(self, result):
        if 'diff' in result._result:
            host = result._host.get_name()
            self.on_file_diff(host, result._result['diff'])

    def v2_playbook_on_include(self, included_file):
        pass  # no v1 correspondence

    def v2_runner_item_on_ok(self, result):
        pass

    def v2_runner_item_on_failed(self, result):
        pass

    def v2_runner_item_on_skipped(self, result):
        pass

    def v2_runner_retry(self, result):
        pass
