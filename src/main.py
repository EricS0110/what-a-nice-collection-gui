from nicegui import ui

# Application flow:
# Check for MongoDB credentials & details file, create and encrypt if not available
# Read and decrypt MongoDB credentials & details, then create Mongo connection object for use in app
# Launch main UI with required components


def check_credentials():
    print("Check if there's a mongo credentials file")
    return


def establish_connection() -> int:
    print("Establish a connection to MongoDB based on the credentials file details")
    return 0


def main_app(mongo_conn):
    ui.label("Getting started with NiceGUI!")

    ui.run()


if __name__ in ("__main__", "__mp_main__"):
    check_credentials()
    mongo_base = establish_connection()
    main_app(mongo_base)
