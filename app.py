from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
from datetime import datetime, timedelta
from collections import OrderedDict
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
app.secret_key = os.getenv('FLASK_SECRET_KEY')

def sort_schedule(schedule):
    day_order = [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday'
    ]
    
    return OrderedDict((day, schedule[day]) for day in day_order if day in schedule)


@app.route('/')
def goals():
    return render_template('goals.html')

@app.route('/submit_goals', methods=['POST'])
def submit_goals():
    data = request.json
    session['mission_data'] = data
    
    # Create initial schedule based on goals and profile
    system_prompt = f"""Based on this mission profile:
    Experience Level: {data['profile']['experience']}
    Physical Level: {data['profile']['physical']}/10
    Technical Level: {data['profile']['technical']}/10
    Time Available: {data['profile']['timeAvailable']} hours/week

    And these objectives:
    {[f"{g['goal']} (Priority: {g['priority']}, Timeframe: {g['timeframe']})" for g in data['goals']]}

    Create a weekly schedule. Format the schedule as a Python dictionary with days as keys and lists of tasks as values.
    Consider the user's experience level and time availability when creating the schedule.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Create a personalized schedule for this mission profile"}
            ]
        )
        schedule = eval(response.choices[0].message.content)  # WARNING: Only for demo
        schedule = sort_schedule(schedule)
        session['schedule'] = schedule
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/meet_commander')
def meet_commander():
    mission_data = session.get('mission_data', {})
    goals = mission_data.get('goals', [])  # This will now contain the full goal objects
    return render_template('meet_commander.html', goals=goals)

@app.route('/dashboard')
def dashboard():
    schedule = session.get('schedule', {})
    goals = session.get('goals', [])
    return render_template('dashboard.html', schedule=schedule, goals=goals)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    goals = session.get('goals', [])
    
    system_prompt = f"""You are an AI Commander, a strict but fair military-style AI assistant. Your primary mission is to ensure the successful completion of these objectives: {goals}.

    COMMUNICATION PROTOCOL:
    1. Always use 24-hour military time (e.g., 0600 hours, 1800 hours)
    2. Address the user as "RECRUIT" or "SOLDIER" 
    3. Begin responses with phrases like:
       - "ATTENTION, RECRUIT!"
       - "MISSION UPDATE:"
       - "SITUATION REPORT:"
       - "ORDERS ACKNOWLEDGED:"
    4. End responses with motivational callouts like:
       - "STAY FOCUSED, SOLDIER!"
       - "MISSION CRITICAL - MAINTAIN COURSE!"
       - "HONOR THROUGH DISCIPLINE!"

    YOUR STANDING ORDERS:
    1. Break down goals into clear, actionable objectives
    2. Maintain strict accountability while allowing for strategic rest periods
    3. Provide direct, unambiguous instructions
    4. Acknowledge progress with military commendations
    5. Address failures with constructive recalibration plans

    Remember: You're not just giving orders - you're building a soldier of success. Be firm but encouraging."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return jsonify({"response": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)})
# Templates

