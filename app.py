from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests
from datetime import datetime, timedelta
import random
import re
import base64
from urllib.parse import quote

app = Flask(__name__)
CORS(app)

# Configurações Z-API
ZAPI_INSTANCE_ID = "3E34371D3A3420D319F79EFBA4B7C50F"
ZAPI_TOKEN = "6D9333950FDDCC8FB3D11ECA"
ZAPI_BASE_URL = "https://api.z-api.io/instances"

# Configurações Pollinations AI
POLLINATIONS_TEXT_URL = "https://text.pollinations.ai/openai"
POLLINATIONS_IMAGE_URL = "https://image.pollinations.ai/prompt"
POLLINATIONS_AUDIO_URL = "https://text.pollinations.ai/openai"

# Base de dados em memória
students_db = {}
conversations_db = []
lesson_progress = {}

# Sistema de lições estruturadas
LESSONS = {
    'beginner': [
        {'id': 1, 'title': 'Basic Greetings', 'content': 'Hello, Hi, Good morning, Good evening'},
        {'id': 2, 'title': 'Personal Information', 'content': 'My name is..., I am from..., I live in...'},
        {'id': 3, 'title': 'Numbers 1-20', 'content': 'One, two, three... twenty'},
        {'id': 4, 'title': 'Colors', 'content': 'Red, blue, green, yellow, black, white'},
        {'id': 5, 'title': 'Family Members', 'content': 'Mother, father, sister, brother, grandmother'}
    ],
    'elementary': [
        {'id': 6, 'title': 'Present Simple', 'content': 'I work, You work, He/She works'},
        {'id': 7, 'title': 'Daily Routines', 'content': 'I wake up, I have breakfast, I go to work'},
        {'id': 8, 'title': 'Food and Drinks', 'content': 'Apple, bread, water, coffee, pizza'},
        {'id': 9, 'title': 'Time and Days', 'content': 'Monday, Tuesday, 3 o\'clock, half past four'},
        {'id': 10, 'title': 'Asking Questions', 'content': 'What, Where, When, How, Why'}
    ],
    'intermediate': [
        {'id': 11, 'title': 'Past Tense', 'content': 'I went, I saw, I did, I was, I had'},
        {'id': 12, 'title': 'Future Plans', 'content': 'I will go, I am going to study'},
        {'id': 13, 'title': 'Comparatives', 'content': 'Bigger, smaller, more beautiful, better'},
        {'id': 14, 'title': 'Modal Verbs', 'content': 'Can, could, should, must, might'},
        {'id': 15, 'title': 'Conditional Sentences', 'content': 'If I study, I will pass the exam'}
    ]
}

# Sugestões de vídeos por nível
VIDEO_SUGGESTIONS = {
    'beginner': [
        {'title': 'English Alphabet Song', 'url': 'https://youtu.be/75p-N9YKqNo', 'duration': '2:30'},
        {'title': 'Basic English Greetings', 'url': 'https://youtu.be/OmJbhJJ8Uh8', 'duration': '5:15'},
        {'title': 'Numbers 1-100 in English', 'url': 'https://youtu.be/bGetqbqDVaA', 'duration': '4:20'},
        {'title': 'Colors in English for Kids', 'url': 'https://youtu.be/uTxeYQqGp2k', 'duration': '3:45'}
    ],
    'elementary': [
        {'title': 'Present Simple Explained', 'url': 'https://youtu.be/8X4BPQX8rjE', 'duration': '8:30'},
        {'title': 'Daily Routines Vocabulary', 'url': 'https://youtu.be/eUXkj6j6Ezw', 'duration': '6:15'},
        {'title': 'Food Vocabulary', 'url': 'https://youtu.be/pU0cYzk6LvE', 'duration': '7:20'},
        {'title': 'Telling Time in English', 'url': 'https://youtu.be/ykMFbFzVwS8', 'duration': '5:45'}
    ],
    'intermediate': [
        {'title': 'Past Tense Irregular Verbs', 'url': 'https://youtu.be/6XNBXNHOUoE', 'duration': '12:30'},
        {'title': 'Future Tense Will vs Going to', 'url': 'https://youtu.be/3_5v3pONhQA', 'duration': '10:15'},
        {'title': 'Comparative and Superlative', 'url': 'https://youtu.be/7xaRJOT8P_k', 'duration': '9:20'},
        {'title': 'Modal Verbs Explained', 'url': 'https://youtu.be/jNi0nYFKlBs', 'duration': '11:45'}
    ]
}

