from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/system")
def system():
    name = 'Docker'
    mail = 'my_email@gmail.com'
    return jsonify(
            system=name,
            email=mail
            )

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Run Flask server.')
    parser.add_argument("-a", "--ip", dest="hostIP", default="0.0.0.0",
                        type=str, help="IP address. Default: 0.0.0.0")
    args = parser.parse_args()

    app.run(debug=False, host=args.hostIP, port=5200)
