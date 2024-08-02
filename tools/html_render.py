from jinja2 import Environment, FileSystemLoader
import os


class HTML:

    def __init__(self, template: str, output, title: str, pack_name: str, features: int, total: int, failed: int,
                 env: str, tests=None, tags: list = None, features_stat=None, started_at=None, finished_at=None):
        self.template = template
        self.output = output
        self.title = title
        self.pack_name = pack_name
        self.features = features
        self.total = total
        self.failed = failed
        self.tests = tests
        self.env = env
        self.tags = tags,
        self.features_stat = features_stat
        self.started_at = started_at
        self.finished_at = finished_at

    def __render(self):
        template_folder, template = os.path.split(self.template)
        environment = Environment(loader=FileSystemLoader(template_folder))
        template = environment.get_template(template)
        with open(self.output, "w") as fh:
            fh.write(
                template.render(
                    title=self.title,
                    env=self.env,
                    pack_name=self.pack_name,
                    features=self.features,
                    total=self.total,
                    passed=self.total - self.failed,
                    failed=self.failed,
                    percent=int((self.total - self.failed) / self.total * 100),
                    tags=self.tags,
                    features_stat=self.features_stat,
                    tests=self.tests,
                    started_at=self.started_at,
                    finished_at=self.finished_at
                ))

    def __get_html(self) -> str:
        with open(self.output, "r") as f:
            html = f.read()
        return html

    def render(self) -> str:
        self.__render()
        return self.__get_html()
