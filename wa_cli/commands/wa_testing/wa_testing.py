
# spell-checker:ignore thres

import inspect
import os
import shlex
import subprocess
import sys
from ..helpers import cfg

KFOLD_TEMPLATE = """
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


class wa_testing(object):

    defaults = {
        'conf_threshold': 0.2,
        'max_test_rate': 100,
    }

    def __init__(self, skill_file: str, folds: int = 5):
        self.skill_file = os.path.abspath(skill_file)
        self.skill_test_root = self._skill_test_root()
        self.test_output = os.path.join(self.skill_test_root, 'data')
        self.folds = folds

    def _skill_test_root(self) -> str:
        skill_folder_name = os.path.splitext(os.path.basename(self.skill_file))[0]
        test_folder = cfg.test_folder()
        return os.path.join(test_folder, skill_folder_name)

    def kfold_cfg(self, apikey: str, url: str, skill_file: str) -> str:
        cfg_contents = KFOLD_TEMPLATE.format(apikey=apikey,
                                             url=url,
                                             skill_file=self.skill_file,
                                             fold_num=self.folds,
                                             output_directory=self.test_output,
                                             **self.defaults)
        cfg_path = os.path.join(self.skill_test_root, 'wa-testing-tool.ini')
        os.makedirs(self.test_output, exist_ok=True)
        with open(cfg_path, 'w') as _file:
            _file.write(cfg_contents)
        print(cfg_contents)
        return cfg_path

    def graphics_as_html(self, launch: bool = False):
        html = f"""
        <html>
            <body>
                <h1>{os.path.basename(self.skill_test_root)}</h1>
                <figure>
                    <img src="./kfold.png" width="60%">
                </figure>
                <figure>
                    <img src="./kfold-out.metrics.png" width="80%">
                </figure>
                <figure>
                    <img src="./kfold-out.confusion_args.png" width="80%">
                </figure>
            </body>
        </html>
        """
        html = inspect.cleandoc(html)
        html_path = os.path.join(self.test_output, 'k-fold.html')
        with open(html_path, 'w') as _file:
            _file.write(html)
        if launch:
            os.system(f'open {shlex.quote(html_path)}')

    def run(self, cfg_file: str):
        script_path = os.path.join(cfg.test_scripts_folder(), 'run.py')
        command_line = [
            sys.executable,
            script_path,
            '--config_file', cfg_file]
        print(f'===> {" ".join(command_line)}')
        completed = subprocess.run(command_line,
                                   stderr=sys.stderr, stdout=sys.stdout)
        if completed.returncode != 0:
            raise RuntimeError(f'Failure running {script_path}')

    @classmethod
    def k_fold(cls, apikey: str, url: str, skill_file: str, folds: int, show_graphics: bool):
        cfg_file = ''
        try:
            tester = wa_testing(skill_file, folds=folds)
            cfg_file = tester.kfold_cfg(apikey, url, skill_file)
            success = tester.run(cfg_file)
            tester.graphics_as_html(launch=show_graphics)
            return success
        finally:
            if cfg_file:
                os.remove(cfg_file)
