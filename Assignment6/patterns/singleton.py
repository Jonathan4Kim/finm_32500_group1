import json

class Config:
    # create instance
    _instance = None
    def __new__(cls):
        # ensure that we haven't created an instance yet
        if cls._instance is None:
            
            # get default confiuration attributes
            with open("config.json", "r") as f:
                data = json.load(f)
            # inherit from object
            cls._instance = super().__new__(cls)
            # centralize attributes from config
            cls._instance.log_level = data["log_level"]
            cls._instance.data_path = data["data_path"]
            cls._instance.report_path = data["report_path"]
            cls._instance.default_strategy = data["default_strategy"]
        return cls._instance