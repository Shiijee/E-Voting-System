from flask import redirect, url_for, session
from Voxify import create_app

app = create_app()

@app.route('/')
def home():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'voter':
            return redirect(url_for('voter.dashboard'))
        elif role == 'superadmin':
            return redirect(url_for('super_admin.dashboard'))
    return redirect(url_for('auth.voter_login'))

if __name__ == '__main__':
    app.run(debug=True)
