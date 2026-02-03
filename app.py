from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import random
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kbc-secret-key-2026'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Hardcoded users database
USERS = {
    'participant1': 'pass1',
    'participant2': 'pass2',
    'participant3': 'pass3',
    'participant4': 'pass4',
    'participant5': 'pass5'
}

ADMIN_PASSWORD = 'admin123'

# Load questions
with open('questions.json', 'r', encoding='utf-8') as f:
    QUESTIONS = json.load(f)

# Game state
game_state = {
    'current_question': 0,
    'lifelines': {
        '50-50': True,
        'audience_poll': True,
        'phone_friend': True
    },
    'poll_votes': {'A': 0, 'B': 0, 'C': 0, 'D': 0},
    'poll_active': False,
    'fff_winner': None,
    'fff_active': False
}


# Routes
@app.route('/')
def index():
    return "KBC Quiz Server Running"


@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/participant')
def participant():
    return render_template('participant.html')


@app.route('/poll')
def poll():
    return render_template('poll.html')


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    password = request.json.get('password')
    if password == ADMIN_PASSWORD:
        session['admin'] = True
        return jsonify({'success': True})
    return jsonify({'success': False}), 401


@app.route('/api/participant/login', methods=['POST'])
def participant_login():
    username = request.json.get('username')
    password = request.json.get('password')
    if username in USERS and USERS[username] == password:
        session['participant'] = username
        return jsonify({'success': True, 'username': username})
    return jsonify({'success': False}), 401


@app.route('/api/questions/<int:question_id>')
def get_question(question_id):
    if question_id < len(QUESTIONS):
        return jsonify(QUESTIONS[question_id])
    return jsonify({'error': 'Question not found'}), 404


# WebSocket Events
@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('load_question')
def handle_load_question(data):
    question_id = data.get('question_id', 0)
    game_state['current_question'] = question_id
    if question_id < len(QUESTIONS):
        emit('question_loaded', QUESTIONS[question_id], broadcast=True)


@socketio.on('select_answer')
def handle_select_answer(data):
    emit('answer_selected', data, broadcast=True)


@socketio.on('reveal_answer')
def handle_reveal_answer(data):
    emit('answer_revealed', data, broadcast=True)


@socketio.on('use_lifeline')
def handle_use_lifeline(data):
    lifeline = data.get('lifeline')
    if lifeline in game_state['lifelines'] and game_state['lifelines'][lifeline]:
        game_state['lifelines'][lifeline] = False

        if lifeline == '50-50':
            question = QUESTIONS[game_state['current_question']]
            correct = question['correct']
            options = ['A', 'B', 'C', 'D']
            options.remove(correct)
            wrong_to_remove = random.sample(options, 2)
            emit('lifeline_5050', {'remove': wrong_to_remove}, broadcast=True)

        elif lifeline == 'audience_poll':
            game_state['poll_active'] = True
            game_state['poll_votes'] = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
            emit('poll_started', {'question_id': game_state['current_question']}, broadcast=True)

        elif lifeline == 'phone_friend':
            emit('phone_friend_started', {}, broadcast=True)

        emit('lifeline_used', {'lifeline': lifeline}, broadcast=True)


@socketio.on('submit_vote')
def handle_vote(data):
    if game_state['poll_active']:
        option = data.get('option')
        if option in game_state['poll_votes']:
            game_state['poll_votes'][option] += 1
            emit('vote_recorded', {}, room=request.sid)


@socketio.on('end_poll')
def handle_end_poll():
    game_state['poll_active'] = False
    total = sum(game_state['poll_votes'].values())
    if total > 0:
        percentages = {k: round((v / total) * 100) for k, v in game_state['poll_votes'].items()}
    else:
        percentages = {'A': 25, 'B': 25, 'C': 25, 'D': 25}
    emit('poll_results', {'results': percentages}, broadcast=True)


@socketio.on('activate_fff')
def handle_activate_fff():
    game_state['fff_active'] = True
    game_state['fff_winner'] = None
    emit('fff_activated', {}, broadcast=True)


@socketio.on('fff_buzz')
def handle_fff_buzz(data):
    if game_state['fff_active'] and game_state['fff_winner'] is None:
        username = data.get('username')
        game_state['fff_winner'] = username
        game_state['fff_active'] = False
        emit('fff_winner', {'winner': username}, broadcast=True)


@socketio.on('reset_lifelines')
def handle_reset_lifelines():
    for key in game_state['lifelines']:
        game_state['lifelines'][key] = True
    emit('lifelines_reset', game_state['lifelines'], broadcast=True)


@socketio.on('start_phone_timer')
def handle_start_phone_timer():
    emit('phone_timer_start', {}, broadcast=True)


@socketio.on('pause_timer')
def handle_pause_timer():
    emit('timer_paused', {}, broadcast=True)


@socketio.on('resume_timer')
def handle_resume_timer():
    emit('timer_resumed', {}, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)