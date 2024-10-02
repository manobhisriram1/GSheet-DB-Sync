
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import mysql.connector
import time
from datetime import datetime

# MySQL Database setup
db = mysql.connector.connect(
    host="localhost",
    user="root",  # Replace with  MySQL username
    password="Manu@123",  # Replace with  MySQL password
    database="new_db"  # Update this with  database name
)
cursor = db.cursor()

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open("Sheet-DB Sync").sheet1  # Open the first sheet as our data is in the sheet1 


def sync_to_database():
    # Fetch data from the Google Sheet
    rows = sheet.get_all_records()
    google_data = {row['Name']: row for row in rows}

    # Fetch existing data from the database
    cursor.execute("SELECT id, name, age, city, occupation FROM cust")
    db_data = cursor.fetchall()
    db_data_dict = {(name, age, city, occupation): id for (id, name, age, city, occupation) in db_data}

    # Insert or update data
    for row in google_data.values():
        name = row['Name']
        age = row['Age'] if row['Age'] != '' else None  # Set age to None if empty
        city = row['City']
        occupation = row['Occupation']
        
        # Check for empty values
        if not name or age is None or not city or not occupation:
            continue  # Skip this row if any of the required fields are empty

        # Check if the combination of name, age, city, and occupation already exists
        if (name, age, city, occupation) in db_data_dict:
            # Update existing data
            update_query = "UPDATE cust SET last_modified=%s WHERE id=%s"
            cursor.execute(update_query, (datetime.now(), db_data_dict[(name, age, city, occupation)]))
            db.commit()
        else:
            # Insert new data with a manually specified id
            cursor.execute("SELECT MAX(id) FROM cust")
            max_id = cursor.fetchone()[0]
            new_id = (max_id + 1) if max_id is not None else 1  # Manually set the next id
            insert_query = "INSERT INTO cust (id, name, age, city, occupation) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (new_id, name, age, city, occupation))
            db.commit()

    # Handle deletions
    for key in db_data_dict.keys():
        if key[0] not in google_data:  # Check by name only for deletion
            # Replace with a placeholder
            delete_query = "DELETE FROM cust WHERE name=%s"
            cursor.execute(delete_query, (key[0],))
            db.commit()

def sync_to_google_sheet():
    cursor.execute("SELECT name, age, city, occupation FROM cust")
    all_users = cursor.fetchall()

    # Clear existing data in the Google Sheet (except headers)
    sheet.clear()
    sheet.append_row(["Name", "Age", "City", "Occupation"])  # Re-add the headers

    # Append each user to Google Sheet
    for user in all_users:
        sheet.append_row(user)

    print(f"Total customers in the database: {len(all_users)}")

def main():
    while True:
        # Sync from Google Sheets to Database
        sync_to_database()

        # Sync from Database to Google Sheets
        sync_to_google_sheet()

        # Wait for a specified time before the next sync
        time.sleep(60)  # Adjust the interval as needed

if __name__ == "__main__":
    main()

 