from flask import Flask, render_template, redirect, url_for
from Voxify.__init__ import create_app

app = create_app()

@app.route('/')
def home():
    return redirect(url_for("auth.login"))

if __name__ == "__main__":
    app.run(debug=True)