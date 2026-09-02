import os
import json


class KnowledgeLoader:

    def __init__(self):

        # Project root (one level above modules/)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.folder = os.path.join(project_root, "knowledge")

        self.data = {}

        self.load_all()

    def load_all(self):

        print("Knowledge Folder:", self.folder)

        for filename in os.listdir(self.folder):

            if filename.endswith(".json"):

                path = os.path.join(self.folder, filename)

                with open(path, "r", encoding="utf-8") as f:

                    name = filename.replace(".json", "")

                    self.data[name] = json.load(f)

        print(f"Loaded {len(self.data)} knowledge files.")

    def get(self, name):
        return self.data.get(name)

    def all(self):
        return self.data
