import os
import uuid
import sqlite3
from datetime import datetime
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, flash, redirect, render_template, request, session, jsonify, url_for, Response
from flask_session import Session
from helpers import login_required, user_name, new_msg_check, vote_check


# Configure application
app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///DATABASE/database.db")

if __name__ == '__main__':
    app.run(host='192.168.75.105')

@app.route("/")
def start():
    # first page that user sees if not alredy loged in

    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")

    else:
        username = request.form.get("username")
        password = request.form.get("psw")
        confirmation = request.form.get("psw-repeat")

        if password != confirmation:
            flash("PASSWORD != CONFIRMATION PASSWORD")

        my_hash = generate_password_hash(password)

        try:
            new_user = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, my_hash))
        except sqlite3.Error as e:
            print("Error occurred while inserting user:", e)
            return False

        session["user_id"] = new_user

        db.execute("INSERT INTO users_info (id, username) VALUES (?, ?)", new_user, username)
        db.execute("INSERT INTO images (user_id) VALUES (?)", new_user)
        db.execute("INSERT INTO ratings (skill, skill_count, fairplay, fairplay_count, friendliness, friendliness_count, id) VALUES (?, ?, ?, ?, ?, ?, ?)", 1, 1, 1, 1, 1, 1, new_user)
        return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        username = request.form.get("username")
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("psw")):
            flash("Invalid username and/or password", 403)
            return render_template("login.html")
        else:
            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]

            # Remember user's choice to stay logged in
            if request.form.get("remember"):
                session.permanent = True

            # Redirect user to home page
            return redirect("/user_interface")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")




@app.route("/user_interface", methods=["GET", "POST"])
@login_required
def user_interface():
    # first page that user sees if not alredy loged in
    user_id = session.get("user_id")

    # get name
    name = user_name(user_id, db)

    # get user img
    img_path = db.execute('SELECT filepath FROM images WHERE user_id = ?', user_id)
    img = img_path[0]["filepath"]

    return render_template("user_interface.html", name=name, img=img)

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/create_group", methods=["GET", "POST"])
@login_required
def create_group():
    if request.method == "POST":
        # Get group name, sport, location, time, creator_info and send requests to users for joining
        group_name = request.form.get("group_name") # name
        # creator_info
        creator_id = session.get("user_id")
        creator_name = db.execute("SELECT name || ' ' || surname AS name, username FROM users_info WHERE id = ?", creator_id)
        if not creator_name[0]['name'] or creator_name[0]['name'].strip() == '':
            creator_name = creator_name[0]['username']
        else:
            creator_name = creator_name[0]['name']

        selected_user_ids = request.form["selected_users"].split(",")  # create list of users you wont to send requests

        sport = request.form.get("sport") # sport

        latitude = request.form.get("latitude") # location
        longitude = request.form.get("longitude")

        lang = request.form.get("lang") # speaking language

        start_time = request.form.get("start-time") # time and date
        end_time = request.form.get("end-time")
        date = request.form.get("date")
        date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%y")

        size = request.form.get("size") # size

        user_ids = [] # empty tuple for users ids that we wont to send request to

        unique_filename = f"{uuid.uuid4().hex}"

        for user_id in selected_user_ids: # puting users ids in empty tuple
            user_ids.append(user_id)

        # Create the group and adding info
        db.execute("INSERT INTO groups (name, code, language, sport, location_lati, location_long, date, size, start_time, end_time, creator_id, creator_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", group_name, unique_filename, lang, sport, latitude, longitude, date, size, start_time, end_time, creator_id, creator_name)
        group_id = db.execute("SELECT group_id FROM groups WHERE code = ?", unique_filename)
        group_id = group_id[0]["group_id"]
        # adding requests to group system
        for user_id in user_ids:
            db.execute("INSERT INTO user_groups (user_id, group_id, send) VALUES (?, ?, 0)", user_id, group_id)
        # adding a creator in group system and vote system
        db.execute("UPDATE user_groups SET creator = 1, status = 1 WHERE user_id = ?", creator_id)
        db.execute("INSERT INTO votes (group_id, voter_id, member_id, voted) VALUES (?, ?, ?, 1)", group_id, creator_id, creator_id)


        flash("Group created successfully!")
        return redirect("/user_interface")

    else:
        user_id = session.get("user_id")
        name = user_name(user_id, db)  
        return render_template("create_group.html", user_id=user_id, name=name)
        
