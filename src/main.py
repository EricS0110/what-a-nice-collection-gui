from io import BytesIO
from pathlib import Path

import pandas as pd
from bson import ObjectId
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
bulk_upload_data = None  # store the data from the bulk upload file
available_collections_label = None  # refreshable available collections list
confirm_upload_button = None  # enable/disable bulk upload confirm button
search_collection_picked = ""  # store the collection picked for search
search_field_picked = ""  # store the field picked for search
search_results_data = []  # store the results of the search
delete_from_collection = ""  # store the collection picked for deletion method
delete_id = ""  # store the ID of the item to delete

# Get a MongoDB connection instance
mongo_conn = MongoConnection(settings)

# Set up the list of available collections
available_collections = mongo_conn.get_collections()  # List[str]
available_collections_str = ", ".join(mongo_conn.get_collections())  # Single string of comma-sep values

# Set up or update the cache of available fields for each collection
mongo_conn.update_fields_cache()
fields_cache = mongo_conn.read_fields_cache()

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

    def check_new_item():
        global add_item_button
        these_fields = current_add_one_fields
        these_fields_enums = current_add_one_fields_enums
        item_data = {}
        check_label_string = "Please verify item...\n\n"
        for k, v in these_fields_enums.items():
            input_value = these_fields[k].value
            if input_value != "":
                item_data[v] = these_fields[k].value
                check_label_string += f"{v}: {these_fields[k].value} \n\n"
                # ui.notify(f"{v}: {these_fields[k].value}")
        add_one_check_label.set_content(check_label_string)
        add_item_button.enable()

    def add_one_item():
        global add_item_button
        ui.notify("Adding item...")
        this_collection = collection_selection.value
        these_fields = current_add_one_fields
        these_fields_enums = current_add_one_fields_enums
        item_data = {}
        for k, v in these_fields_enums.items():
            input_value = these_fields[k].value
            if input_value != "":
                item_data[v] = these_fields[k].value
        mongo_conn.add_item(this_collection, item_data)
        ui.notify(f"Item added to {this_collection}")
        add_one_check_label.set_content("Enter next item details if desired...")
        add_item_button.disable()
        return

    with ui.tab_panel(add_one_tab):
        ui.markdown("# Add One Item")
        ui.separator()
        with ui.row():
            with ui.column():
                with ui.row():
                    with ui.card():
                        ui.markdown("### Select a collection:")
                        collection_selection = ui.select(
                            options=mongo_conn.get_collections(), on_change=lambda item: update_add_one_card(item.value)
                        ).classes("w-full bg-gray-200 shadow-lg text-lg")
                    with ui.column():
                        ui.button(text="Check", on_click=check_new_item, color="orange")
                        add_item_button = ui.button(text="ADD", on_click=add_one_item, color="green")
                        add_item_button.disable()

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
                    add_item_button.disable()
                    return

            with ui.column():
                add_one_check_label = ui.markdown("Please select a collection to begin...")

    # Set up the "Add Bulk" tab environment
    with ui.tab_panel(add_bulk_tab) as bulk_tab_panel:
        with open(Path(src_dir / "bulk_import.md"), "r") as bulk_import_readme_file:
            bulk_import_markdown_content = bulk_import_readme_file.read()

        def upload_bulk_items():
            global bulk_upload_data
            global bulk_upload_file
            if bulk_upload_file is not None:
                ui.notify("File loaded, now sending to MongoDB")
                mongo_conn.upload_bulk(bulk_upload_data)
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
                    global confirm_upload_button
                    if confirm_upload_button is not None:
                        confirm_upload_button = ui.button(
                            text="CONFIRM UPLOAD", on_click=upload_bulk_items, color="green"
                        )
                    confirm_upload_button.disable()

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
            global bulk_upload_data
            global bulk_upload_file
            if e.content is not None:
                if confirm_upload_button is not None:
                    confirm_upload_button.enable()
                bulk_upload_file = e.content.read()
                mocked_excel_file = BytesIO(bulk_upload_file)
                bulk_excel = pd.read_excel(mocked_excel_file, sheet_name=None)
                with bulk_tab_panel:
                    ui.label(f"File Uploaded: {e.name}")
                    for sheet_name, df in bulk_excel.items():
                        ui.label(f"Sheet: {sheet_name}")
                        columns, rows = df_to_table(df)
                        ui.table(columns=columns, rows=rows)
                bulk_upload_data = bulk_excel

        ui.markdown(bulk_import_markdown_content)
        with ui.row():
            ui.upload(label="SELECT A FILE!", on_upload=add_bulk_items)
            ui.button(text="RESET", on_click=reset_bulk_tab_panel, color="orange")
            # noinspection PyRedeclaration
            confirm_upload_button = ui.button(text="CONFIRM UPLOAD", on_click=upload_bulk_items, color="green")
            confirm_upload_button.disable()

    # Set up the "Search" tab environment
    current_search_fields = {}
    current_search_fields_enums = {}

    with ui.tab_panel(search_tab):
        with ui.row():
            with ui.column():
                with ui.card():
                    ui.markdown("### Select a collection:")
                    search_collection_select = ui.select(
                        options=mongo_conn.get_collections(), on_change=lambda item: update_search_card(item.value)
                    ).classes("w-full bg-gray-200 shadow-lg text-lg")
                    ui.markdown("#### Select a field to search:")
                    search_fields = ui.select(
                        options=["Select a collection first"], on_change=lambda item: prepare_search(item.value)
                    ).classes("w-full bg-gray-200 shadow-lg text-lg")
                    search_fields.disable()
                    ui.markdown("##### Enter the search value:")
                    search_value_input = ui.input(label="Search Value")

                    def search_df_to_table(input_df: pd.DataFrame):
                        return_columns = []
                        return_rows = []

                        for col in input_df.columns:
                            return_columns.append(
                                {
                                    "name": col,
                                    "label": col,
                                    "field": col,
                                }
                            )
                        if not input_df.empty:
                            return_rows = input_df.to_dict(orient="records")

                        for row in return_rows:
                            for key, value in row.items():
                                if isinstance(value, ObjectId):
                                    row[key] = str(value)

                        return return_columns, return_rows

                    def update_search_card(value):
                        global search_collection_picked
                        global search_fields
                        current_search_fields.clear()
                        current_search_fields_enums.clear()
                        search_collection_picked = value
                        search_options = [item for item in fields_cache[value] if item != "_id"]
                        search_fields.set_options(search_options)
                        search_fields.enable()
                        return

                    def prepare_search(value):
                        global search_button
                        global search_field_picked
                        search_button.enable()
                        search_field_picked = value

                    def search_collection_items():
                        global search_collection_picked
                        global search_field_picked
                        global search_results_data
                        global search_results_table
                        search_collection_value = search_collection_picked
                        search_field_value = search_field_picked
                        search_value = search_value_input.value
                        search_results_data = []
                        if (
                            (search_value is not None)
                            and (search_collection_value != "")
                            and (search_field_value != "")
                        ):
                            search_results_data = mongo_conn.search_collection(
                                search_collection_value, search_field_value, search_value
                            )
                            search_results_df = pd.DataFrame(search_results_data)
                            res_cols, res_rows = search_df_to_table(search_results_df)
                            search_results_table.columns = res_cols
                            search_results_table.rows = res_rows
                        else:
                            ui.notify("Please enter a search value")
                        return

                search_button = ui.button(text="SEARCH", color="green", on_click=search_collection_items)
                search_button.disable()
            with ui.column().classes("w-full"):
                ui.markdown("#### Search Results:")
                search_results_table = ui.table(columns=[], rows=[])

    # Set up the "Delete" tab environment
    with ui.tab_panel(delete_tab):

        def update_delete_collection(value):
            global delete_from_collection
            delete_from_collection = value
            delete_id_input.enable()
            return

        def verify_delete():
            global delete_button
            global delete_check_table
            global delete_id

            delete_id = delete_id_input.value
            delete_check_results = mongo_conn.search_collection(delete_from_collection, "_id", delete_id)
            if not delete_check_results:
                ui.notify(f"No item found with ID: {delete_id}")
            else:
                delete_check_df = pd.DataFrame(delete_check_results)
                delete_check_cols, delete_check_rows = search_df_to_table(delete_check_df)
                delete_check_table.columns = delete_check_cols
                delete_check_table.rows = delete_check_rows
                delete_button.enable()
            return

        def delete_item_click():
            global delete_button
            global delete_check_table
            global delete_from_collection
            global delete_id
            mongo_conn.delete_item(delete_from_collection, delete_id)
            ui.notify(f"{delete_id} has been deleted from {delete_from_collection}")
            delete_button.disable()
            delete_check_table.columns = []
            delete_check_table.rows = []
            return

        with open(Path(src_dir / "delete_readme.md"), "r") as delete_readme_file:
            delete_readme_md = delete_readme_file.read()
        ui.markdown(delete_readme_md)
        with ui.row():
            # Left Space
            with ui.column():
                with ui.card():
                    ui.markdown("### Select a collection:")
                    delete_from_collection_select = ui.select(
                        options=mongo_conn.get_collections(),
                        on_change=lambda item: update_delete_collection(item.value),
                    ).classes("w-full bg-gray-200 shadow-lg text-lg")
                    delete_id_input = ui.input(label="Item ID:").classes("w-full")
                    delete_id_input.disable()
            # Middle Space
            with ui.column():
                verify_delete_button = ui.button(text="VERIFY", color="orange", on_click=verify_delete)
                delete_button = ui.button(text="DELETE", color="red", on_click=delete_item_click)
                delete_button.disable()
            # Right Space
            with ui.column():
                delete_check_table = ui.table(columns=[], rows=[])

ui.run()
