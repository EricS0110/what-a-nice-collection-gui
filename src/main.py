from io import BytesIO
from pathlib import Path

import pandas as pd
from nicegui import events, ui

from mongo import MongoConnection
from security import check_credentials


def clean_list_string(input_list: list) -> str:
    return ", ".join(map(str, input_list))


src_dir = Path(__file__).parent.resolve()

# Get MongoDB details and any other application configurations established
settings = check_credentials()

# Global variables
bulk_upload_file = None  # store a bulk upload file
available_collections_label = None  # refreshable available collections list

# Get a MongoDB connection instance
mongo_conn = MongoConnection(settings)

# Set up the list of available collections
available_collections = mongo_conn.get_collections()  # List[str]
available_collections_str = ", ".join(mongo_conn.get_collections())  # Single string of comma-sep values

# Set up or update the cache of available fields for each collection
mongo_conn.update_fields_cache()
fields_cache = mongo_conn.read_fields_cache()

# available_collections = ["books", "comics", "movies", "music", "television"]
# with open(Path(__file__).parent.parent.resolve() / "fields_cache.json", "r") as fields_cache_file:
#     fields_cache = json.load(fields_cache_file)

# Set up the UI elements
ui.page_title("Collections App")
with ui.tabs().classes("w-full") as main_tabs:
    welcome_tab = ui.tab("Welcome")
    new_collection = ui.tab("New Collection")
    add_one_tab = ui.tab("Add One")
    add_bulk_tab = ui.tab("Add Bulk")
    search_tab = ui.tab("Search")
    delete_tab = ui.tab("Delete")
