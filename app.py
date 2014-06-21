import os
import sqlite3
## request = current request object
## g =  general purpose variable associated with current app context
from flask import Flask, request, session, g, redirect,  url_for, abort, render_template, flash

#create app
app = Flask(__name__)

# Load Default config
app.config.from_object(__name__)

# override config
#TODO: put in separate file
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    DEBUG=True,
    SECRET_KEY='development key', #keep client sesh secure
    USERNAME='admin',
    PASSWORD='default'
))

# don't conplain if env var doesn't exist
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

#connect to db
def connect_db():
    """connect to specific db"""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

## db connection is open, but only want one
## request at a time uses the connection

#helper fn: db connect for current context and successive
#calls will return already established connection
def get_db():
    """opens a db connec if there is notne yet for current app context"""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

# close db uses function decorator
#called every time app tears down (at end of every request)
@app.teardown_appcontext
def close_db(error):
    """closes the db again at end of request"""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


#initialize the DB when you have no request --> application context
def init_db():
    with app.app_context(): #g is available
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.route('/')
def show_entries():
    #connect to db
    db = get_db()
    #query entries table, get title and text in order
    cur = db.execute('select title, text from entries order by id desc')
    #get all of those queries
    entries = cur.fetchall()
    #call template, feeding it namespaced data
    return render_template('show_entries.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries(title, text) values (?,?)',
               [request.form['title'], request.form['text']])
    db.commit()
    flash('New entry successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

#since we run this file to start the app ('python app.py'), the special variable
#__name__ is equal to '__main__' (cf. exporting it would set __name__ equal to
#'app'
if __name__ == '__main__':
    app.run()