@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    user_id = session.get("user_id")
    name = user_name(user_id, db)
    data = db.execute("SELECT name, surname, city, state, filepath, lang1, lang2 FROM users_info JOIN images ON users_info.id = images.user_id WHERE id = ?", user_id)

    if request.method == "GET":
        return render_template("edit_profile.html", data=data, name=name)
    else:
        # Get the uploaded file and user ID
        user_id = session.get("user_id")
        file = request.files['filename']
        print(file)
        if file.filename == '':
            pass
        else:
            # Get the current filepath from the database
            current_filepath = db.execute("SELECT filepath FROM images WHERE user_id = ?", user_id)
            if current_filepath is not None:
                filepath = current_filepath[0]['filepath']
                if os.path.exists(filepath):
                    # Delete the old file
                    os.remove(filepath)
                else:
                    pass

            # Generate a unique filename for the uploaded file
            filename, ext = os.path.splitext(file.filename)
            filename = f"{uuid.uuid4().hex}{ext}"

            # Move the uploaded file to the images directory
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Store the file path and user ID in the database
            db.execute('UPDATE images SET filename = ?, filepath = ? WHERE user_id = ?', filename, path, user_id)

        # Get form data
        name = request.form.get('firstname')
        surname = request.form.get('surename')
        city = request.form.get('city')
        state = request.form.get('state')
        lang1 = request.form.get('lang1')
        lang2 = request.form.get('lang2')
        abouty = request.form.get('info')

        update_query = 'UPDATE users_info SET'
        params = []

        if name:
            update_query += ' name = ?,'
            params.append(name)
        else:
            pass
        if surname:
            update_query += ' surname = ?,'
            params.append(surname)
        else:
            pass
        if abouty:
            update_query += ' info = ?,'
            params.append(abouty)
        else:
            pass
        if city:
            update_query += ' city = ?,'
            params.append(city)
        else:
            pass
        if state:
            update_query += ' state = ?,'
            params.append(state)
        else:
            pass
        if lang1:
            update_query += ' lang1 = ?,'
            params.append(lang1)
        else:
            pass
        if lang2:
            update_query += ' lang2 = ?,'
            params.append(lang2)
        else:
            pass
        # Remove the trailing comma from the query
        update_query = update_query.rstrip(',')

        # Append the WHERE clause
        update_query += ' WHERE id = ?'
        params.append(user_id)

        # Execute the update query with the provided parameters
        db.execute(update_query, *params)

        flash('User information saved successfully!')

        return redirect("/profile")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    
    user_id = session.get("user_id")
    name = user_name(user_id, db)
    users_info = db.execute("SELECT users_info.id AS id, name, surname, info, state, city, lang1, filepath, skill / skill_count AS skill, fairplay / fairplay_count AS fairplay, friendliness / friendliness_count AS friendliness FROM users_info JOIN images ON users_info.id = images.user_id JOIN ratings ON users_info.id = ratings.id  WHERE users_info.id = ? ;", user_id)

    return render_template('profile.html', data=users_info, name=name)




@app.route("/lobbies", methods=["GET", "POST"])
@login_required
def lobbies():
    user = session.get("user_id")
    join_requests = db.execute("SELECT groups.*, user_counts.user_count FROM groups JOIN user_groups ON groups.group_id = user_groups.group_id JOIN (SELECT user_groups.group_id, SUM(CASE WHEN user_groups.status = 1 THEN 1 ELSE 0 END) || '/' || groups.size AS user_count FROM user_groups JOIN groups ON user_groups.group_id = groups.group_id WHERE user_groups.group_id IN (SELECT group_id FROM user_groups WHERE user_id = ?) GROUP BY user_groups.group_id) AS user_counts ON groups.group_id = user_counts.group_id WHERE user_groups.user_id = ? AND user_groups.status = 0 AND user_groups.send = 0", user, user )
    sent_requests = db.execute("SELECT users_info.id, users_info.name || ' ' || users_info.surname AS name, users_info.city, users_info.lang1, user_groups.group_id, user_groups.status, groups.name AS group_name, user_groups.send FROM users_info JOIN user_groups ON users_info.id = user_groups.user_id JOIN groups ON user_groups.group_id = groups.group_id WHERE user_groups.group_id IN (SELECT group_id FROM user_groups WHERE user_id = ? AND creator = 1) AND user_groups.send = 2 AND user_groups.status = 0", user)
    groups_names = db.execute("SELECT groups.* , SUM(CASE WHEN user_groups.status = 1 THEN 1 ELSE 0 END) || '/' || groups.size AS user_count, groups.start_time || 'h - ' || groups.end_time || 'h ' || groups.date AS time FROM groups JOIN user_groups ON groups.group_id = user_groups.group_id  WHERE groups.group_id IN (SELECT group_id FROM user_groups WHERE user_id = ? AND status = 1) GROUP BY groups.group_id;", user)
    name = user_name(user, db)
    return render_template('lobbies.html', groups=groups_names, requests=join_requests, sent_requests=sent_requests, name=name)

