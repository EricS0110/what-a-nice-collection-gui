# What is bulk importing?

This page will process bulk imports of items into collections from an __EXCEL (.xlsx)__ file input.

The recommended Excel file can have multiple sheets, with each sheet being named with the intended collection.
The first row of the sheet should include the name of the field for the data in that column.  For an example, see
the table below!

| Title                | Author           | Genre           | Condition   |
|----------------------|------------------|-----------------|-------------|
| Lord of the Flies    | William Golding  | Fiction         | New         |
| Ender's Game         | Orson Scott Card | Science Fiction | Good        |
| A Tale of Two Cities | Charles Dickens  | Fiction         | Worn        |

And the sheet this data is contained in could be named 'books' or 'Books' or 'BOOKS'.  The casing of the collection
name is not important, as this application will cast it to lower case to have some element of consistency to check
if the collection name exists already as a destination for the data in the sheet.

Once you have selected your file, click the import icon (cloud with up arrow) and this will prepare your dataset for
upload to MongoDB.  A preview of the data you have selected will be shown, with each sheet being capped at 10 rows for
readability.  If this data looks like you were expecting, click on the
<span style="color: green;">__CONFIRM UPLOAD__</span> button.  If the data does not look correct, or you want to check a
different file, you can click the <span style="color: orange;">__RESET__</span> button to clear the upload state and any
generated previews.

Please note that the application currently expects an Excel file without any validation.  This will come, but please
understand the behavior of the app will vary (and probably crash) if you do not upload
an __Excel (.xlsx, .xlsm, .xls)__ file.
