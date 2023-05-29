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

def format_sql_time(group_time):

    date_value = group_time[0]['date']
    time_value = group_time[0]['end_time']
    date_datetime = datetime.strptime(date_value, "%Y-%m-%d")
    end_time_datetime = datetime.strptime(time_value, "%H:%M:%S")

    # Format the datetime objects to match the desired format
    formatted_date = date_datetime.strftime("%Y-%m-%d")
    formatted_end_time = end_time_datetime.strftime("%H:%M")

    # Concatenate the formatted date and end_time
    formatted_datetime = f"{formatted_date} / {formatted_end_time}"

    return(formated_datetime)

# SELECT users_info.id, users_info.name, users_info.surname, users_info.city, users_info.lang1, user_groups.group_id, user_groups.status, groups.name
# FROM users_info JOIN user_groups ON users_info.id = user_groups.user_id JOIN groups ON user_groups.group_id = groups.group_id
# WHERE user_groups.group_id IN (SELECT group_id FROM user_groups WHERE user_id = 1 AND creator = 1)