@app.route("/lobby", methods=["GET", "POST"])
@login_required
def lobby():
    user = session.get("user_id")
    group_id = request.args.get('group_id')
    group_name = request.args.get('group_name')
    name = user_name(user, db)
    check = vote_check(group_id, db)
    votes = db.execute("SELECT * FROM votes WHERE group_id = ? AND voter_id = ? ORDER BY voter_id", group_id, user)
    users_info = db.execute("SELECT users_info.id AS id, group_id, name, surname, state, city, lang1, filepath, skill / skill_count AS skill, fairplay / fairplay_count AS fairplay, friendliness / friendliness_count AS friendliness, creator FROM users_info JOIN user_groups ON users_info.id = user_groups.user_id JOIN images ON users_info.id = images.user_id JOIN ratings ON users_info.id = ratings.id  WHERE user_groups.group_id = ? ;", group_id)
    users_info.sort(key=lambda x: x['id'] != user)
    group_info = db.execute("SELECT groups.* , SUM(CASE WHEN user_groups.status = 1 THEN 1 ELSE 0 END) || '/' || groups.size AS user_count, groups.start_time || 'h - ' || groups.end_time || 'h ' || groups.date AS time FROM groups JOIN user_groups ON groups.group_id = user_groups.group_id  WHERE groups.group_id= ?;", group_id)
    group_time = db.execute("SELECT date, end_time FROM groups WHERE group_id = ?", group_id)
    date_value = group_time[0]['date']
    end_time_value = group_time[0]['end_time']
    # Combine the date and end_time into a single datetime object
    group_datetime = datetime.strptime(f"{date_value} {end_time_value}", "%d.%m.%y %H:%M")
    current_datetime = datetime.now()
    formatted_datetime = datetime.strptime(current_datetime.strftime("%d.%m.%y %H:%M"), "%d.%m.%y %H:%M")
    time = False
    if group_datetime < formatted_datetime:
        time = True
    print(time)
    print(group_datetime)
    print(formatted_datetime)
    return render_template('lobby.html', group_name=group_name, users=users_info, user=user, votes=votes, group_id=group_id, group_info=group_info, time_check=time, name=name, check=check)

@app.route("/user_profile", methods=["GET", "POST"])
@login_required
def user_profile():


    user_id = request.args.get('data-user-id')

    users_info = db.execute("SELECT users_info.id AS id, name, surname, state, city, lang1, filepath, skill / skill_count AS skill, fairplay / fairplay_count AS fairplay, friendliness / friendliness_count AS friendliness FROM users_info JOIN images ON users_info.id = images.user_id JOIN ratings ON users_info.id = ratings.id  WHERE users_info.id = ? ;", user_id)

    return render_template('profile.html', data=users_info)

@app.route("/vote", methods=["POST"])
@login_required
def vote():

    user = session.get("user_id")
    group_id = request.form['group_id']
    member_id = request.form['form']
    skill = request.form['skill_vote']
    fairplay = request.form['fairplay_vote']
    friendliness = request.form['friendliness_vote']
    db.execute("UPDATE ratings SET skill = skill + ?, skill_count = skill_count + 1, fairplay = fairplay + ?, fairplay_count = fairplay_count + 1, friendliness = friendliness + ?, friendliness_count = friendliness_count + 1 WHERE id = ?;", skill, fairplay, friendliness, member_id)
    db.execute("UPDATE votes SET voted = 1 WHERE group_id = ? AND voter_id = ? AND member_id = ?", group_id, user, member_id)
    return redirect(request.referrer or url_for('lobby'))

