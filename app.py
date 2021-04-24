from flask import Flask
app = Flask(__name__)

@app.route("/foo")
def hello():
  return "bar"

if __name__ == "__main__":
  app.run()