with ui.tab_panels(main_tabs, value=welcome_tab).classes("w-full"):
    # Set up the "Welcome" tab environment
    with ui.tab_panel(welcome_tab) as welcome_panel:
        welcome_panel.clear()
        ui.markdown("# Welcome to the Collections Manager application")
        ui.separator()
        ui.label("This application will help you manage what items are stored in your MongoDB collections.")
        ui.label("Tabs:")
        ui.markdown("\t- __Welcome__: You are here!")
        ui.markdown("\t- __New Collection__: add a new collection to your database")
        ui.markdown("\t- __Add One__: add a single item to a collection of your choice")
        ui.markdown("\t- __Add Bulk__: add multiple items based on an Excel file input")
        ui.markdown("\t- __Search__: search your collections for a given item")
        ui.markdown("\t- __Delete__: delete an item from a collection")
        ui.separator().style("padding-top: 50px;")
        with ui.grid(columns=2):
            ui.label("Current database: ")
            ui.label(f"{settings.mongo_database}")

            ui.label("Mongo URI: ")
            ui.label(f"{settings.mongo_uri}")

            ui.label("Source code: ")
            ui.link("Go to GitHub!", "https://github.com/EricS0110/what-a-nice-collection-gui")

            ui.label("Source docs: ")
            ui.link("Go to GitHub Pages!", "https://erics0110.github.io/what-a-nice-collection-gui/")

            ui.label("Available collections at startup: ")
            ui.label(f"{clean_list_string(mongo_conn.get_collections())}")

    # Set up the "New Collection" tab environment
    def add_new_collection():
        new_collection_value = new_collection_input_field.value.lower().strip()
        existing_collections = mongo_conn.get_collections()
        if new_collection_value == "":
            ui.notify("Please enter a collection name")
            return
        if new_collection_value not in existing_collections:
            # add the new collection
            ui.notify("Adding new collection...")
            mongo_conn.add_collection(new_collection_value)
            ui.notify(f"Available collections: {mongo_conn.get_collections()}")
        else:
            ui.notify("Collection already exists!")

    with ui.tab_panel(new_collection):
        ui.markdown("# New Collection")
        ui.markdown("### Name the new collection (lower-case only): ")
        with ui.card():
            new_collection_input_field = ui.input(label="new collection")
            ui.button(text="ADD", color="green", on_click=add_new_collection)

    # Set up the "Add One" tab environment
    current_add_one_fields = {}
    current_add_one_fields_enums = {}

    def add_one_item():
        ui.notify("Adding item...")
        this_collection = collection_selection.value
        these_fields = current_add_one_fields
        these_fields_enums = current_add_one_fields_enums
        item_data = {}
        for k, v in these_fields_enums.items():
            input_value = these_fields[k].value
            if input_value != "":
                item_data[v] = these_fields[k].value
                ui.notify(f"{v}: {these_fields[k].value}")
        # TODO: Need to update to actually send to Mongo, confirm with user before send
        ui.notify(f"Item added to {this_collection}")
        return

    with ui.tab_panel(add_one_tab):
        ui.markdown("# Add One Item")
        ui.separator()
        with ui.row():
            with ui.card():
                ui.markdown("### Select a collection:")
                collection_selection = ui.select(
                    options=mongo_conn.get_collections(), on_change=lambda item: update_add_one_card(item.value)
                ).classes("w-full bg-gray-200 shadow-lg text-lg")
            ui.button(text="ADD", on_click=add_one_item, color="green")

        add_one_fields_card = ui.card()

        def update_add_one_card(value):
            current_add_one_fields.clear()
            current_add_one_fields_enums.clear()
            add_one_fields_card.clear()
            with add_one_fields_card:
                for field in fields_cache[value]:
                    with ui.row():
                        if field != "_id":
                            this_add_one_field = ui.input(label=field)
                            current_add_one_fields[this_add_one_field.id] = this_add_one_field
                            current_add_one_fields_enums[this_add_one_field.id] = field
            add_one_fields_card.update()
            return

    # Set up the "Add Bulk" tab environment
    with ui.tab_panel(add_bulk_tab) as bulk_tab_panel:
        with open(Path(src_dir / "bulk_import.md"), "r") as bulk_import_readme_file:
            bulk_import_markdown_content = bulk_import_readme_file.read()

        def upload_bulk_items():
            global bulk_upload_file
            if bulk_upload_file is not None:
                ui.notify("File uploaded, now sending to MongoDB")
            else:
                ui.notify("No file uploaded, please select a file")
            return

        def reset_bulk_tab_panel():
            global bulk_upload_file
            bulk_upload_file = None
            bulk_tab_panel.clear()
            with bulk_tab_panel:
                ui.markdown(bulk_import_markdown_content)
                with ui.row():
                    ui.upload(label="SELECT YOUR FILE", on_upload=add_bulk_items)
                    ui.button(
                        text="RESET",
                        on_click=reset_bulk_tab_panel,
                        color="orange",
                    )
                    ui.button(text="CONFIRM UPLOAD", on_click=upload_bulk_items, color="green")

        def df_to_table(input_df: pd.DataFrame):
            return_columns = []
            return_rows = []

            df_head = input_df.head(n=10)

            for col in input_df.columns:
                return_columns.append(
                    {
                        "name": col,
                        "label": col,
                        "field": col,
                    }
                )
            if not input_df.empty:
                return_rows = df_head.to_dict(orient="records")

            return return_columns, return_rows

        def add_bulk_items(e: events.UploadEventArguments):
            if e.content is not None:
                global bulk_upload_file
                bulk_upload_file = e.content.read()
                mocked_excel_file = BytesIO(bulk_upload_file)
                bulk_excel = pd.read_excel(mocked_excel_file, sheet_name=None)
                with bulk_tab_panel:
                    ui.label(f"File Uploaded: {e.name}")
                    for sheet_name, df in bulk_excel.items():
                        ui.label(f"Sheet: {sheet_name}")
                        columns, rows = df_to_table(df)
                        ui.table(columns=columns, rows=rows)

        ui.markdown(bulk_import_markdown_content)
        with ui.row():
            ui.upload(label="SELECT A FILE!", on_upload=add_bulk_items)
            ui.button(text="RESET", on_click=reset_bulk_tab_panel, color="orange")
            ui.button(text="CONFIRM UPLOAD", on_click=upload_bulk_items, color="green")

    # Set up the "Search" tab environment
    with ui.tab_panel(search_tab):
        ui.label("Search text")

    # Set up the "Delete" tab environment
    with ui.tab_panel(delete_tab):
        ui.label("Delete text")

ui.run()