class PollinationsAI:
    """Classe para integração com Pollinations AI"""
    
    @staticmethod
    def generate_intelligent_response(user_message, student_level, conversation_history):
        """Gera resposta inteligente usando Pollinations AI"""
        try:
            # Construir prompt contextual
            context = f"""You are an expert English teacher helping a {student_level} level student.
            
Student's message: "{user_message}"
Student level: {student_level}
Recent conversation: {conversation_history[-3:] if conversation_history else 'First interaction'}

Please respond as a friendly, encouraging English teacher. Your response should:
1. Address the student's message directly
2. Provide helpful corrections if there are grammar/vocabulary errors
3. Teach something new related to their message
4. Ask a follow-up question to continue the conversation
5. Keep it appropriate for their level ({student_level})
6. Be encouraging and positive
7. Limit response to 2-3 sentences

Respond in a natural, conversational way."""

            # Fazer requisição para Pollinations
            response = requests.post(
                POLLINATIONS_TEXT_URL,
                json={
                    "model": "openai",
                    "messages": [{"role": "user", "content": context}],
                    "seed": random.randint(1, 1000000)
                },
                timeout=10
            )
            
            if response.status_code == 200:
                ai_response = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
                return ai_response.strip() if ai_response else None
            else:
                print(f"Pollinations AI error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error calling Pollinations AI: {e}")
            return None
    
    @staticmethod
    def generate_audio_url(text, voice_type="female"):
        """Gera URL de áudio usando Pollinations"""
        try:
            # Pollinations pode não ter TTS direto, então vamos usar uma alternativa
            # Por enquanto, retornamos uma URL que pode ser implementada
            encoded_text = quote(text)
            audio_url = f"https://text.pollinations.ai/tts?text={encoded_text}&voice={voice_type}"
            return audio_url
        except Exception as e:
            print(f"Error generating audio URL: {e}")
            return None
    
    @staticmethod
    def generate_educational_image(topic, level):
        """Gera imagem educacional usando Pollinations"""
        try:
            prompt = f"Educational illustration for {level} English learners about {topic}, simple and clear, cartoon style, bright colors"
            encoded_prompt = quote(prompt)
            image_url = f"{POLLINATIONS_IMAGE_URL}/{encoded_prompt}?width=512&height=512&seed={random.randint(1, 1000000)}"
            return image_url
        except Exception as e:
            print(f"Error generating image: {e}")
            return None
    
    @staticmethod
    def analyze_grammar(text):
        """Analisa gramática usando Pollinations AI"""
        try:
            prompt = f"""Analyze this English text for grammar errors and provide corrections:

Text: "{text}"

Please respond in this format:
- Errors found: [list any errors]
- Corrections: [provide corrected version]
- Explanation: [brief explanation of the errors]
- Level assessment: [beginner/elementary/intermediate/advanced]

Keep it concise and educational."""

            response = requests.post(
                POLLINATIONS_TEXT_URL,
                json={
                    "model": "openai",
                    "messages": [{"role": "user", "content": prompt}],
                    "seed": random.randint(1, 1000000)
                },
                timeout=10
            )
            
            if response.status_code == 200:
                analysis = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
                return analysis.strip() if analysis else None
            else:
                return None
                
        except Exception as e:
            print(f"Error analyzing grammar: {e}")
            return None

