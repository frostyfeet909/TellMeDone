# Flask webhook plus some handling of that user-input
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request
from tell_me_done import data_interface
from tell_me_done import phone_numbers
from tell_me_done import password_manager
from passlib.hash import sha256_crypt
from subprocess import Popen
from pyngrok import ngrok


app = Flask(__name__)


def run(debug=False):
    # Run Flask consistent with ngrok
    port = 3000
    url = ngrok.connect(port).public_url
    print('[*] Tunnel URL:', url)
    app.run(port=port, debug=debug)


def process_command(command):
    # If-Else Chain to determine command
    if " " in command:
        argument = " ".join(command.split(" ")[1:])

        if command.lower().startswith("admin"):
            if set_admin(user, argument):
                responce = "Correct password! Your an admin"
            else:
                responce = "Wrong password! Your no admin"

        elif command.lower().startswith("name"):
            set_name(user, argument)
            responce = "Name Set! " + "Welcome " + user.name

        elif command.lower().startswith("newvars"):
            if set_newvars(user, argument):
                responce = "Variables saved!"
            else:
                responce = "You do not have permission!"

        elif command.lower().startswith("notification"):
            set_notifications(user)
            responce = "Notifications toggled!"

        else:
            responce = "Command not found!"

    else:
        responce = "Command not found!"

    return responce


def set_admin(user, password):
    # Set user admin under certain conditions
    password = password_manager.Password(password)
    if password.verify_admin():
        print("[*] New admin: %s" %
              (user.name if user.name is not None else user.phone_number))
        user.admin = True
        data_interface.save_user_data(user)

        return True

    return False


def set_name(user, name):
    # Set user nickname
    user.name = name
    data_interface.save_user_data(user)


def set_notifications(user):
    # Toggles users notifications setting
    if user.notifications:
        user.notifications = False
    else:
        user.notifications = True


def set_newvars(user, var):
    if user.admin:
        data_interface.save_json_data(var)
        return True
    else:
        return False


@ app.route("/", methods=['GET', 'POST'])
def sms():
    # Receive incoming messages
    resp = MessagingResponse()
    user = data_interface.get_user_data(request.form['From'])
    command = str(request.form['Body'])

    # Setup new user if needed
    if not user:
        user = phone_numbers.User(request.form['From'])
        data_interface.save_user_data(user)
        print("[*] New user registered: %s" %
              (user.name if user.name is not None else user.phone_number))
        resp.message("Welcome new user! Your now signed up for notifications")
        resp.message(
            "Commands:\n admin [admin password] - Admin login \n name [name] - Set username \n notification - Toggles notifications \n newvars [variable] - Assign new variables")

    print("[*] Message from: %s" %
          (user.name if user.name is not None else user.phone_number))
    print("    - %s" % command)

    resp.message(process_command(command))

    return str(resp)
