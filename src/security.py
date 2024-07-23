import tkinter.simpledialog
from pathlib import Path

from dotenv import load_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_username: str
    mongo_password: SecretStr
    mongo_cluster: str
    mongo_database: str
    mongo_uri: str

    @property
    def mongo_connection_string(self) -> str:
        return (
            f"mongodb+srv://{self.mongo_username}:{self.mongo_password.get_secret_value()}@{self.mongo_cluster}"
            f".{self.mongo_uri}.mongodb.net"
        )


def check_credentials():
    mongo_filename = "mongo.env"
    mongo_path = Path(Path(__file__).parent.parent.resolve() / mongo_filename)
    if not mongo_path.exists():
        # Prompt the user for a set of credentials (username, password, cluster, database, uri)
        new_username = tkinter.simpledialog.askstring(title="Username", prompt="Please enter your MongoDB username:")
        new_password = tkinter.simpledialog.askstring(title="Password", prompt="Please enter your MongoDB password:")
        new_cluster = tkinter.simpledialog.askstring(title="Cluster", prompt="Please enter your MongoDB cluster:")
        new_database = tkinter.simpledialog.askstring(title="Database", prompt="Please enter your MongoDB database:")
        new_uri = tkinter.simpledialog.askstring(title="URI", prompt="Please enter your MongoDB URI:")
        with open(mongo_path, "w") as mongo_file:
            mongo_file.writelines(f"MONGO_USERNAME='{new_username}'\n")
            mongo_file.writelines(f"MONGO_PASSWORD='{new_password}'\n")
            mongo_file.writelines(f"MONGO_CLUSTER='{new_cluster}'\n")
            mongo_file.writelines(f"MONGO_DATABASE='{new_database}'\n")
            mongo_file.writelines(f"MONGO_URI='{new_uri}'")

    load_dotenv(mongo_path)
    return Settings()


if __name__ == "__main__":
    testing_settings = check_credentials()
    print(testing_settings.mongo_connection_string)
