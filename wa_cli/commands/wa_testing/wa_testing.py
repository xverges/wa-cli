
# spell-checker:ignore thres

from abc import ABC, abstractmethod
import inspect
import json
import os
import shlex
import shutil
import subprocess
import sys
from ..helpers import cfg

class TestingToolTestFiles(ABC):

    defaults = {
        'conf_threshold': 0.2,
        'max_test_rate': 100,
    }

    def __init__(self, output_directory, test_type):
        self.output_directory = output_directory
        self.test_type = test_type
        self.cfg_path = os.path.join(output_directory, 'wa-testing-tool.ini')
        self.skill_name = os.path.basename(output_directory)
        os.makedirs(self.output_directory, exist_ok=True)

    @abstractmethod
    def cfg_contents(self):
        pass

    def cleanup(self):
        if os.path.isfile(self.cfg_path):
            os.remove(self.cfg_path)

    def write_cfg(self):
        with open(self.cfg_path, 'w') as _file:
            _file.write(self.cfg_contents())
        return self.cfg_path

    def graphics_as_html(self):
        html = f"""
        <html>
            <body>
                <h1>{self.skill_name}</h1>
                <figure>
                    <img src="./{self.test_type}.png" width="60%">
                </figure>
                <figure>
                    <img src="./{self.test_type}-out.metrics.png" width="80%">
                </figure>
                <figure>
                    <img src="./{self.test_type}-out.confusion_args.png" width="80%">
                </figure>
            </body>
        </html>
        """
        html = inspect.cleandoc(html)
        html_path = os.path.join(self.output_directory, 'index.html')
        with open(html_path, 'w') as _file:
            _file.write(html)
        return html_path

class KFoldTestFiles(TestingToolTestFiles):

    template = """

    [ASSISTANT CREDENTIALS]
    iam_apikey = {apikey}
    url = {url}
    version=2019-02-28

    [DEFAULT]
    mode = kfold
    workspace_id = {skill_file}

    fold_num = {fold_num}
    output_directory = {output_directory}
    conf_thres = {conf_threshold}
    keep_workspace_after_test = no
    max_test_rate = {max_test_rate}
    """

    def __init__(self, apikey, url, skill_file, fold_num, output_directory):
        super().__init__(output_directory, 'kfold')
        template = inspect.cleandoc(self.template)
        self.contents = template.format(apikey=apikey,
                                        url=url,
                                        skill_file=skill_file,
                                        fold_num=fold_num,
                                        output_directory=output_directory,
                                        **self.defaults)

    def cfg_contents(self):
        return self.contents

    def cleanup(self):
        super().cleanup()
        shutil.rmtree(os.path.join(self.output_directory, 'kfold'), ignore_errors=True)
        for tmp_file in ['workspace_base.json', 'intent-train.csv', 'entity-train.csv']:
            tmp_file = os.path.join(self.output_directory, tmp_file)
            if os.path.isfile(tmp_file):
                os.remove(tmp_file)


class wa_testing_tool_core(object):

    @classmethod
    def _run_command(cls, cfg_file: str):
        script_path = os.path.join(cfg.test_scripts_folder(), 'run.py')
        command_line = [
            sys.executable,
            script_path,
            '--config_file', cfg_file]
        print(f'Launching {" ".join(command_line)}')
        completed = subprocess.run(command_line,
                                   stderr=sys.stderr, stdout=sys.stdout)
        if completed.returncode != 0:
            raise RuntimeError(f'Failure running {script_path}')
        return True

    @classmethod
    def run(cls, test_files, show_graphics):
        try:
            cfg_path = test_files.write_cfg()
            success = cls._run_command(cfg_path)
            html_path = test_files.graphics_as_html()
            if show_graphics:
                os.system(f'open {shlex.quote(html_path)}')
            return success
        finally:
            test_files.cleanup()


class wa_testing(object):

    @staticmethod
    def _skill_name(skill_file):
        with open(skill_file, 'r') as json_file:
            return json.load(json_file)['name']

    @classmethod
    def _root_for_skill(cls, skill_name, test_type):
        root = cfg.test_folder()
        return os.path.join(root, test_type, skill_name)

    @classmethod
    def k_fold(cls, apikey: str, url: str, skill_file: str, folds: int, show_graphics: bool):
        output_dir = cls._root_for_skill(cls._skill_name(skill_file), 'kfold')
        test_files = KFoldTestFiles(apikey, url, skill_file, folds, output_dir)
        return wa_testing_tool_core.run(test_files, show_graphics)
