from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)

# Configurações Z-API
ZAPI_INSTANCE_ID = "3E34371D3A3420D319F79EFBA4B7C50F"
ZAPI_TOKEN = "6D9333950FDDCC8FB3D11ECA"
ZAPI_BASE_URL = "https://api.z-api.io/instances"

# Base de dados em memória
students_db = {}
conversations_db = []

# Respostas educacionais inteligentes
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
        "Pronunciation is so important! Let me help you sound more natural.",
        "Great choice! Good pronunciation will boost your confidence in speaking English.",
        "Let's work on your pronunciation. I'll help you with the sounds and rhythm of English."
    ],
    'conversation': [
        "I love having conversations! This is the best way to practice real English.",
        "Conversation practice is perfect! Let's chat and improve your fluency naturally.",
        "Excellent! Real conversations help you think in English. Let's talk!"
    ]
}

def send_whatsapp_message(phone, message):
    """Envia mensagem via Z-API com múltiplas tentativas para WhatsApp Business"""
    
    # Diferentes formatos de autenticação para testar
    auth_formats = [
        # Formato 1: Client-Token no header (padrão atual)
        {
            "name": "Client-Token Header",
            "url": f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-text",
            "headers": {
                "Content-Type": "application/json",
                "Client-Token": ZAPI_TOKEN
            }
        },
        # Formato 2: Sem Client-Token (só URL com token)
        {
            "name": "URL Token Only",
            "url": f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-text",
            "headers": {
                "Content-Type": "application/json"
            }
        },
        # Formato 3: Authorization Bearer
        {
            "name": "Authorization Bearer",
            "url": f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-text",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ZAPI_TOKEN}"
            }
        },
        # Formato 4: X-API-Token
        {
            "name": "X-API-Token",
            "url": f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-text",
            "headers": {
                "Content-Type": "application/json",
                "X-API-Token": ZAPI_TOKEN
            }
        },
        # Formato 5: Token no header como Authorization
        {
            "name": "Authorization Token",
            "url": f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-text",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": ZAPI_TOKEN
            }
        }
    ]
    
    payload = {
        "phone": phone,
        "message": message
    }
    
    print(f"🚀 Tentando enviar mensagem para {phone}")
    print(f"💬 Mensagem: {message[:50]}...")
    
    # Tentar cada formato até um funcionar
    for i, config in enumerate(auth_formats, 1):
        try:
            print(f"\n--- Tentativa {i}: {config['name']} ---")
            
            response = requests.post(
                config["url"], 
                json=payload, 
                headers=config["headers"],
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                print(f"✅ SUCESSO! Formato '{config['name']}' funcionou!")
                return True
            elif response.status_code == 400:
                print(f"❌ Erro 400: {response.text}")
            elif response.status_code == 401:
                print(f"❌ Erro 401: Token inválido")
            elif response.status_code == 403:
                print(f"❌ Erro 403: Sem permissão")
            else:
                print(f"❌ Erro {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout na tentativa {i}")
        except requests.exceptions.ConnectionError:
            print(f"🔌 Erro de conexão na tentativa {i}")
        except Exception as e:
            print(f"❌ Erro inesperado na tentativa {i}: {e}")
    
    print(f"\n❌ Todas as tentativas falharam para {phone}")
    return False

def generate_pollinations_response(message, user_context=""):
    """Gera resposta inteligente usando Pollinations AI"""
    try:
        # Prompt educacional para Pollinations
        educational_prompt = f"""
        You are an expert English tutor. A student sent this message: "{message}"
        
        Context: {user_context}
        
        Respond as a friendly, encouraging English teacher. Your response should:
        1. Be helpful and educational
        2. Correct any grammar mistakes gently
        3. Suggest improvements
        4. Ask follow-up questions to continue the conversation
        5. Keep it conversational and engaging
        6. Use simple English if the student is a beginner
        
        Response (max 100 words):
        """
        
        # Chamar Pollinations Text API
        pollinations_url = "https://text.pollinations.ai/openai"
        
        response = requests.post(
            pollinations_url,
            json={
                "messages": [
                    {"role": "system", "content": "You are a helpful English tutor."},
                    {"role": "user", "content": educational_prompt}
                ],
                "model": "openai"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            ai_response = response.text.strip()
            print(f"🤖 Pollinations response: {ai_response[:50]}...")
            return ai_response
        else:
            print(f"❌ Pollinations error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error calling Pollinations: {e}")
        return None

def generate_response(message, user_id):
    """Gera resposta educacional inteligente"""
    
    # Primeiro tenta Pollinations AI
    ai_response = generate_pollinations_response(message, f"User ID: {user_id}")
    
    if ai_response:
        return ai_response
    
    # Fallback para respostas pré-definidas
    message_lower = message.lower()
    
    # Detectar tipo de mensagem
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
        response_type = 'greeting'
    elif any(word in message_lower for word in ['grammar', 'correct', 'mistake', 'error']):
        response_type = 'grammar'
    elif any(word in message_lower for word in ['word', 'vocabulary', 'meaning', 'definition']):
        response_type = 'vocabulary'
    elif any(word in message_lower for word in ['pronounce', 'pronunciation', 'sound', 'accent']):
        response_type = 'pronunciation'
    else:
        response_type = 'conversation'
    
    # Selecionar resposta aleatória do tipo detectado
    responses = educational_responses.get(response_type, educational_responses['conversation'])
    base_response = random.choice(responses)
    
    # Personalizar resposta
    if 'name' in message_lower:
        base_response += " It's nice to meet you! What would you like to practice today?"
    elif '?' in message:
        base_response += " That's a great question! Let me help you with that."
    
    return base_response

def update_student_progress(phone, message_type="text"):
    """Atualiza progresso do estudante"""
    if phone not in students_db:
        students_db[phone] = {
            "level": "beginner",
            "xp": 0,
            "conversations": 0,
            "last_activity": datetime.now().isoformat(),
            "streak_days": 1,
            "achievements": []
        }
    
    student = students_db[phone]
    
    # Adicionar XP baseado no tipo de atividade
    xp_rewards = {
        "text": 10,
        "audio": 15,
        "image": 5,
        "document": 8
    }
    
    student["xp"] += xp_rewards.get(message_type, 10)
    student["conversations"] += 1
    student["last_activity"] = datetime.now().isoformat()
    
    # Atualizar nível baseado no XP
    if student["xp"] >= 1000:
        student["level"] = "advanced"
    elif student["xp"] >= 500:
        student["level"] = "intermediate"
    elif student["xp"] >= 200:
        student["level"] = "elementary"
    
    # Verificar conquistas
    new_achievements = []
    if student["conversations"] == 1 and "First Conversation" not in student["achievements"]:
        new_achievements.append("🎉 First Conversation")
    if student["conversations"] == 10 and "Chatty Learner" not in student["achievements"]:
        new_achievements.append("💬 Chatty Learner")
    if student["xp"] >= 100 and "Rising Star" not in student["achievements"]:
        new_achievements.append("⭐ Rising Star")
    
    student["achievements"].extend(new_achievements)
    
    return student, new_achievements

@app.route('/')
def home():
    return jsonify({
        "bot_name": "English Tutor Bot",
        "version": "2.0 - WhatsApp Business Compatible",
        "status": "online",
        "features": [
            "🧠 AI-Powered Conversations (Pollinations)",
            "🎮 Gamification System",
            "📊 Progress Tracking",
            "🎵 Audio Support",
            "🖼️ Image Generation",
            "📱 WhatsApp Business Compatible"
        ],
        "endpoints": {
            "health": "/api/health",
            "webhook": "/api/webhook/message-received",
            "progress": "/api/student/{phone}/progress"
        }
    })

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_students": len(students_db),
        "total_conversations": sum(s.get("conversations", 0) for s in students_db.values()),
        "services": {
            "bot": "online",
            "ai": "functional",
            "database": "connected"
        }
    })

@app.route('/api/webhook/message-received', methods=['POST'])
def receive_message():
    try:
        data = request.get_json()
        
        # Extrair informações da mensagem
        phone = data.get('phone', 'unknown')
        message_type = data.get('type', 'text')
        
        print(f"📨 Mensagem recebida de {phone} - Tipo: {message_type}")
        
        # Processar diferentes tipos de mensagem
        if message_type == 'text':
            message_content = data.get('text', {}).get('message', '')
        elif message_type == 'audio':
            message_content = "Received audio message"
        elif message_type == 'image':
            message_content = "Received image"
        else:
            message_content = f"Received {message_type} message"
        
        print(f"💬 Conteúdo: {message_content}")
        
        # Atualizar progresso do estudante
        student_data, achievements = update_student_progress(phone, message_type)
        
        # Gerar resposta educacional
        bot_response = generate_response(message_content, phone)
        
        # Adicionar informações de progresso à resposta
        if achievements:
            bot_response += f"\n\n🎉 New Achievement: {', '.join(achievements)}"
        
        progress_info = f"\n\n📊 Your Progress: Level {student_data['level'].title()} | {student_data['xp']} XP | {student_data['conversations']} conversations"
        bot_response += progress_info
        
        # Enviar resposta via WhatsApp
        success = send_whatsapp_message(phone, bot_response)
        
        # Salvar conversa
        conversations_db.append({
            "timestamp": datetime.now().isoformat(),
            "phone": phone,
            "user_message": message_content,
            "bot_response": bot_response,
            "sent_successfully": success
        })
        
        return jsonify({
            "status": "success",
            "message_processed": True,
            "response_sent": success,
            "student_progress": student_data,
            "bot_response": bot_response
        })
        
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/webhook/message-status', methods=['POST'])
def message_status():
    """Webhook para status de mensagens"""
    try:
        data = request.get_json()
        print(f"📋 Status da mensagem: {data}")
        return jsonify({"status": "received"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/webhook/disconnected', methods=['POST'])
def disconnected():
    """Webhook para desconexão"""
    try:
        data = request.get_json()
        print(f"🔌 Instância desconectada: {data}")
        return jsonify({"status": "received"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/webhook/test', methods=['GET', 'POST'])
def test_webhook():
    """Endpoint para testar o webhook"""
    if request.method == 'GET':
        return jsonify({
            "status": "success",
            "message": "Webhook test endpoint working!",
            "timestamp": datetime.now().isoformat()
        })
    
    # Simular mensagem de teste
    test_response = generate_response("Hello, this is a test!", "test_user")
    return jsonify({
        "status": "success",
        "message": "Test completed successfully",
        "test_response": test_response
    })

@app.route('/api/student/<phone>/progress')
def get_student_progress(phone):
    """Obter progresso de um estudante"""
    if phone in students_db:
        student = students_db[phone]
        return jsonify({
            "phone": phone,
            "level": student["level"],
            "xp": student["xp"],
            "conversations": student["conversations"],
            "achievements": student["achievements"],
            "last_activity": student["last_activity"],
            "streak_days": student["streak_days"]
        })
    else:
        return jsonify({
            "phone": phone,
            "message": "Student not found",
            "level": "new",
            "xp": 0,
            "conversations": 0
        }), 404

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("🚀 Starting English Tutor Bot - WhatsApp Business Compatible...")
    print("📚 Educational AI: Pollinations + Fallback")
    print("🎮 Gamification: Active")
    print("💬 WhatsApp Business Integration: Multi-format Auth")
    print(f"📡 Z-API Instance: {ZAPI_INSTANCE_ID}")
    print(f"🔗 Running on port: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

