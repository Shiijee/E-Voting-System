from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')
@app.route('/vote', methods=['POST'])

def vote():
    candidate = request.form['candidate']
    print(f'Vote cast for: {candidate}')
    return redirect(url_for('home'))    

if __name__ == '__main__':
    app.run(debug=True)
