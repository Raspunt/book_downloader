import os
import json

class Checkpoint:
    def __init__(self, save_folder: str):
        self.save_folder = save_folder
        self.check_point = os.path.join(self.save_folder, "checkpoint.json")

    def load_checkpoint(self) -> set[str]:
        if os.path.exists(self.check_point):
            try:
                with open(self.check_point, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                return set()
        else:
            with open(self.check_point, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return set()

    def save_checkpoint(self, data: set[str]):
        with open(self.check_point, "w", encoding="utf-8") as f:
            json.dump(list(data), f, ensure_ascii=False, indent=2)