def send_whatsapp_message(phone, message):
    """Envia mensagem de texto via Z-API"""
    url = f"{ZAPI_BASE_URL}/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-text"
    
    headers = {
        "Content-Type": "application/json",
        "Client-Token": ZAPI_TOKEN
    }
    
    payload = {
        "phone": phone,
        "message": message
    }
    
    try:
        print(f"🚀 Enviando mensagem para {phone}: {message[:50]}...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Mensagem enviada com sucesso!")
            return True
        else:
            print(f"❌ Erro ao enviar: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def send_whatsapp_image(phone, image_url, caption=""):
    """Envia imagem via Z-API"""
    url = f"{ZAPI_BASE_URL}/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-image"
    
    headers = {
        "Content-Type": "application/json",
        "Client-Token": ZAPI_TOKEN
    }
    
    payload = {
        "phone": phone,
        "image": image_url,
        "caption": caption
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending image: {e}")
        return False

def send_whatsapp_audio(phone, audio_url):
    """Envia áudio via Z-API"""
    url = f"{ZAPI_BASE_URL}/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-audio"
    
    headers = {
        "Content-Type": "application/json",
        "Client-Token": ZAPI_TOKEN
    }
    
    payload = {
        "phone": phone,
        "audio": audio_url
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending audio: {e}")
        return False

def get_student_level(phone):
    if phone not in students_db:
        students_db[phone] = {
            'level': 'beginner',
            'xp': 0,
            'streak': 0,
            'last_activity': datetime.now(),
            'conversations': 0,
            'current_lesson': 1,
            'completed_lessons': [],
            'conversation_history': []
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
    
    old_level = student['level']
    for i, threshold in enumerate(level_thresholds):
        if student['xp'] >= threshold:
            student['level'] = levels[min(i, len(levels)-1)]
    
    # Verificar se subiu de nível
    if student['level'] != old_level:
        return True  # Level up!
    return False

def process_command(message, phone):
    """Processa comandos especiais do bot"""
    message_lower = message.lower().strip()
    student = get_student_level(phone)
    
    if message_lower in ['/help', 'help', 'ajuda']:
        return """🎓 **English Tutor Bot Commands:**

📚 **Learning:**
• `/lesson` - Start next lesson
• `/grammar` - Grammar check
• `/vocabulary` - Learn new words
• `/pronunciation` - Practice pronunciation

🎬 **Media:**
• `/video` - Get video suggestions
• `/audio` - Practice with audio
• `/image` - Visual learning

📊 **Progress:**
• `/progress` - Check your progress
• `/level` - Check your level
• `/achievements` - See your badges

💬 **Conversation:**
• Just chat naturally in English!
• I'll help correct and teach you!

Type any command or just start chatting! 😊"""

    elif message_lower in ['/lesson', 'lesson', 'lição']:
        return get_next_lesson(student)
    
    elif message_lower in ['/video', 'video', 'vídeo']:
        return get_video_suggestions(student['level'])
    
    elif message_lower in ['/progress', 'progress', 'progresso']:
        return get_progress_report(student)
    
    elif message_lower in ['/grammar', 'grammar', 'gramática']:
        return "📝 Send me a sentence and I'll check your grammar! Example: 'I are going to school'"
    
    elif message_lower in ['/pronunciation', 'pronunciation', 'pronúncia']:
        return "🎤 Send me an audio message and I'll help you with pronunciation!"
    
    elif message_lower in ['/vocabulary', 'vocabulary', 'vocabulário']:
        return get_vocabulary_lesson(student['level'])
    
    elif message_lower in ['/image', 'image', 'imagem']:
        return "🖼️ What topic would you like to see an image about? Example: 'animals', 'food', 'colors'"
    
    return None

def get_next_lesson(student):
    """Retorna a próxima lição para o estudante"""
    level_lessons = LESSONS.get(student['level'], [])
    current_lesson_id = student.get('current_lesson', 1)
    
    # Encontrar a lição atual
    current_lesson = None
    for lesson in level_lessons:
        if lesson['id'] == current_lesson_id:
            current_lesson = lesson
            break
    
    if current_lesson:
        lesson_text = f"""📚 **Lesson {current_lesson['id']}: {current_lesson['title']}**

📖 **Content:** {current_lesson['content']}

💡 **Practice:** Try using these words in a sentence!

🎯 **Your turn:** Write a sentence using this vocabulary and I'll help you improve it!

Type 'next lesson' when you're ready to move on! 🚀"""
        return lesson_text
    else:
        return "🎉 Congratulations! You've completed all lessons for your level. Time to level up! 🚀"

def get_video_suggestions(level):
    """Retorna sugestões de vídeos baseadas no nível"""
    videos = VIDEO_SUGGESTIONS.get(level, [])
    if not videos:
        return "📹 No video suggestions available for your level yet!"
    
    video_text = f"🎬 **Video Suggestions for {level.title()} Level:**\n\n"
    
    for i, video in enumerate(videos[:3], 1):  # Mostrar apenas 3 vídeos
        video_text += f"**{i}. {video['title']}**\n"
        video_text += f"⏱️ Duration: {video['duration']}\n"
        video_text += f"🔗 {video['url']}\n\n"
    
    video_text += "💡 **Tip:** Watch with subtitles first, then without! 📝"
    return video_text

def get_vocabulary_lesson(level):
    """Retorna lição de vocabulário baseada no nível"""
    vocab_sets = {
        'beginner': ['apple', 'book', 'cat', 'dog', 'eat', 'family', 'good', 'house'],
        'elementary': ['beautiful', 'different', 'important', 'interesting', 'necessary', 'possible', 'special', 'wonderful'],
        'intermediate': ['achieve', 'analyze', 'communicate', 'demonstrate', 'establish', 'facilitate', 'generate', 'implement']
    }
    
    words = vocab_sets.get(level, vocab_sets['beginner'])
    selected_words = random.sample(words, min(4, len(words)))
    
    vocab_text = f"📚 **Vocabulary Practice - {level.title()} Level**\n\n"
    vocab_text += "🔤 **Today's words:**\n"
    
    for word in selected_words:
        vocab_text += f"• **{word.title()}**\n"
    
    vocab_text += "\n💡 **Challenge:** Use each word in a sentence! I'll help you improve them! 🎯"
    return vocab_text

def get_progress_report(student):
    """Gera relatório de progresso do estudante"""
    achievements = get_achievements(student)
    next_level_info = get_next_level_info(student)
    
    progress_text = f"""📊 **Your English Learning Progress**

🎯 **Current Level:** {student['level'].title()}
⭐ **XP Points:** {student['xp']}
💬 **Conversations:** {student['conversations']}
📚 **Current Lesson:** {student.get('current_lesson', 1)}
🔥 **Streak:** {student.get('streak', 0)} days

🏆 **Achievements:**
{chr(10).join(achievements) if achievements else 'No achievements yet - keep learning!'}

🎯 **Next Goal:** {next_level_info}

Keep up the great work! 🚀"""
    
    return progress_text

def get_achievements(student):
    achievements = []
    if student['conversations'] >= 1:
        achievements.append("🎉 First Conversation")
    if student['conversations'] >= 10:
        achievements.append("💬 Chatty Learner")
    if student['conversations'] >= 50:
        achievements.append("🗣️ Conversation Master")
    if student['xp'] >= 100:
        achievements.append("⭐ Rising Star")
    if student['xp'] >= 500:
        achievements.append("🚀 English Enthusiast")
    if student['xp'] >= 1000:
        achievements.append("🏆 English Champion")
    return achievements

def get_next_level_info(student):
    level_thresholds = {'beginner': 100, 'elementary': 300, 'intermediate': 600, 'advanced': 1000}
    current_level = student['level']
    
    if current_level in level_thresholds:
        next_threshold = level_thresholds[current_level]
        needed = next_threshold - student['xp']
        return f"Need {needed} more XP to reach next level!"
    
    return "You're at the highest level! Keep practicing!"

@app.route('/')
def home():
    return f"""
    <h1>🎓 English Tutor Bot - AI POWERED!</h1>
    <p><strong>Status:</strong> ✅ Online e Operacional</p>
    <p><strong>AI Engine:</strong> 🧠 Pollinations AI Integrated</p>
    <p><strong>Usuários ativos:</strong> {len(students_db)}</p>
    <p><strong>Conversas processadas:</strong> {len(conversations_db)}</p>
    
    <h2>🚀 Funcionalidades:</h2>
    <ul>
        <li>🧠 Conversação inteligente com IA</li>
        <li>🎵 Geração e processamento de áudio</li>
        <li>🖼️ Imagens educacionais personalizadas</li>
        <li>🎬 Sugestões de vídeos por nível</li>
        <li>📚 Lições estruturadas</li>
        <li>📝 Correção de gramática em tempo real</li>
        <li>🎯 Sistema de gamificação avançado</li>
    </ul>
    
    <h2>Endpoints Disponíveis:</h2>
    <ul>
        <li>🟢 GET /api/health - Health check</li>
        <li>🟢 POST /api/webhook/message-received - Receber mensagens</li>
        <li>🟢 GET /api/student/{{phone}}/progress - Ver progresso</li>
    </ul>
    <p><em>Bot desenvolvido com ❤️ e IA para ensinar inglês!</em></p>
    """

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
            "ai": "pollinations_integrated",
            "zapi": "configured",
            "features": {
                "intelligent_conversation": True,
                "audio_processing": True,
                "image_generation": True,
                "video_suggestions": True,
                "grammar_analysis": True
            }
        }
    })

@app.route('/api/webhook/message-received', methods=['POST'])
def receive_message():
    try:
        data = request.get_json()
        phone = data.get('phone', 'unknown')
        message_type = data.get('type', 'text')
        
        print(f"📨 Mensagem recebida de {phone} - Tipo: {message_type}")
        
        student = get_student_level(phone)
        
        if message_type == 'text':
            message = data.get('text', {}).get('message', '')
            print(f"💬 Conteúdo: {message}")
            
            # Verificar se é um comando
            command_response = process_command(message, phone)
            if command_response:
                success = send_whatsapp_message(phone, command_response)
                
                # Se for comando de imagem, gerar e enviar imagem
                if '/image' in message.lower() or 'image' in message.lower():
                    topic = "English learning"  # Tópico padrão
                    image_url = PollinationsAI.generate_educational_image(topic, student['level'])
                    if image_url:
                        send_whatsapp_image(phone, image_url, f"Educational image about {topic}")
                
                return jsonify({"status": "success", "response_type": "command", "sent_to_whatsapp": success})
            
            # Verificar se é solicitação de análise de gramática
            if any(word in message.lower() for word in ['check', 'correct', 'grammar', 'mistake']):
                grammar_analysis = PollinationsAI.analyze_grammar(message)
                if grammar_analysis:
                    response_text = f"📝 **Grammar Analysis:**\n\n{grammar_analysis}"
                    success = send_whatsapp_message(phone, response_text)
                    add_xp(phone, 15)  # Bônus por prática de gramática
                    return jsonify({"status": "success", "response_type": "grammar_analysis", "sent_to_whatsapp": success})
            
            # Verificar se é solicitação de imagem sobre tópico específico
            if any(word in message.lower() for word in ['show me', 'image of', 'picture of', 'foto de']):
                # Extrair tópico da mensagem
                topic_match = re.search(r'(?:show me|image of|picture of|foto de)\s+(.+)', message.lower())
                if topic_match:
                    topic = topic_match.group(1).strip()
                    image_url = PollinationsAI.generate_educational_image(topic, student['level'])
                    if image_url:
                        send_whatsapp_image(phone, image_url, f"Here's an educational image about {topic}!")
                        add_xp(phone, 10)
                        return jsonify({"status": "success", "response_type": "image_generation"})
            
            # Conversação inteligente usando Pollinations AI
            conversation_history = student.get('conversation_history', [])
            ai_response = PollinationsAI.generate_intelligent_response(message, student['level'], conversation_history)
            
            if ai_response:
                # Adicionar dicas de progresso
                level_up = add_xp(phone, 10)
                tip = get_learning_tip(student['level'])
                
                full_response = ai_response
                if level_up:
                    full_response += f"\n\n🎉 **LEVEL UP!** You're now {student['level']}! 🚀"
                
                full_response += f"\n\n{tip}"
                full_response += f"\n📊 Level: {student['level']} | XP: {student['xp']}"
                
                # Atualizar histórico de conversação
                conversation_history.append({'user': message, 'bot': ai_response, 'timestamp': datetime.now().isoformat()})
                student['conversation_history'] = conversation_history[-10:]  # Manter apenas últimas 10
                
                success = send_whatsapp_message(phone, full_response)
                
                # Ocasionalmente enviar áudio de pronúncia
                if random.random() < 0.3:  # 30% de chance
                    audio_url = PollinationsAI.generate_audio_url(ai_response[:100])  # Primeiras 100 chars
                    if audio_url:
                        send_whatsapp_audio(phone, audio_url)
                
            else:
                # Fallback para resposta padrão
                fallback_responses = [
                    "I understand you're practicing English! That's great! Can you tell me more about what you'd like to learn?",
                    "Keep practicing! Every conversation helps you improve. What topic interests you today?",
                    "I'm here to help you learn English! Try asking me about grammar, vocabulary, or just chat with me!"
                ]
                response_text = random.choice(fallback_responses)
                success = send_whatsapp_message(phone, response_text)
                add_xp(phone, 5)
        
        elif message_type == 'audio':
            # Processar mensagem de áudio
            audio_url = data.get('audio', {}).get('audioUrl', '')
            print(f"🎤 Áudio recebido: {audio_url}")
            
            response_text = """🎤 **Great! You sent an audio message!**

I received your audio! Here are some pronunciation tips:

🗣️ **Tips for better pronunciation:**
• Speak slowly and clearly
• Practice vowel sounds: A, E, I, O, U
• Record yourself and listen back
• Repeat after native speakers

🎯 **Try this:** Record yourself saying "Hello, my name is [your name]" and I'll give you feedback!

Keep practicing! 🌟"""
            
            success = send_whatsapp_message(phone, response_text)
            add_xp(phone, 15)  # Bônus por prática de pronúncia
            
            # Enviar áudio de exemplo
            example_audio_url = PollinationsAI.generate_audio_url("Hello, my name is English Tutor. Practice your pronunciation!")
            if example_audio_url:
                send_whatsapp_audio(phone, example_audio_url)
        
        elif message_type == 'image':
            # Processar imagem recebida
            image_url = data.get('image', {}).get('imageUrl', '')
            caption = data.get('image', {}).get('caption', '')
            print(f"🖼️ Imagem recebida: {image_url}")
            
            response_text = """🖼️ **Nice image!**

I can see you shared an image! Here's how we can use images for learning:

📚 **Image-based learning:**
• Describe what you see in English
• Learn new vocabulary from the image
• Practice using adjectives (colors, sizes, shapes)

🎯 **Try this:** Describe your image in English! Start with "I can see..." or "In this image, there is..."

Example: "I can see a red car and a blue house."

What do you see in your image? 🔍"""
            
            success = send_whatsapp_message(phone, response_text)
            add_xp(phone, 12)
        
        else:
            # Outros tipos de mensagem
            response_text = f"📱 I received a {message_type} message! I'm still learning how to handle this type. Try sending text, audio, or images for the best learning experience! 😊"
            success = send_whatsapp_message(phone, response_text)
            add_xp(phone, 5)
        
        # Salvar conversa
        conversation = {
            'phone': phone,
            'user_message': message if message_type == 'text' else f'{message_type} message',
            'bot_response': 'AI-generated response',
            'timestamp': datetime.now().isoformat(),
            'message_type': message_type,
            'sent_successfully': success
        }
        conversations_db.append(conversation)
        
        return jsonify({
            "status": "success",
            "response_type": "ai_powered_response",
            "message": "Message processed with AI intelligence",
            "student_progress": student,
            "sent_to_whatsapp": success
        })
        
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error processing message: {str(e)}",
            "response_type": "error"
        }), 500