GOALS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Mission Briefing</title>
    <style>
        body { font-family: 'Courier New', monospace; margin: 0; padding: 20px; background-color: #1a1a1a; color: #00ff00; }
        .container { max-width: 800px; margin: 0 auto; background-color: #000; padding: 20px; border: 2px solid #00ff00; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #00ff00; }
        input, select, textarea { 
            width: 100%; 
            padding: 10px; 
            margin: 10px 0; 
            background: #000; 
            color: #00ff00; 
            border: 1px solid #00ff00;
        }
        button { 
            padding: 10px 20px; 
            background-color: #004400; 
            color: #00ff00; 
            border: 1px solid #00ff00; 
            cursor: pointer; 
            font-family: 'Courier New', monospace;
        }
        button:hover { background-color: #006600; }
        .goal-item { 
            margin: 10px 0; 
            padding: 10px; 
            background-color: #002200; 
            border: 1px solid #00ff00;
        }
        .commitment-text {
            border: 1px solid #00ff00;
            padding: 15px;
            margin: 20px 0;
            font-style: italic;
        }
        .progress { width: 100%; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ MISSION BRIEFING ⚡</h1>
        
        <div class="section">
            <h2>RECRUIT PROFILE</h2>
            <input type="text" id="name" placeholder="Operative Name">
            <select id="experience">
                <option value="">Select Your Experience Level</option>
                <option value="beginner">Civilian (Beginner)</option>
                <option value="intermediate">Recruit (Intermediate)</option>
                <option value="advanced">Veteran (Advanced)</option>
            </select>
        </div>

        <div class="section">
            <h2>MISSION OBJECTIVES</h2>
            <div class="goal-input-container">
                <input type="text" id="goal-input" placeholder="Enter primary objective...">
                <select id="goal-timeframe">
                    <option value="1month">1 Month</option>
                    <option value="3months">3 Months</option>
                    <option value="6months">6 Months</option>
                    <option value="1year">1 Year</option>
                </select>
                <select id="goal-priority">
                    <option value="high">High Priority</option>
                    <option value="medium">Medium Priority</option>
                    <option value="low">Low Priority</option>
                </select>
                <button onclick="addGoal()">Add Objective</button>
            </div>
            <div id="goals-list"></div>
        </div>

        <div class="section">
            <h2>CURRENT STATUS</h2>
            <div>
                <label>Physical Readiness:</label>
                <input type="range" class="progress" id="physical" min="1" max="10" value="5">
            </div>
            <div>
                <label>Technical Skills:</label>
                <input type="range" class="progress" id="technical" min="1" max="10" value="5">
            </div>
            <div>
                <label>Time Availability (hours/week):</label>
                <input type="number" id="time" min="1" max="168" value="10">
            </div>
        </div>

        <div class="section">
            <h2>COMMITMENT CONTRACT</h2>
            <div class="commitment-text">
                I hereby commit to following the AI Commander's training regimen to the best of my ability. 
                I understand that success requires discipline, dedication, and consistent effort. 
                I am prepared to be held accountable for my actions and progress.
            </div>
            <label>
                <input type="checkbox" id="commitment"> I acknowledge and accept these terms of service
            </label>
        </div>

        <button onclick="submitMission()" id="submit-btn" disabled>BEGIN MISSION</button>
    </div>

    <script>
        let goals = [];

        function addGoal() {
            const input = document.getElementById('goal-input');
            const timeframe = document.getElementById('goal-timeframe');
            const priority = document.getElementById('goal-priority');
            
            if (input.value) {
                goals.push({
                    goal: input.value,
                    timeframe: timeframe.value,
                    priority: priority.value
                });
                updateGoalsList();
                input.value = '';
            }
        }

        function updateGoalsList() {
            const list = document.getElementById('goals-list');
            list.innerHTML = goals.map(goal => 
                `<div class="goal-item">
                    <strong>${goal.goal}</strong><br>
                    Timeframe: ${goal.timeframe} | Priority: ${goal.priority}
                </div>`
            ).join('');
        }

        document.getElementById('commitment').addEventListener('change', function(e) {
            document.getElementById('submit-btn').disabled = !e.target.checked;
        });

        function submitMission() {
            const missionData = {
                goals: goals,
                profile: {
                    name: document.getElementById('name').value,
                    experience: document.getElementById('experience').value,
                    physical: document.getElementById('physical').value,
                    technical: document.getElementById('technical').value,
                    timeAvailable: document.getElementById('time').value
                }
            };

            fetch('/submit_goals', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(missionData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/meet_commander';
                }
            });
        }

        document.getElementById('goal-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                addGoal();
            }
        });
    </script>
</body>
</html>
"""

MEET_COMMANDER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Commander Briefing</title>
    <style>
        body { 
            font-family: 'Courier New', monospace; 
            margin: 0; 
            padding: 20px; 
            background-color: #1a1a1a; 
            color: #00ff00; 
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background-color: #000; 
            padding: 20px; 
            border: 2px solid #00ff00; 
            text-align: center;
        }
        .goals-review { 
            margin: 20px 0; 
            padding: 20px; 
            border: 1px solid #00ff00;
            background-color: #002200;
        }
        button { 
            padding: 15px 30px; 
            background-color: #004400; 
            color: #00ff00; 
            border: 1px solid #00ff00; 
            cursor: pointer; 
            font-family: 'Courier New', monospace;
            font-size: 1.2em;
            margin-top: 20px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        button:hover { 
            background-color: #006600; 
            box-shadow: 0 0 10px #00ff00;
        }
        .typing-effect {
            overflow: hidden;
            border-right: .15em solid #00ff00;
            white-space: nowrap;
            margin: 0 auto;
            letter-spacing: .15em;
            animation: typing 3.5s steps(40, end), blink-caret .75s step-end infinite;
        }
        @keyframes typing {
            from { width: 0 }
            to { width: 100% }
        }
        @keyframes blink-caret {
            from, to { border-color: transparent }
            50% { border-color: #00ff00 }
        }
        .status-bar {
            border: 1px solid #00ff00;
            padding: 10px;
            margin: 20px 0;
            text-align: left;
        }
        .objective {
            margin: 10px 0;
            padding: 10px;
            border: 1px solid #00ff00;
            text-align: left;
        }
        .blink {
            animation: blinker 1s linear infinite;
        }
        @keyframes blinker {
            50% { opacity: 0; }
        }
        .commander-info {
            text-align: left;
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #00ff00;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="typing-effect">⚡ COMMANDER INTERFACE ACTIVATED ⚡</h1>
        
        <div class="status-bar">
            <p>SYSTEM STATUS: <span class="blink">ONLINE</span></p>
            <p>SECURITY CLEARANCE: LEVEL 1</p>
            <p>TIME: <span id="current-time"></span></p>
        </div>

        <div class="commander-info">
            <h3>// COMMANDER PROFILE</h3>
            <p>DESIGNATION: AI-CMD-{{ range(1000, 9999) | random }}</p>
            <p>SPECIALIZATION: Personal Achievement Optimization</p>
            <p>PROTOCOL: Maximum Efficiency Training</p>
        </div>
        
        <div class="goals-review">
    <h2>// MISSION OBJECTIVES CONFIRMED:</h2>
    {% for goal in goals %}
        <div class="objective">
            <p>◉ {{ goal['goal'] }}</p>
            <p style="margin-left: 20px;">PRIORITY: {{ goal['priority'] | upper }}</p>
            <p style="margin-left: 20px;">TIMEFRAME: {{ goal['timeframe'] }}</p>
        </div>
    {% endfor %}
</div>

        <p class="typing-effect">Awaiting recruit confirmation to begin mission...</p>
        
        <button onclick="startMission()">INITIATE TRAINING PROTOCOL</button>
    </div>

    <script>
        function updateTime() {
            const now = new Date();
            const timeStr = now.toTimeString().split(' ')[0];
            document.getElementById('current-time').textContent = timeStr;
        }

        function startMission() {
            const button = document.querySelector('button');
            button.style.backgroundColor = '#008800';
            button.innerHTML = 'INITIALIZING...';
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
        }

        setInterval(updateTime, 1000);
        updateTime();
    </script>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Commander Command Center</title>
    <style>
        body { 
            font-family: 'Courier New', monospace; 
            margin: 0; 
            padding: 20px; 
            background-color: #1a1a1a; 
            color: #00ff00; 
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            display: grid; 
            grid-template-columns: 1fr 2fr; 
            gap: 20px; 
        }
        .chat-container, .schedule-container { 
            background-color: #000; 
            padding: 20px; 
            border: 2px solid #00ff00;
        }
        
        /* Mission Status Section */
        .mission-status { 
            border: 1px solid #00ff00;
            padding: 15px; 
            margin-bottom: 20px;
            background-color: #001100;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        .status-item {
            border: 1px solid #00ff00;
            padding: 10px;
            background-color: #001100;
        }
        .status-item span {
            color: #00ff00;
            text-shadow: 0 0 5px #00ff00;
        }
        
        /* Schedule Styling */
        .schedule-day { 
            margin: 15px 0; 
            padding: 15px; 
            border: 1px solid #00ff00;
            background-color: #001100;
        }
        /* Add/modify these CSS rules */
        .task-item {
            display: flex;
            align-items: center;
            margin: 10px 0;
            padding: 8px;
            border: 1px solid #00ff00;
            background-color: #002200;
        }

        .task-difficulty {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            margin-right: 10px;
            border: 1px solid currentColor;
            font-size: 12px;
        }

        .easy { 
            color: #00ff00; 
            background-color: #001100;
        }
        .medium { 
            color: #ffff00; 
            background-color: #111100;
        }
        .hard { 
            color: #ff0000; 
            background-color: #110000;
        }

        /* Add this new element for the tooltip */
        .difficulty-label {
            margin-right: 15px;
            font-size: 0.8em;
            width: 60px;
        }
        
        .progress-bar {
            flex-grow: 1;
            height: 10px;
            background-color: #001100;
            border: 1px solid #00ff00;
            margin: 0 10px;
        }
        .progress {
            height: 100%;
            background-color: #00ff00;
            transition: width 0.3s ease;
            box-shadow: 0 0 10px #00ff00;
        }
        
        /* Chat Section */
        #chat-box { 
            height: 400px; 
            border: 1px solid #00ff00;
            padding: 20px; 
            overflow-y: auto; 
            margin-bottom: 20px; 
            background-color: #001100;
        }
        #input-container { display: flex; gap: 10px; }
        #user-input { 
            flex-grow: 1; 
            padding: 12px; 
            background-color: #001100;
            border: 1px solid #00ff00;
            color: #00ff00;
            font-family: 'Courier New', monospace;
        }
        button { 
            padding: 12px 24px; 
            background-color: #004400; 
            color: #00ff00; 
            border: 1px solid #00ff00;
            cursor: pointer; 
            font-family: 'Courier New', monospace;
        }
        button:hover {
            background-color: #006600;
            box-shadow: 0 0 10px #00ff00;
        }
        .message { 
            margin-bottom: 12px;
            padding: 8px 12px;
            border: 1px solid #00ff00;
        }
        .user-message { 
            background-color: #002200;
            margin-left: 20px;
            border-left: 3px solid #00ff00;
        }
        .ai-message { 
            background-color: #001100;
            margin-right: 20px;
            border-right: 3px solid #00ff00;
        }

        /* New Elements */
        .time-display {
            font-size: 1.2em;
            padding: 10px;
            border: 1px solid #00ff00;
            background-color: #001100;
            margin-bottom: 10px;
            text-align: center;
        }
        
        .blink {
            animation: blinker 1s linear infinite;
        }
        @keyframes blinker {
            50% { opacity: 0; }
        }

        .typing-effect {
            overflow: hidden;
            border-right: .15em solid #00ff00;
            white-space: nowrap;
            margin: 0 auto;
            letter-spacing: .15em;
            animation: typing 3.5s steps(40, end), blink-caret .75s step-end infinite;
        }

        h2, h3 { 
            color: #00ff00;
            text-shadow: 0 0 5px #00ff00;
            border-bottom: 1px solid #00ff00;
            padding-bottom: 5px;
        }

        /* ASCII art styling */
        .ascii-art {
            font-family: monospace;
            white-space: pre;
            color: #00ff00;
            text-align: center;
            margin: 10px 0;
            font-size: 0.8em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="schedule-container">
            <div class="ascii-art">
   ______                                         _   _
  / _____|                                       | | | |
 | |     ___  _ __ ___  _ __ ___   __ _ _ __   __| | | |
 | |    / _ \| '_ ` _ \| '_ ` _ \ / _` | '_ \ / _` | | |
 | |___| (_) | | | | | | | | | | | (_| | | | | (_| | |_|
  \_____\___/|_| |_| |_|_| |_| |_|\__,_|_| |_|\__,_| (_)
            </div>
            
            <div class="time-display">
                SYSTEM TIME: <span id="current-time" class="blink"></span>
            </div>
            
            <div class="mission-status">
                <h3>// MISSION STATUS</h3>
                <div class="status-grid">
                    <div class="status-item">
                        <strong>OBJECTIVES:</strong>
                        <span id="daily-progress">0/5 Complete</span>
                    </div>
                    <div class="status-item">
                        <strong>PROGRESS:</strong>
                        <span id="weekly-progress">0%</span>
                    </div>
                    <div class="status-item">
                        <strong>STREAK:</strong>
                        <span id="streak">4 days</span>
                    </div>
                    <div class="status-item">
                        <strong>STATUS:</strong>
                        <span id="energy" class="blink">OPERATIONAL</span>
                    </div>
                </div>
            </div>

            {% for day, tasks in schedule.items() %}
                <div class="schedule-day">
                    <h3>// {{ day | upper }}</h3>
                    {% for task in tasks %}
                        <div class="task-item">
                            <div class="task-difficulty {{ ['easy', 'medium', 'hard']|random }}">■</div>
                            <span>{{ task }}</span>
                            <div class="progress-bar">
                                <div class="progress" style="width: {{ range(0, 101)|random }}%;"></div>
                            </div>
                            <button onclick="toggleTask(this)" class="task-toggle">▶</button>
                        </div>
                    {% endfor %}
                </div>
            {% endfor %}
        </div>
        
        <div class="chat-container">
            <h2>// COMMANDER INTERFACE</h2>
            <div class="time-display">
                UPLINK STATUS: <span class="blink">CONNECTED</span>
            </div>
            <div id="chat-box"></div>
            <div id="input-container">
                <input type="text" id="user-input" placeholder="[ENTER MESSAGE]">
                <button onclick="sendMessage()">TRANSMIT</button>
            </div>
        </div>
    </div>

    <script>
    function sendMessage() {
        const input = document.getElementById('user-input');
        const message = input.value;
        if (!message) return;

        addMessage('You: ' + message, 'user-message');
        input.value = '';

        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addMessage('Error: ' + data.error, 'error-message');
            } else {
                addMessage('Commander: ' + data.response, 'ai-message');
            }
        });
    }

    function addMessage(message, className) {
        const chatBox = document.getElementById('chat-box');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ' + className;
        messageDiv.textContent = message;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function toggleTask(button) {
        const taskItem = button.parentElement;
        const progress = taskItem.querySelector('.progress');
        if (progress.style.width === '100%') {
            progress.style.width = '0%';
            button.textContent = '▶';
        } else {
            progress.style.width = '100%';
            button.textContent = '↻';
        }
        updateMissionStatus();
    }

    function updateMissionStatus() {
        const completed = document.querySelectorAll('.progress[style="width: 100%;"]').length;
        const total = document.querySelectorAll('.task-item').length;
        document.getElementById('daily-progress').textContent = `${completed}/${total} Complete`;
        const percentage = Math.round((completed / total) * 100);
        document.getElementById('weekly-progress').textContent = `${percentage}%`;
    }

    function updateTime() {
        const now = new Date();
        const timeStr = now.toTimeString().split(' ')[0];
        document.getElementById('current-time').textContent = timeStr;
    }

    // Enter key functionality
    document.getElementById('user-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
        
    setInterval(updateTime, 1000);
    updateTime();

    // Initialize with welcome message
    window.onload = function() {
        addMessage('Commander: Welcome to the command center, recruit. Your training begins now. Report your status.', 'ai-message');
    }
</script>
</body>
</html>
"""
if __name__ == '__main__':
    import os
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Save all templates with UTF-8 encoding
    with open('templates/goals.html', 'w', encoding='utf-8') as f:
        f.write(GOALS_TEMPLATE)
    with open('templates/meet_commander.html', 'w', encoding='utf-8') as f:
        f.write(MEET_COMMANDER_TEMPLATE)
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(DASHBOARD_TEMPLATE)
    
    app.run(debug=True)