import json
from pathlib import Path

from pymongo import MongoClient

from src.security import Settings, check_credentials


class MongoConnection:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.mongo_client = MongoClient(settings.mongo_connection_string)
        self.db = self.mongo_client[settings.mongo_database]
        self.CACHE_PATH = Path(__file__).parent.parent.resolve() / "fields_cache.json"

    def get_collections(self) -> [str | None]:
        no_collections = []
        found_collections = [col["name"] for col in self.db.list_collections()]
        if len(found_collections) == 0:
            return no_collections
        else:
            return found_collections

    def add_collection(self, collection_value: str):
        self.db.create_collection(collection_value)
        return

    def update_fields_cache(self):
        found_collections = [col["name"] for col in self.db.list_collections()]
        fields_cache = {}
        if len(found_collections) == 0:
            with open(self.CACHE_PATH, "w") as fields_cache_file:
                json.dump(fields_cache, fields_cache_file, indent=4)
        else:
            for collection in found_collections:
                active_collection = self.db[collection]
                # Pipeline to get all unique field names in the collection
                pipeline = [
                    {"$project": {"arrayofkeyvalue": {"$objectToArray": "$$ROOT"}}},
                    {"$unwind": "$arrayofkeyvalue"},
                    {"$group": {"_id": None, "allkeys": {"$addToSet": "$arrayofkeyvalue.k"}}},
                ]

                # Run the aggregation pipeline
                result = list(active_collection.aggregate(pipeline))

                # Extract the list of unique field names
                field_names = result[0]["allkeys"] if result else []
                fields_cache[collection] = sorted(field_names)
            with open(self.CACHE_PATH, "w") as fields_cache_file:
                json.dump(fields_cache, fields_cache_file, indent=4)
        return

    def read_fields_cache(self) -> dict:
        with open(self.CACHE_PATH, "r") as fields_cache_file:
            my_fields_cache = json.load(fields_cache_file)
        return my_fields_cache


if __name__ == "__main__":
    testing_settings = check_credentials()
    test_conn = MongoConnection(testing_settings)
    print(test_conn.update_fields_cache())
