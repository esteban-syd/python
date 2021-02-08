
from __future__ import (absolute_import, division, print_function)
import six

__metaclass__ = type

import json
import os
# import sys
# import shutil
import glob

# sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../python-routines/asciidoctorgenerator.py")
# from asciidoctorgenerator import *

from ansible.plugins.callback import CallbackBase


def _new_task(task):
    return {
        'task': {
            'name': task.name,
            'id': str(task._uuid)
        },
        'hosts': {}
    }


def _new_play(play):
    return {
        'play': {
            'name': play.name,
            'id': str(play._uuid)
        },
        'tasks': []
    }


class CallbackModule(CallbackBase):
    # CALLBACK_VERSION = 2.0
    # CALLBACK_TYPE = 'stdout'
    # CALLBACK_NAME = 'json'

    CALLBACK_VERSION = 3.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'json-custom'
    CALLBACK_NEEDS_WHITELIST = True

    # PATH_REPORT=os.path.dirname(os.path.abspath(__file__))

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display)
        self.results = []

    def v2_playbook_on_play_start(self, play):
        self.results.append(_new_play(play))

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.results[-1]['tasks'].append(_new_task(task))

    def v2_runner_on_ok(self, result, **kwargs):
        host = result._host
        self.results[-1]['tasks'][-1]['hosts'][host.name] = result._result

    def v2_playbook_on_stats(self, stats):
        """Display info about playbook statistics"""

        hosts = sorted(stats.processed.keys())

        summary = {}
        for h in hosts:
            s = stats.summarize(h)
            summary[h] = s

        output = {
            'plays': self.results,
            'stats': summary
        }

        print(json.dumps(output, indent=4, sort_keys=True))
        facts_location = os.path.dirname(os.path.abspath(__file__)) + "/../documentation/"
        facts_file = facts_location + "play-data.json"
        if not os.path.exists(facts_location):
            os.makedirs(facts_location)
        with open(facts_file, "w") as text_file:
            text_file.write(json.dumps(output, indent=4, sort_keys=True))
        self.asciidoctorgenerator(output)

    def asciidoctorgenerator(self, facts):
        print("ENTRANDO A generate-asciidoc()")
        # facts_file=os.path.dirname(os.path.abspath(__file__))+ "/../documentation/test.json"
        result_folder = os.path.dirname(os.path.abspath(__file__)) + "/../documentation/"

        checklist_data = dict()
        checklist_file_list = []
        checklist_data_list = []

        print("Borrando archivos viejos en : chapters/anexos")
        for f in glob.glob(result_folder + "chapters/anexos/data/*"):
            os.remove(f)
        for f in glob.glob(result_folder + "chapters/anexos/checklists/*"):
            os.remove(f)

        print("ANTES DEL FOR")
        # print (type(facts))
        # print (facts)
        for item in facts['plays']:
            # Generar nuevo archivo
            fname = result_folder + "chapters/anexos/data/" + item['play']['name'] + "-" + item['play']["id"] + ".adoc"
            checklist_data_list.append("data/" + item['play']['name'] + "-" + item['play']["id"] + ".adoc")

            with open(fname, "w") as text_file:
                self.printLine(text_file, "=== Grupo: " + item['play']['name'])
                self.printLine(text_file, ". Play: " + item['play']['name'])
                self.printLine(text_file, ". Play ID: " + item['play']['id'])
                self.printLine(text_file, ". Size: " + str(len(item['tasks'])))

                self.printLine(text_file, "\n ")
                tasksName = list()
                for task in item['tasks']:
                    if task['task']['name']:
                        tasksName.append(task['task']['name'])
                        self.printLine(text_file, "==== TASK: " + task['task']['name'])
                        for hosts, invhost in six.iteritems(task['hosts']):
                            print("----------------------------------------------------")
                           #print(invhost)
                            raw_cmd_tmp = invhost
                            print(raw_cmd_tmp)
                            if '_raw_params' in raw_cmd_tmp:
                                raw_cmd = invhost['invocation']['module_args']['_raw_params']
                                # self.printLine(text_file,"."+host+": "+invhost['invocation']['module_name'])
                                self.printLine(text_file,
                                               "." + hosts + ": " + invhost['invocation']['module_args']['_raw_params'])
                                if "cat {}" not in raw_cmd:
                                    self.printLine(text_file, "[source,bash]")
                                    self.printLine(text_file, "----")
                                    self.printLine(text_file, "$ " + str(raw_cmd))
                                    if invhost['stdout_lines']:
                                        for line in invhost['stdout_lines']:
                                            self.printLine(text_file, str(line.encode('utf-8')))
                                    else:
                                        self.printLine(text_file, invhost['stderr'])
                                    self.printLine(text_file, "----")
                                    self.printLine(text_file, "\n ")
                                else:
                                    self.printLine(text_file, "[source,bash]")
                                    self.printLine(text_file, "----")
                                    self.printLine(text_file, "$ " + str(raw_cmd))
                                    self.printLine(text_file, "----")
                                    self.printLine(text_file, "\n ")
                                    # seccion de archivos
                                    self.printLine(text_file, "====")
                                    if invhost['stdout_lines']:
                                        for line in invhost['stdout_lines']:
                                            self.printLine(text_file, str(line))
                                    else:
                                        self.printLine(text_file, invhost['stderr'])
                                    self.printLine(text_file, "\n ")
                                    # fin seccion de archivos
                checklist_data[item['play']['name']] = tasksName
                checklist_folder = result_folder + "chapters/anexos/checklists/"

                for key, value in six.iteritems(checklist_data):
                    chkfilename = checklist_folder + "anexo_" + key + ".adoc"
                    checklist_file_list.append("checklists/anexo_" + key + ".adoc")

                    print(checklist_file_list)
                    with open(chkfilename, "w") as chkfile:
                        self.printLine(chkfile, "=== Producto: " + key)
                        self.printLine(chkfile, "\n")
                        self.printLine(chkfile, "====")
                        self.printLine(chkfile, ".Checklist " + key)
                        self.printLine(chkfile,
                                       "//[width=\"100%\", cols=\"^1,^1,4,16\", frame=\"topbot\",options=\"header\"]")
                        self.printLine(chkfile,
                                       "[width=\"100%\", cols=\"^1,4,4\", frame=\"topbot\",options=\"header\"]")
                        self.printLine(chkfile, "|======================")
                        self.printLine(chkfile, "//| #        \n//| Res \n//| Aspecto    \n//| Comentario")
                        self.printLine(chkfile, "| #        \n| Aspecto    \n| Comprobacion")
                        self.printLine(chkfile, "\n")
                        cont = 0
                        for taskItem in value:
                            cont = cont + 1
                            # self.printLine(chkfile, ""+str(taskItem))
                            # print str.replace("is", "was")
                            self.printLine(chkfile, "| " + str(cont))
                            self.printLine(chkfile, "//| image:w.png[]")
                            self.printLine(chkfile, "| " + str(taskItem).replace("|", "\|"))
                            self.printLine(chkfile, "| TBD")
                            self.printLine(chkfile, "\n")

                        self.printLine(chkfile, "|======================")
                        self.printLine(chkfile, "====")

        ## Creando archivo de anexos: data
        fname = result_folder + "chapters/anexos/1_anexos_checklist.adoc"
        with open(fname, "w") as chkfile:
            self.printLine(chkfile, "== Anexo: Checklist de puntos ")
            for item in set(checklist_file_list):
                if "INIT" not in item:
                    self.printLine(chkfile, "\n")
                    self.printLine(chkfile, "include::" + item + "[]")
                # checklist_file_list.append("checklists/anexo_"+key+".adoc")
        fname = result_folder + "chapters/anexos/2_anexos_data.adoc"
        with open(fname, "w") as chkfile:
            self.printLine(chkfile, "== Anexo: Datos obtenidos ")
            for item in set(checklist_data_list):
                if "INIT" not in item:
                    self.printLine(chkfile, "\n")
                    self.printLine(chkfile, "include::" + item + "[]")

    def str_unicode(self, text):
        try:
            text = six.text_type(text, 'utf-8')
        except TypeError:
            return text

    def printLine(self, file, texto):
        print("PRINT LINE: " + texto)
        file.write(texto + "\n")

    v2_runner_on_failed = v2_runner_on_ok
    v2_runner_on_unreachable = v2_runner_on_ok
    v2_runner_on_skipped = v2_runner_on_ok 