@app.route("/delete_group", methods=["GET", "POST"])
@login_required
def delete_group():

    user = session.get("user_id")
    group_id = request.form.get("group_id")
    users_groups = db.execute("SELECT * FROM user_groups WHERE user_id = ? AND group_id = ? AND creator = 1", user, group_id)
    csv_file_data = db.execute("SELECT code FROM groups WHERE group_id = ?", group_id)
    csv_file = csv_file_data[0]["code"]
    print(csv_file)

    if any(user_row['user_id'] == user for user_row in users_groups):
        db.execute("DELETE FROM votes WHERE group_id = ?", group_id)
        db.execute("DELETE FROM user_groups WHERE group_id = ?", group_id)
        db.execute("DELETE FROM groups WHERE group_id = ?", group_id)
        db.execute("DELETE FROM messages WHERE group_id = ?", group_id)

    flash("Lobby deleted successfully!")
    return redirect("/user_interface")

@app.route("/lo_lobbies", methods=["GET", "POST"])
@login_required
def lo_lobbies():
    user = session.get("user_id")
    name = user_name(user, db)
    groups = db.execute("SELECT groups.group_id AS id, groups.name, COUNT(user_groups.user_id) AS user_count, sport, language, location_lati, location_long, start_time || 'h - ' || end_time || 'h ' || date AS time FROM groups JOIN user_groups ON groups.group_id = user_groups.group_id WHERE groups.group_id NOT IN (SELECT group_id FROM user_groups WHERE user_id = ? AND status = 1) GROUP BY groups.group_id, groups.name;", user)

    return render_template('lo_lobbies.html', data=groups, name=name)

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    query = request.form['query']
    group_id = request.form.get('group_id', None)
    users = request.form.get('selected_users')
    user_ids = users.split(",") if users else []

    # Connect to your SQLite database
    conn = sqlite3.connect('DATABASE/database.db')
    cursor = conn.cursor()

    # Execute the SQL query to search for users based on the query
    if group_id is None:
        cursor.execute("""SELECT users_info.id AS id, name, surname, state, city, skill / skill_count AS skill, fairplay / fairplay_count AS fairplay, friendliness / friendliness_count AS friendliness, filepath AS img FROM users_info JOIN ratings ON users_info.id = ratings.id JOIN images ON users_info.id = images.user_id WHERE name LIKE ? AND users_info.id NOT IN ({})""".format(','.join('?' * len(user_ids))), ('%' + query + '%', *user_ids))
        results = cursor.fetchall()
    else:
        cursor.execute("SELECT users_info.id AS id, name, surname, state, city, skill / skill_count AS skill, fairplay / fairplay_count AS fairplay, friendliness / friendliness_count AS friendliness, filepath AS img FROM users_info JOIN ratings ON users_info.id = ratings.id JOIN images ON users_info.id = images.user_id WHERE name LIKE ? AND users_info.id NOT IN (SELECT user_id FROM user_groups WHERE group_id = ?)", ('%' + query + '%', group_id ))
        results = cursor.fetchall()
    # Close the database connection
    conn.close()

    # Return the results as JSON
    return jsonify(results)

@app.route("/settings_group", methods=["GET", "POST"])
@login_required
def settings_group():

    if request.method == "POST":
        group_id = request.args.get('group_id')
        group_name = request.args.get('group_name')
        user_id = session.get("user_id")
        print("name", group_name)
        selected_user_ids = request.form["selected_users"].split(",")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        user_ids = []

        for user_id in selected_user_ids:
            user_ids.append(user_id)

        db.execute("UPDATE groups SET location_lati = ?, location_long = ? WHERE group_id = ?", latitude, longitude, group_id)

        for user_id in user_ids:
            db.execute("INSERT INTO user_groups (user_id, group_id, send) VALUES (?, ?, 1)", user_id, group_id)


        flash("Settings changed successfully!")
        return redirect("/lobby?group_id=" + group_id + "&group_name=" + group_name)

    else:
        group_id = request.args.get('group_id')
        group_name = request.args.get('group_name')
        group_info = db.execute("SELECT * FROM groups WHERE group_id = ?", group_id)
        return render_template("settings_group.html", group_id=group_id, group_name=group_name, group_info=group_info)