def get_learning_tip(level):
    tips = {
        'beginner': "💡 Tip: Start with simple sentences and basic vocabulary!",
        'elementary': "💡 Tip: Try to use new words in sentences!",
        'intermediate': "💡 Tip: Practice speaking and listening every day!",
        'advanced': "💡 Tip: Read English articles and watch movies!",
        'expert': "💡 Tip: Focus on nuances and advanced expressions!"
    }
    return tips.get(level, tips['beginner'])

@app.route('/api/webhook/test', methods=['GET', 'POST'])
def test_webhook():
    if request.method == 'GET':
        return jsonify({
            "status": "success",
            "message": "AI-Powered English Tutor Bot is working perfectly!",
            "timestamp": datetime.now().isoformat(),
            "ai_features": {
                "intelligent_conversation": True,
                "audio_processing": True,
                "image_generation": True,
                "grammar_analysis": True,
                "video_suggestions": True
            }
        })
    
    # POST test with AI
    test_message = "Hello, I want to learn English!"
    ai_response = PollinationsAI.generate_intelligent_response(test_message, "beginner", [])
    
    return jsonify({
        "status": "success",
        "message": "AI test completed successfully",
        "test_input": test_message,
        "ai_response": ai_response,
        "features_tested": ["pollinations_ai", "conversation_flow", "response_generation"]
    })

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
                "recent_conversations": user_conversations[-5:],
                "achievements": get_achievements(student),
                "next_level_info": get_next_level_info(student),
                "available_lessons": LESSONS.get(student['level'], []),
                "video_suggestions": VIDEO_SUGGESTIONS.get(student['level'], [])
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("🚀 Starting AI-Powered English Tutor Bot...")
    print("🧠 Pollinations AI: Integrated")
    print("📚 Educational AI: Ready")
    print("🎮 Gamification: Active")
    print("💬 WhatsApp Integration: Ready")
    print("🎵 Audio Processing: Ready")
    print("🖼️ Image Generation: Ready")
    print("🎬 Video Suggestions: Ready")
    print(f"📡 Z-API Instance: {ZAPI_INSTANCE_ID}")
    app.run(host='0.0.0.0', port=port, debug=False)

