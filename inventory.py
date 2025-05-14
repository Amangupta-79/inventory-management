from flask import Flask, request, redirect, url_for, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os

# --- Flask App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)

# --- Initial Setup ---
def create_tables():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin'))
        db.session.add(admin)
        db.session.commit()

# --- User Loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Templates ---
login_page = '''
<!doctype html><title>Login</title>
<h2>Login</h2>
<form method="post">
    <p><input type="text" name="username" placeholder="Username">
    <p><input type="password" name="password" placeholder="Password">
    <p><button type="submit">Login</button>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <p style="color:red;">{{ messages[0] }}</p>
      {% endif %}
    {% endwith %}
</form>
'''

dashboard_page = '''
<!doctype html><title>Dashboard</title>
<h2>Welcome, {{ current_user.username }}</h2>
<a href="{{ url_for('logout') }}">Logout</a>
<h3>Add Item</h3>
<form method="post" action="{{ url_for('add_item') }}">
    <input name="name" placeholder="Item name" required>
    <input name="quantity" type="number" placeholder="Quantity" required>
    <input name="description" placeholder="Description">
    <button type="submit">Add</button>
</form>

<h3>Inventory Items</h3>
<table border="1" cellpadding="5">
<tr><th>Name</th><th>Quantity</th><th>Description</th><th>Actions</th></tr>
{% for item in items %}
<tr>
<td>{{ item.name }}</td>
<td>{{ item.quantity }}</td>
<td>{{ item.description }}</td>
<td>
    <form method="post" action="{{ url_for('update_item', id=item.id) }}" style="display:inline;">
        <input name="name" value="{{ item.name }}" required>
        <input name="quantity" type="number" value="{{ item.quantity }}" required>
        <input name="description" value="{{ item.description }}">
        <button type="submit">Update</button>
    </form>
    <form method="post" action="{{ url_for('delete_item', id=item.id) }}" style="display:inline;">
        <button onclick="return confirm('Delete this item?')" type="submit">Delete</button>
    </form>
</td>
</tr>
{% endfor %}
</table>
'''

# --- Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form['username']).first()
        if u and check_password_hash(u.password, request.form['password']):
            login_user(u)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template_string(login_page)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    items = Item.query.all()
    return render_template_string(dashboard_page, items=items)

@app.route('/add', methods=['POST'])
@login_required
def add_item():
    new_item = Item(
        name=request.form['name'],
        quantity=int(request.form['quantity']),
        description=request.form.get('description', '')
    )
    db.session.add(new_item)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update_item(id):
    item = Item.query.get_or_404(id)
    item.name = request.form['name']
    item.quantity = int(request.form['quantity'])
    item.description = request.form.get('description', '')
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('dashboard'))

# --- Run ---
if __name__ == '__main__':
    app.run(debug=True)
