import json
import os
from datetime import datetime
import xml.etree.ElementTree as ET


class By:
    NAME = "name"
    START_TIMESTAMP = "start_timestamp"
    ID = "id"
    FEATURE = "feature"


class CucumberReport:

    __results = []

    def __init__(self, dir, project_key=None) -> None:
        self.dir = dir
        self.project_key = project_key

        self.data = self.__read()

    def __get_files(self):
        files =  os.listdir(self.dir)
        return [f for f in files if f.endswith(".json")]


    def __read(self):
        reports = self.__get_files()
        for report in reports:
            with open(os.path.join(self.dir, report), "rb") as f:
                text = f.read()
            features = json.loads(text)
            print(features)
            for feature in features:
                print(feature)
                feature_name = None
                try:
                    feature_name = feature["name"]
                except Exception as e:
                    print("Feature name wasn't read properly")
                    print(e)
                for scenario in feature["elements"]:
                    try:
                        is_failed = False
                        failed_step = None
                        error_message = None
                        tags = []
                        test = {"name":scenario["name"], "start_timestamp":self.__to_timestap(scenario["start_timestamp"]),"id":scenario["id"],"feature":feature_name}
                        # getting status of the test and failed step name
                        # handle before
                        for step in scenario["before"]:
                            if step["result"]["status"] == "failed":
                                is_failed = True
                                failed_step = step["name"]
                                error_message = step["result"]["error_message"]
                        # handle after
                        for step in scenario["after"]:
                            if step["result"]["status"] == "failed":
                                is_failed = True
                                failed_step = step["name"]
                                error_message = step["result"]["error_message"]
                        # handle scenario steps
                        for step in scenario["steps"]:
                            if step["result"]["status"] == "failed":
                                is_failed = True
                                failed_step = step["name"]
                                error_message = step["result"]["error_message"]
                        # getting list of tags
                        for tag in scenario["tags"]:
                            tags.append(tag["name"])
                        test["tags"] = tags
                        test["aio_key"] = None
                        if self.project_key is not None:
                            for tag in tags:
                                if self.project_key in tag:
                                    test["aio_key"] = tag.replace("@","")
                        test["is_failed"] = is_failed
                        test["failed_step"] = failed_step
                        test["error_message"] = error_message
                        test["status"] = "failed" if test["is_failed"] is True else "passed"
                        # get screenshot path
                        test["screenshot"] = None
                        if is_failed:
                            error_log = test["error_message"].split('\r\n')
                            for line in error_log:
                                if "Screenshot" in line:
                                    path = line.split("file:/")[1]
                                    # fix for the gitlab-ci path
                                    if "\nPage" in path:
                                        path = "/" +  path.split("\nPage")[0]
                                    test["screenshot"] = path
                        self.__results.append(test)
                    except Exception as e:
                        print("Data of the test wasn't read properly")
                        print(e)

    def __to_timestap(self, time: str) -> int:
        dt = datetime.strptime(time.replace("Z", ""), '%Y-%m-%dT%H:%M:%S.%f')
        return int(round(dt.timestamp()))

    def merge(self):
        history = []
        output = []
        for i in range(0, len(self.__results)):
            id = self.__results[i]["id"]

            if id in history:
                continue

            duplicates = []
            history.append(id)

            for j in range(i, len(self.__results)):
                if self.__results[j]["id"] == id:
                    duplicates.append(self.__results[j])


            output.append(sorted(duplicates, key=lambda d: d['start_timestamp'], reverse=True)[0])

        self.__results = output

    def sort(self,key):
        tmp = sorted(self.__results, key=lambda d: d[key])
        self.results = tmp



    @property
    def get_results(self):
        return self.__results

    @property
    def get_total(self):
        return len(self.__results)

    @property
    def get_total_features(self):
        features = []
        for test in self.__results:
            if test["feature"] not in features:
                features.append(test["feature"])
        return len(features)


    @property
    def get_failed(self):
        failed = 0
        for test in self.__results:
            if test["is_failed"]:
                failed += 1
        return failed

    @property
    def get_aio_linked_tests(self):
        output = []
        for test in self.__results:
            if "aio_key" in test:
                if test["aio_key"] is not None:
                    output.append(test)
        return output

    @property
    def get_aio_failed_scenarios(self):
        output = []
        for test in self.get_aio_linked_tests:
            if test["is_failed"]:
                output.append(test)
        return output

    @property
    def get_tags(self):
        output = []
        for test in self.__results:
            for tag in test['tags']:
                if tag not in output and "debug" not in tag and "Pack" not in tag and "ESHOP-UI" not in tag:
                    output.append(tag)
        output = [i.replace("@", "") for i in output]
        return output

    @property
    def get_tags_stat(self):
        tags = ["@" + tag for tag in self.get_tags]
        stats = {}
        for tag in tags:
            stats[tag] = {"total": 0, "passed": 0, "pass_rate": 0}
        for test in self.__results:
            for tag in test['tags']:
                if tag in stats.keys():
                    stats[tag]['total'] += 1
                    if test['status'] == 'passed':
                        stats[tag]['passed'] += 1
        for tag in stats:
            stats[tag]["pass_rate"] = int(stats[tag]["passed"] / stats[tag]["total"] * 100)
        keys = [key for key in stats]
        for i in range(0, len(stats)):
            tag = keys[i]
            stats[tag.replace("@", "")] = stats.pop(tag)
        return stats

    @property
    def get_feature_stat(self) -> dict:
        features = {}
        for test in self.__results:
            # first test in feature
            if test["feature"] not in features.keys():
                passed = 0
                failed = 0
                if test['is_failed']:
                    failed += 1
                else:
                    passed += 1
                feature = {"passed": passed, "failed": failed, "total": 1, "pass_rate": 0}
                features[test["feature"]] = feature
            # feature already contains tests
            else:
                features[test['feature']]['total'] += 1
                if test['is_failed']:
                    features[test['feature']]['failed'] += 1
                else:
                    features[test['feature']]['passed'] += 1
        # count pass rate
        for feature in features:
            features[feature]["pass_rate"] = int(features[feature]["passed"] / features[feature]["total"] * 100)
        return features


class TestNG:
    reporter_output = None
    suite = None

    def __init__(self, xml_file):
        self.xml_file = xml_file

        self.parse()

    def parse(self):
        tree = ET.parse(self.xml_file)
        root = tree.getroot()
        self.reporter_output = root.attrib
        for child in root:
            if child.tag == "suite":
                self.suite = child.attrib

    @property
    def started_at(self):
        return self.suite["started-at"]

    @property
    def finished_at(self):
        return self.suite["finished-at"]
