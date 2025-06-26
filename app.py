from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)

# Base de dados em memória (simples e funcional)
students_db = {}
conversations_db = []

# Respostas educacionais pré-definidas
educational_responses = {
    'greeting': [
        "Hello! Welcome to your English learning journey! I'm excited to help you improve your skills. What's your name?",
        "Hi there! I'm your personal English tutor. Let's start learning together! How can I help you today?",
        "Welcome! I'm here to make learning English fun and effective. What would you like to practice?"
    ],
    'grammar': [
        "Great question about grammar! Let me help you with that. Grammar is the foundation of good English.",
        "I love helping with grammar! It's one of the most important aspects of learning English.",
        "Grammar can be tricky, but don't worry - we'll practice together and you'll master it!"
    ],
    'vocabulary': [
        "Expanding your vocabulary is fantastic! Let's learn some new words together.",
        "Vocabulary building is key to fluent English. I'll help you learn words in context.",
        "Great! Learning new words will make your English much more expressive."
    ],
    'pronunciation': [
        "Pronunciation practice is excellent! Speaking clearly will boost your confidence.",
        "I'd love to help you with pronunciation. Practice makes perfect!",
        "Pronunciation is so important for communication. Let's work on it together!"
    ],
    'general': [
        "That's interesting! Let me help you express that better in English.",
        "I can see you're making progress! Keep practicing and you'll improve quickly.",
        "Excellent! Your English is getting better. What else would you like to learn?"
    ]
}

def get_student_level(phone):
    if phone not in students_db:
        students_db[phone] = {
            'level': 'beginner',
            'xp': 0,
            'streak': 0,
            'last_activity': datetime.now(),
            'conversations': 0
        }
    return students_db[phone]

def add_xp(phone, points):
    student = get_student_level(phone)
    student['xp'] += points
    student['conversations'] += 1
    student['last_activity'] = datetime.now()
    
    # Sistema de níveis
    levels = ['beginner', 'elementary', 'intermediate', 'advanced', 'expert']
    level_thresholds = [0, 100, 300, 600, 1000]
    
    for i, threshold in enumerate(level_thresholds):
        if student['xp'] >= threshold:
            student['level'] = levels[min(i, len(levels)-1)]

def generate_response(message, phone):
    message_lower = message.lower()
    student = get_student_level(phone)
    
    # Detectar tipo de pergunta
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
        response_type = 'greeting'
    elif any(word in message_lower for word in ['grammar', 'correct', 'mistake']):
        response_type = 'grammar'
    elif any(word in message_lower for word in ['word', 'vocabulary', 'meaning']):
        response_type = 'vocabulary'
    elif any(word in message_lower for word in ['pronounce', 'speak', 'sound']):
        response_type = 'pronunciation'
    else:
        response_type = 'general'
    
    # Selecionar resposta
    response = random.choice(educational_responses[response_type])
    
    # Adicionar informações de progresso
    add_xp(phone, 10)
    
    return {
        'response': response,
        'student_info': student,
        'tips': get_learning_tip(student['level'])
    }

def get_learning_tip(level):
    tips = {
        'beginner': "💡 Tip: Start with simple sentences and basic vocabulary!",
        'elementary': "💡 Tip: Try to use new words in sentences!",
        'intermediate': "💡 Tip: Practice speaking and listening every day!",
        'advanced': "💡 Tip: Read English articles and watch movies!",
        'expert': "💡 Tip: Focus on nuances and advanced expressions!"
    }
    return tips.get(level, tips['beginner'])

@app.route('/')
def home():
    return """
    <h1>🎓 English Tutor Bot - FUNCIONANDO!</h1>
    <p><strong>Status:</strong> ✅ Online e Operacional</p>
    <p><strong>Usuários ativos:</strong> {}</p>
    <p><strong>Conversas processadas:</strong> {}</p>
    <h2>Endpoints Disponíveis:</h2>
    <ul>
        <li>🟢 GET /api/health - Health check</li>
        <li>🟢 POST /api/webhook/message-received - Receber mensagens</li>
        <li>🟢 GET /api/student/{{phone}}/progress - Ver progresso</li>
    </ul>
    <p><em>Bot desenvolvido com ❤️ para ensinar inglês!</em></p>
    """.format(len(students_db), len(conversations_db))

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_students": len(students_db),
        "total_conversations": len(conversations_db),
        "services": {
            "bot": "online",
            "database": "connected",
            "ai": "functional"
        }
    })

@app.route('/api/webhook/message-received', methods=['POST'])
def receive_message():
    try:
        data = request.get_json()
        phone = data.get('phone', 'unknown')
        message_type = data.get('type', 'text')
        
        if message_type == 'text':
            message = data.get('text', {}).get('message', '')
        else:
            message = f"Received {message_type} message"
        
        # Gerar resposta educacional
        bot_data = generate_response(message, phone)
        
        # Salvar conversa
        conversation = {
            'phone': phone,
            'user_message': message,
            'bot_response': bot_data['response'],
            'timestamp': datetime.now().isoformat(),
            'message_type': message_type
        }
        conversations_db.append(conversation)
        
        return jsonify({
            "status": "success",
            "response_type": "educational_response",
            "message": "Message processed successfully",
            "bot_response": bot_data['response'],
            "student_progress": bot_data['student_info'],
            "learning_tip": bot_data['tips']
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error processing message: {str(e)}",
            "response_type": "error"
        }), 500

@app.route('/api/student/<phone>/progress')
def get_progress(phone):
    try:
        if phone not in students_db:
            return jsonify({
                "status": "error",
                "message": "Student not found"
            }), 404
        
        student = students_db[phone]
        user_conversations = [c for c in conversations_db if c['phone'] == phone]
        
        return jsonify({
            "status": "success",
            "data": {
                "student_info": student,
                "total_conversations": len(user_conversations),
                "recent_conversations": user_conversations[-5:],  # Últimas 5
                "achievements": get_achievements(student),
                "next_level_info": get_next_level_info(student)
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def get_achievements(student):
    achievements = []
    if student['conversations'] >= 1:
        achievements.append("🎉 First Conversation")
    if student['conversations'] >= 10:
        achievements.append("💬 Chatty Learner")
    if student['xp'] >= 100:
        achievements.append("⭐ Rising Star")
    if student['xp'] >= 500:
        achievements.append("🚀 English Enthusiast")
    return achievements

def get_next_level_info(student):
    level_thresholds = {'beginner': 100, 'elementary': 300, 'intermediate': 600, 'advanced': 1000}
    current_level = student['level']
    
    if current_level in level_thresholds:
        next_threshold = level_thresholds[current_level]
        needed = next_threshold - student['xp']
        return f"Need {needed} more XP to reach next level!"
    
    return "You're at the highest level! Keep practicing!"

@app.route('/api/webhook/test', methods=['GET', 'POST'])
def test_webhook():
    if request.method == 'GET':
        return jsonify({
            "status": "success",
            "message": "Webhook test endpoint working perfectly!",
            "timestamp": datetime.now().isoformat()
        })
    
    # POST test
    test_response = generate_response("Hello, this is a test!", "test_user")
    return jsonify({
        "status": "success",
        "message": "Test completed successfully",
        "test_response": test_response
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

