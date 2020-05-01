
# spell-checker:ignore thres

from abc import ABC, abstractmethod
from glob import glob
import inspect
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

from ..helpers import cfg
from ..wa import wa


class TestingToolTestFiles(ABC):

    defaults = {
        'conf_threshold': 0.2,
        'max_test_rate': 100,
    }

    def __init__(self, output_directory, test_type):
        self.output_directory = output_directory
        self.test_type = test_type
        self.cfg_path = os.path.join(output_directory, 'wa-testing-tool.ini')
        self.master_skill_name = os.path.basename(output_directory)
        os.makedirs(self.output_directory, exist_ok=True)

    @abstractmethod
    def cfg_contents(self):
        pass

    def cleanup(self):
        for folder in ['blind', 'kfold']:
            tmp_folder = os.path.join(self.output_directory, folder)
            if os.path.isdir(tmp_folder):
                shutil.rmtree(os.path.join(self.output_directory, folder), ignore_errors=True)
        for tmp_file in ['wa-testing-tool.ini', 'workspace_base.json', 'intent-train.csv', 'entity-train.csv']:
            tmp_file = os.path.join(self.output_directory, tmp_file)
            if os.path.isfile(tmp_file):
                os.remove(tmp_file)

    def write_cfg(self):
        with open(self.cfg_path, 'w') as _file:
            _file.write(self.cfg_contents())
        return self.cfg_path

    def graphics_as_html(self):
        separator = '.' if self.test_type == 'kfold' else '_'
        postfix = '_args' if self.test_type == 'kfold' else ''
        html = f"""
        <html>
            <body>
                <h1>Skill: {self.master_skill_name}</h1>
                <figure>
                    <img src="./{self.test_type}.png" width="60%">
                </figure>
                <figure>
                    <img src="./{self.test_type}-out{separator}metrics.png" width="80%">
                </figure>
                <figure>
                    <img src="./{self.test_type}-out{separator}confusion{postfix}.png" width="80%">
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
    workspace_id = {workspace_id}

    fold_num = {fold_num}
    output_directory = {output_directory}
    conf_thres = {conf_threshold}
    keep_workspace_after_test = no
    max_test_rate = {max_test_rate}
    """

    def __init__(self, apikey, url, skill_name, skill_file, fold_num, output_directory):
        super().__init__(output_directory, 'kfold')
        template = inspect.cleandoc(self.template)

        workspace_id = skill_file if not skill_name else wa.workspace_id_from_skill_name(apikey, url, skill_name)
        self.contents = template.format(apikey=apikey,
                                        url=url,
                                        workspace_id=workspace_id,
                                        fold_num=fold_num,
                                        output_directory=output_directory,
                                        **self.defaults)

    def cfg_contents(self):
        return self.contents


class BlindTestFiles(TestingToolTestFiles):

    template = """

    [ASSISTANT CREDENTIALS]
    iam_apikey = {apikey}
    url = {url}
    version=2019-02-28

    [DEFAULT]
    mode = blind
    workspace_id = {workspace_id}

    test_input_file = {input_file}
    {previous_execution_info}
    output_directory = {output_directory}
    conf_thres = {conf_threshold}
    keep_workspace_after_test = no
    max_test_rate = {max_test_rate}
    """

    def __init__(self, apikey, url, skill_name, output_directory):
        super().__init__(output_directory, 'blind')
        template = inspect.cleandoc(self.template)
        input_file = os.path.join(output_directory, 'input.csv')
        if not os.path.isfile(input_file):
            raise ValueError(f'Blind test input file "{input_file}" not found')
        workspace_id = wa.workspace_id_from_skill_name(apikey, url, skill_name)
        if not workspace_id:
            raise ValueError(f'Skill "{skill_name}" not found')
        report_file = os.path.join(output_directory, 'blind-out.csv')
        previous_report = os.path.join(output_directory, 'blind-out-previous.csv')
        previous_execution_info = ''
        if os.path.isfile(report_file):
            shutil.copyfile(report_file, previous_report)
            previous_execution_info = f'previous_blind_out = {previous_report}'
        self.contents = template.format(apikey=apikey,
                                        url=url,
                                        workspace_id=workspace_id,
                                        input_file=input_file,
                                        previous_execution_info=previous_execution_info,
                                        output_directory=output_directory,
                                        **self.defaults)

    def cfg_contents(self):
        return self.contents


class TestingToolCoreMode(object):

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


class TestingToolCoreFlow(object):

    @classmethod
    def run(cls, apikey: str, url: str, skill_name: str, output_dir: str) -> int:
        if skill_name != os.path.basename(output_dir):
            print(f'Running on a sandbox. Using skill "{skill_name}"')
        final_rc = 0
        test_count = 0
        workspace_id = wa.workspace_id_from_skill_name(apikey, url, skill_name)
        if not workspace_id:
            raise ValueError(f'Skill "{skill_name}" not found')
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env['ASSISTANT_PASSWORD'] = apikey
            env['ASSISTANT_URL'] = url
            env['WORKSPACE_ID'] = workspace_id
            script_path = os.path.join(cfg.test_scripts_folder(), 'dialog_test', 'flowtest.py')
            for file_path in glob(os.path.join(output_dir, '*.tsv')):
                if file_path.endswith('_report.tsv'):
                    continue
                test_count += 1
                test_name = os.path.splitext(os.path.basename(file_path))[0]
                command_line = [
                    sys.executable,
                    script_path,
                    file_path]
                print(f'Launching {" ".join(command_line)}')
                completed = subprocess.run(command_line,
                                           stderr=sys.stderr,
                                           stdout=sys.stdout,
                                           env=env,
                                           cwd=tmpdir)
                for report in ['json', 'tsv']:
                    report_file = os.path.join(tmpdir, 'results', f'{test_name}_report.{report}')
                    if os.path.isfile(report_file):
                        shutil.copy(report_file, output_dir)
                print(f'Moving {test_name}_report.tsv to {output_dir}')
                if completed.returncode != 0:
                    final_rc = completed.returncode
        if not test_count:
            print('No tests have been executed', file=sys.stderr)
            final_rc = 1
        return final_rc


class wa_testing(object):

    @staticmethod
    def _skill_name(skill_file):
        with open(skill_file, 'r') as json_file:
            return json.load(json_file)['name']

    @classmethod
    def output_dir_for_skill(cls, skill_name, test_type):
        root = cfg.test_folder()
        return os.path.join(root, test_type, skill_name)

    @classmethod
    def k_fold(cls, apikey: str, url: str, skill_file: str, folds: int, show_graphics: bool,
               output_dir: str = '', skill_name: str = ''):
        if not output_dir:
            name = skill_name if skill_name else cls._skill_name(skill_file)
            output_dir = cls.output_dir_for_skill(name, 'kfold')
        test_files = KFoldTestFiles(apikey, url, skill_name, skill_file, folds, output_dir)
        return TestingToolCoreMode.run(test_files, show_graphics)

    @classmethod
    def blind(cls, apikey: str, url: str, skill_name: str, show_graphics: bool, output_dir: str = ''):
        if not output_dir:
            output_dir = cls.output_dir_for_skill(skill_name, 'blind')
        test_files = BlindTestFiles(apikey, url, skill_name, output_dir)
        return TestingToolCoreMode.run(test_files, show_graphics)

    @classmethod
    def flow(cls, apikey: str, url: str, skill_name: str, output_dir: str = '') -> int:
        if not output_dir:
            output_dir = cls.output_dir_for_skill(skill_name, 'flow')
        return TestingToolCoreFlow.run(apikey, url, skill_name, output_dir)
