from functools import wraps
from flask import redirect, render_template, request, session
import csv
import datetime
import os

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def create_csv(csv_filename):
    csv_filename = os.path.join('data', csv_filename + '.csv')

    # Create empty CSV file with header row
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Time', 'Text', 'User ID'])
# create_csv("my_data")

def write_to_csv(csv_filename, row_data):
    csv_filename = os.path.join('data', csv_filename + '.csv')

    # Write row data to CSV file
    with open(csv_filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(row_data)
# write_to_csv("my_data", ['2023-05-05 10:30:00', 'Hello, world!', '123'])

def delete_csv(csv_filename):
    csv_filename = os.path.join('data', csv_filename + '.csv')  # Add .csv extension
    if os.path.exists(csv_filename):
        os.remove(csv_filename)
    else:
        print(f"The file {csv_filename} does not exist.")
# delete_csv("my_data")

def user_name(user_id, db):
    user_data = db.execute("SELECT name, surname FROM users_info WHERE id = ?", user_id)
    if user_data:
        name = user_data[0]["name"] + " " + user_data[0]["surname"]
        return(name)
    else:
        return "User data not found."