@app.route("/join_request", methods=["GET", "POST"])
@login_required
def join_request():

    user_id = session.get("user_id")
    group_id = request.args.get('group_id')
    request_id = request.args.get('user_id')
    if request_id:
        db.execute("UPDATE user_groups SET status = 1 WHERE group_id = ? AND user_id = ?", group_id, request_id)
        db.execute("INSERT INTO votes (group_id, voter_id, member_id, voted) VALUES (?, ?, ?, 1)", group_id, request_id, request_id)
        flash("User added!")
    else:
        group_users = db.execute("SELECT user_id FROM user_groups WHERE group_id = ? AND status = 0", group_id)
        user_ids = [user['user_id'] for user in group_users]
        if user_id in user_ids:
            db.execute("INSERT INTO votes (group_id, voter_id, member_id, voted) VALUES (?, ?, ?, 1)", group_id, user_id, user_id)
            db.execute("UPDATE user_groups SET status = 1 WHERE group_id = ? AND user_id = ?", group_id, user_id)
            flash("You have been added to the group!")
        else:
            db.execute("INSERT INTO user_groups (user_id, group_id, status, send) VALUES (?, ?, 0, 2)", user_id, group_id)
            flash("Your request has been sent!")
    return redirect(request.referrer or url_for('lobby'))

@app.route("/delete_request", methods=["GET", "POST"])
@login_required
def delete_request():

    user_id = session.get("user_id")
    group_id = request.args.get('group_id')
    request_id = request.args.get('user_id')
    if request_id:
        db.execute("DELETE FROM user_groups WHERE user_id = ? AND group_id = ?", request_id, group_id)
        flash("Request has been deleted!")
    else:
        db.execute("DELETE FROM user_groups WHERE user_id = ? AND group_id = ?", user_id, group_id)
        flash("Request has been deleted!")
    return redirect(request.referrer or url_for('lobbies'))

@app.route("/start_voting", methods=["GET", "POST"])
@login_required
def start_voting():
    group_id = request.args.get('group_id')
    user_ids = db.execute("SELECT user_id FROM user_groups WHERE group_id = ? AND status = 1", group_id)
    vote_status1 = db.execute("SELECT vote FROM groups WHERE group_id = ?", group_id)
    vote_status = vote_status1[0]['vote']
    if vote_status == 0:
        db.execute("UPDATE groups SET vote = 1 WHERE group_id = ?", group_id)
        for user_id in user_ids:
            db.execute("INSERT INTO user_history (name, code, sport, location_lati, location_long, time, ?) SELECT name, code, sport, location_lati, location_long, date || ' ' || start_time AS time FROM groups WHERE group_id = ?", user_id, group_id)
            for user in user_ids:
                if user == user_id:
                    pass
                else:
                    db.execute("INSERT INTO votes (group_id, voter_id, member_id) VALUES (?, ?, ?)", group_id, user_id['user_id'], user['user_id'])
   
    return redirect(request.referrer or url_for('lobby'))

@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    if request.method == "POST":
        group_id = request.form.get('group_id')
        message = request.form.get('message')
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%H:%M %d.%m.%Y")
        user_id = session.get("user_id")
        db.execute("INSERT INTO messages (group_id, user_id, message, datetime) VALUES (?, ?, ?, ?)", group_id, user_id, message, formatted_datetime)
        return Response(status=204)
    else:
        group_name = request.args.get('group_name')
        group_id = request.args.get('group_id')
        user_id = session.get("user_id")
        messages = db.execute("SELECT messages.group_id, messages.user_id, users_info.name || ' ' || users_info.surname AS name, messages.message, messages.datetime, images.filepath AS image FROM messages JOIN users_info ON messages.user_id = users_info.id JOIN images ON messages.user_id = images.user_id WHERE messages.group_id = ?", group_id)
        message_count = db.execute("SELECT COUNT(message) AS count FROM messages WHERE group_id = ?", group_id)
        count = message_count[0]['count']
        return render_template("chat.html", group_name=group_name, messages=messages, group_id=group_id, user_id=user_id, count=count)


@app.route("/get_new_msg", methods=["POST"])
@login_required
def get_new_msg():
    data = request.json
    
    group_id = data.get('key1')
    
    count = data.get('key2')
    
    check = new_msg_check(group_id, db, count)
    
    if check:
        message = db.execute("""
            SELECT messages.id, messages.group_id, messages.user_id,
            users_info.name || ' ' || users_info.surname AS name,
            messages.message, messages.datetime, images.filepath AS image
            FROM messages
            JOIN users_info ON messages.user_id = users_info.id
            JOIN images ON messages.user_id = images.user_id
            WHERE messages.group_id = ?
            ORDER BY messages.id DESC
            LIMIT 1
            """, group_id)
        
        if message:
            response = jsonify(message)
            return response
    
    return jsonify({'error': 'No new messages or invalid request'})
