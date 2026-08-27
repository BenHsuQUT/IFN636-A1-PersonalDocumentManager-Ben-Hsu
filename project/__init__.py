from flask import Flask, render_template
from flask_mysqldb import MySQL

mysql = MySQL()

app = Flask(__name__)

def create_app():
    app = Flask(__name__)

    app.secret_key = 'myqld-apartment-secret-2026'

    # ------ MySQL configurations ----- #
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = '00000000'  # Joon : CHANGE THIS PASSWORD IF IT IS DIFFERENT FROM YOUR LOCAL MYSQL PASSWORD AND MAKE SURE IT MATCHES!!
    # Example) You cannot sign in if this password is '00000000' and your MySQL password is 'admin'.
    # It needs more complicated way to change MySQL password, so please change the password here and save it.
    app.config['MYSQL_DB'] = 'myqld_db'     # Yen: change propertyrental to myqld_db because that is the name of the database
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
    app.config['MYSQL_PORT'] = 3306         # Joon : default number is 3306. Change this according to your MySQL port number.

    mysql.init_app(app)

    # ------ Notification ----- #
    from flask import session as flask_session
    # from project.db import get_notification_from_db

    @app.context_processor
    def inject_notification():
        user_id = flask_session.get('userID')
        if not user_id:
            return {'notifications': [], 'notification_count': 0}
        try:
            # notifs = get_notification_from_db(user_id)
            notifs = "test"
            return {'notifications': notifs, 'notification_count':len(notifs)}
        except:
            return {'notifications': [], 'notification_count': 0}

    # ------ Register Blueprint ----- #
    from project.views import views
    app.register_blueprint(views)

    # ------ Error handlers ----- #
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html")

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("500.html")

    return app
