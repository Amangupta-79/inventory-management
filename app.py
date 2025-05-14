from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# import models and forms after db & login setup
from models import User, Item
from forms import RegistrationForm, LoginForm, ItemForm

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('list_items'))
        flash('Invalid credentials')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def list_items():
    items = Item.query.all()
    return render_template('items.html', items=items)

@app.route('/item/new', methods=['GET', 'POST'])
@login_required
def add_item():
    form = ItemForm()
    if form.validate_on_submit():
        item = Item(
            name=form.name.data,
            quantity=form.quantity.data,
            description=form.description.data,
            category=form.category.data
        )
        db.session.add(item)
        db.session.commit()
        flash('Item added.')
        return redirect(url_for('list_items'))
    return render_template('item_form.html', form=form)

@app.route('/item/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    form = ItemForm(obj=item)
    if form.validate_on_submit():
        form.populate_obj(item)
        db.session.commit()
        flash('Item updated.')
        return redirect(url_for('list_items'))
    return render_template('item_form.html', form=form)

@app.route('/item/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('list_items'))

if __name__ == '__main__':
    app.run(debug=True)