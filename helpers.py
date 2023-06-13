from functools import wraps
from flask import redirect, session

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

def user_name(user_id, db):
    user_data = db.execute("SELECT name, surname FROM users_info WHERE id = ?", user_id)
    if user_data:
        name = user_data[0]["name"] + " " + user_data[0]["surname"]
        return(name)
    else:
        return "User data not found."
    
def new_msg_check(group_id, db, count):
    count1 = db.execute("SELECT COUNT(message) AS count FROM messages WHERE group_id = ?", group_id)
    msg_count = count1[0]['count']
    msg_count1 = int(count)
    print(msg_count, msg_count1)
    if msg_count > msg_count1:
        msg_count1 = msg_count
        return True
    else:
        return False
    
def vote_check(group_id, db):
    vote_status1 = db.execute("SELECT vote FROM groups WHERE group_id = ?", group_id)
    vote_status = vote_status1[0]['vote']

    if vote_status is 0:
        return False
    elif vote_status is 1:
        return True
    else:
        return(KeyError)