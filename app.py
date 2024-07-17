from flask import Flask, render_template, request, redirect, session, url_for
from flask_pymongo import PyMongo
import bcrypt
from bson import ObjectId  # Add this import
from datetime import datetime

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/todoappdb'
mongo = PyMongo(app)

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_username = users.find_one({'username': request.form['username']})
        existing_email = users.find_one({'email': request.form['email']})

        if existing_username:
            return 'That username already exists!'
        elif existing_email:
            return 'That email is already registered!'
        elif request.form['password'] != request.form['confirm_password']:
            return 'Password and confirm password do not match!'

        hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        users.insert_one({
            'name': request.form['name'],
            'email': request.form['email'],
            'username': request.form['username'],
            'password': hashpass,
            'registration_date': current_date,  # Store registration date
            'last_login': None  # Initialize last login as None
        })
        return redirect(url_for('login'))  # Redirect to login page after registration
    return render_template('register.html')



# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        login_user = users.find_one({'username': request.form['username']})

        if login_user:
            # Debugging: print login_user to check its content
            print("Login User:", login_user)

            if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['username'] = request.form['username']
                # Update last login time
                users.update_one({'_id': login_user['_id']}, {'$set': {'last_login': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}})
                return redirect(url_for('dashboard'))
        return 'Invalid username/password combination'
    return render_template('login.html')

# Dashboard Page
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        # Update last login time on session access
        users = mongo.db.users
        user = users.find_one({'username': session['username']})
        users.update_one({'_id': user['_id']}, {'$set': {'last_login': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}})
        todos = mongo.db.todos.find({'username': session['username']})
        return render_template('dashboard.html', todos=todos)
    return redirect(url_for('login'))


# Add Todo
@app.route('/create_todo', methods=['GET', 'POST'])
def create_todo():
    if 'username' in session:
        if request.method == 'POST':
            todos = mongo.db.todos
            todos.insert_one({
                'username': session['username'],
                'title': request.form['title'],
                'description': request.form['description'],
                'date': request.form['date'],
                'start_time': request.form['start-time'],
                'end_time': request.form['end-time']
            })
            return redirect(url_for('dashboard'))  # Redirect to dashboard page after adding a todo
        return render_template('create_todo.html')  # Render the create_todo.html template for GET request
    return redirect(url_for('login'))  # Redirect to login page if not logged in

# Update Todo
@app.route('/update_todo/<string:todo_id>', methods=['GET', 'POST'])
def update_todo(todo_id):
    if 'username' in session:
        if request.method == 'POST':
            print("Form Data:", request.form)
            print("Todo ID:", todo_id)
            
            # Get the todo from the database using todo_id
            todo = mongo.db.todos.find_one({'_id': ObjectId(todo_id)})
            print("Todo from DB:", todo)

            # Update the todo with form data
            updated_todo = {
                'title': request.form['title'],
                'description': request.form['description'],
                'date': request.form['date'],
                'start_time': request.form['start-time'],
                'end_time': request.form['end-time']
            }
            print("Updated Todo Data:", updated_todo)

            # Update the todo in the database
            mongo.db.todos.update_one({'_id': ObjectId(todo_id)}, {'$set': updated_todo})
            
            # Redirect to the dashboard after updating
            return redirect(url_for('dashboard'))
        else:
            # Get the todo from the database using todo_id
            todo = mongo.db.todos.find_one({'_id': ObjectId(todo_id)})
            return render_template('update_todo.html', todo=todo, todo_id=todo_id)
    else:
        return redirect(url_for('login'))







# Profile Page
@app.route('/profile')
def profile():
    if 'username' in session:
        users = mongo.db.users
        user_data = users.find_one({'username': session['username']}, {'_id': 0, 'password': 0})  # Exclude password field
        return render_template('profile.html', user=user_data)
    return redirect(url_for('login'))

# Delete Todo
@app.route('/delete_todo/<string:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    if 'username' in session:
        mongo.db.todos.delete_one({'_id': ObjectId(todo_id), 'username': session['username']})
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True)
