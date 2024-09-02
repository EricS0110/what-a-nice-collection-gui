import json
from pathlib import Path

from pymongo import MongoClient

from src.security import Settings, check_credentials


class MongoConnection:
    def __init__(self, settings: Settings):
        """
        Create MongoDB connection instance to use throughout the application
        :param settings: Pydantic Settings object that stores application settings
        """
        self.settings = settings
        self.mongo_client = MongoClient(settings.mongo_connection_string)
        self.db = self.mongo_client[settings.mongo_database]
        self.CACHE_PATH = Path(__file__).parent.parent.resolve() / "fields_cache.json"

    def get_collections(self) -> [str | None]:
        """
        Retrieves collections present in the established MongoDB instance
        :return: either an empty list [] or a list of the collection names
        """
        no_collections = []
        found_collections = [col["name"] for col in self.db.list_collections()]
        if len(found_collections) == 0:
            return no_collections
        else:
            return found_collections

    def add_collection(self, collection_value: str):
        """
        Add a collection to the established MongoDB instance
        :param collection_value: string value for the new collection's name
        :return: None
        """
        self.db.create_collection(collection_value)
        return

    def update_fields_cache(self):
        """
        Updates the list of available fields in all collections and stores to a JSON file
        :return: None
        """
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
        """
        Loads in the stored JSON data representing available fields in each collection
        :return: Dictionary object containing the JSON data
        """
        with open(self.CACHE_PATH, "r") as fields_cache_file:
            my_fields_cache = json.load(fields_cache_file)
        return my_fields_cache

    def add_item(self, collection: str, item: dict) -> None:
        """
        Add a single item to a collection in MongoDB
        :param collection: string value for the Collection name
        :param item: dictionary representing the item to be added
        :return: None
        """
        self.db[collection].insert_one(item)
        return

    def upload_bulk(self, input_df_dict) -> None:
        """
        Callable to trigger the upload of the Excel data to MongoDB
        :param input_df_dict: the parsed dictionary object of the dataframes of upload data
        :return: None
        """
        for collection, df in input_df_dict.items():
            if not df.empty:
                # Check if the collection exists
                if collection not in self.db.list_collection_names():
                    # Create the collection if it does not exist
                    self.db.create_collection(collection)

                # Convert DataFrame to list of dictionaries
                data = df.to_dict(orient="records")

                # Insert data into the collection
                self.db[collection].insert_many(data)
        return


if __name__ == "__main__":
    testing_settings = check_credentials()
    test_conn = MongoConnection(testing_settings)
    print(test_conn.update_fields_cache())
