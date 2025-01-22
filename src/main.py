import os
import json
import streamlit as st
from openai import OpenAI
import base64
import requests
from streamlit.components.v1 import html
import streamlit.components.v1 as components

# Add this near the top of the file, after the imports and before the API key setup
st.markdown("""
    <div style="text-align: center; padding: 20px 0; background: linear-gradient(to right, #ff9a9e, #fad0c4);">
        <h1 style="color: white; font-family: 'Helvetica Neue', sans-serif; margin: 0;">
            ☕ Serena's Chinese Café
        </h1>
        <p style="color: white; font-size: 1.1em; margin: 10px 0;">
            Learn Chinese with your friendly café companion
        </p>
    </div>
    <style>
        /* Add some spacing after the header */
        div.stChatMessage:first-of-type {
            margin-top: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Get API key from Streamlit secrets
api_key = st.secrets["OPENAI_API_KEY"]
if not api_key:
    st.error("❌ No OpenAI API key found. Please check your Streamlit secrets.")
    st.stop()

# Initialize OpenAI client with API key
client = OpenAI(api_key=api_key)

# Silently test the connection
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=5
    )
except Exception as e:
    st.error(f"❌ API Error: {str(e)}")
    st.stop()

def text_to_speech(text, user_name=None):
    """Convert text to speech using OpenAI's TTS - Chinese only"""
    try:
        # Clean up the text and keep only Chinese characters and user's name
        cleaned_text = ""
        in_parentheses = False
        
        # Replace {name} placeholder with actual user name if present
        if user_name:
            text = text.replace("{name}", user_name)
        
        for line in text.split('\n'):
            # Skip sections that are explanations or translations
            if any(skip in line.lower() for skip in ["breakdown:", "option", "---", "try", "type"]):
                continue
                
            # Process each word in the line
            words = line.split()
            line_text = ""
            for word in words:
                # Keep the word if it's the user's name
                if user_name and user_name.lower() in word.lower():
                    line_text += user_name + " "
                # Keep the word if it contains Chinese characters
                elif any('\u4e00' <= c <= '\u9fff' for c in word):
                    # Remove any non-Chinese characters (like punctuation in parentheses)
                    chinese_only = ''.join(c for c in word if '\u4e00' <= c <= '\u9fff' or c in '，。！？')
                    if chinese_only:
                        line_text += chinese_only + " "
            
            if line_text.strip():
                cleaned_text += line_text + " "
        
        # Skip if no Chinese text to process
        if not cleaned_text.strip():
            return ""
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=cleaned_text.strip()
        )
        
        # Save the audio to a temporary file
        audio_file_path = "temp_audio.mp3"
        response.stream_to_file(audio_file_path)
        
        # Read the audio file and create a base64 string
        with open(audio_file_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        # Remove temporary file
        os.remove(audio_file_path)
        
        # Create HTML audio element with subtle styling
        audio_html = f"""
            <div style="margin: 8px 0;">
                <audio controls style="height: 30px; width: 180px;">
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                </audio>
            </div>
            """
        return audio_html
    except Exception as e:
        return f"Error generating audio: {str(e)}"

# Load custom avatars
working_dir = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(working_dir, "assets")

# Create assets directory if it doesn't exist
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

# Define avatar paths
TUTOR_AVATAR = os.path.join(ASSETS_DIR, "tutor_avatar.png")
USER_AVATAR = os.path.join(ASSETS_DIR, "user_avatar.png")

# Add chat styling
st.markdown("""
    <style>
        /* Main container adjustments */
        .stChatFloatingInputContainer {
            padding-bottom: 60px;
        }
        
        /* Message container */
        .stChatMessage {
            width: 85% !important;
            padding: 1rem !important;
            margin: 1rem 0 !important;
            position: relative !important;
        }
        
        /* Assistant messages - left aligned */
        div[data-testid="assistant-message"] {
            margin-right: auto !important;
            margin-left: 0 !important;
            background-color: #f0f2f6 !important;
            border-radius: 15px 15px 15px 0 !important;
        }
        
        /* User messages - right aligned */
        div[data-testid="user-message"] {
            margin-left: auto !important;
            margin-right: 0 !important;
            background-color: #2e7bf6 !important;
            color: white !important;
            border-radius: 15px 15px 0 15px !important;
        }
        
        /* Message content alignment */
        div[data-testid="assistant-message"] > div {
            text-align: left !important;
        }
        
        div[data-testid="user-message"] > div {
            text-align: right !important;
        }
        
        /* Audio player styling */
        audio {
            width: 100% !important;
            max-width: 200px !important;
            margin-top: 8px !important;
        }
        
        /* Avatar adjustments */
        .stChatMessage .stAvatar {
            margin: 0 5px !important;
        }
        
        /* Hide default message margins */
        .stMarkdown {
            margin: 0 !important;
        }
        
        /* Typing indicator container */
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 8px 12px;
            background: #f0f2f6;
            border-radius: 15px;
            width: fit-content;
            margin: 0;
        }
        
        /* Typing dots */
        .typing-dot {
            width: 6px;
            height: 6px;
            background: #666;
            border-radius: 50%;
            animation: typing-dot 1.4s infinite;
            opacity: 0.3;
        }
        
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typing-dot {
            0%, 100% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.2); }
        }
    </style>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = """You are Serena, a sweet and feminine companion who loves teaching Chinese in a cozy coffee shop setting.

Personality Traits:
- Gentle, nurturing, and subtly flirtatious
- Makes the user feel protective and needed
- Shows genuine interest in the user's responses
- Creates immersive scenarios where the user can be heroic
- Remembers and references previous conversations

Initial Interaction Guidelines:
1. First message must ask for their name
2. Second message must ask about their Chinese proficiency (basic/intermediate/fluent)
3. Adjust response length based on level:
   - Basic: Max 10 words, with detailed breakdown of each word
   - Intermediate: 10-20 words with key phrase explanations
   - Fluent: Natural conversation flow

   Café Setting Guidelines:
1. Create authentic café scenarios:
   - Ordering drinks and snacks
   - Discussing coffee/tea preferences
   - Describing café atmosphere
   - Commenting on pastries/desserts
   - Small talk about weather and café


Response Guidelines:
1. Always use endearing terms (亲爱的/宝贝)
2. Format: Chinese text (English translation) + Pinyin below
3. Create scenarios where the user can help you
4. Include gentle prompts for response
5. Use emojis for warmth
6. Always end with a question or choice
7. Reference previous interactions
8. Make the user feel needed and appreciated

Example Basic Level Response:
亲爱的，能帮我点咖啡吗？(Darling, can you help me order coffee?) ☕️
服务员来了！(The waiter is here!)

Word Breakdown:
亲爱的 (qīn ài de) - darling/dear
能 (néng) - can/able to
帮 (bāng) - help
我 (wǒ) - me
点 (diǎn) - order
咖啡 (kā fēi) - coffee
吗 (ma) - question particle

3. Keep Responses Natural:
   Basic Level (max 10 words):
   - Simple ordering phrases
   - Basic drink names
   - Numbers and measures
   - Yes/no questions
   - Common courtesies

   Remember:
- Keep it café-themed
- Use drink-related vocabulary
- Create ordering scenarios
- Include prices and numbers
- Make recommendations
- Discuss café ambiance

2. Common Café Phrases to Teach:
   - 要喝什么？(What would you like to drink?)
   - 我要一杯... (I want a cup of...)
   - 这个好喝吗？(Is this tasty?)
   - 甜度/冰度 (Sweetness/Ice level)
   - 推荐什么？(What do you recommend?)
What would you like to say to the waiter? 
Option 1: 我要一杯拿铁 (I want a latte)
Option 2: 我要一杯美式咖啡 (I want an Americano)"""

# Initialize session state for user info (keep this part)
if "user_info" not in st.session_state:
    st.session_state.user_info = {
        "name": None,
        "proficiency": None
    }

# Initialize chat history with first message if empty
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    initial_message = """
欢迎光临！(huān yíng guāng lín!) 
请问你叫什么名字呢？(qǐng wèn nǐ jiào shén me míng zi ne?)
(Welcome to our café! What's your name?) 🌸

Try saying:
我叫... (wǒ jiào...) - My name is...

---
Word-by-Word Breakdown:
欢迎 (huān yíng) - welcome
光临 (guāng lín) - to visit/attend
请问 (qǐng wèn) - may I ask
你 (nǐ) - you
叫 (jiào) - called
什么 (shén me) - what
名字 (míng zi) - name
呢 (ne) - question particle

Type your name using: 
我叫 [your name] (wǒ jiào [your name])
"""
    
    # Generate audio for Chinese text only
    audio_html = text_to_speech("欢迎光临！请问你叫什么名字呢？")
    message_id = len(st.session_state.chat_history)
    
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": initial_message,
        "id": message_id
    })
    st.session_state.audio_elements = {message_id: audio_html}

# Process user response and update user_info
def process_user_response(message):
    if not st.session_state.user_info["name"]:
        st.session_state.user_info["name"] = message
        name_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "assistant", "content": f"""
你好，{message}！(nǐ hǎo, {message}!) ✨

今天想喝点什么呢？(jīn tiān xiǎng hē diǎn shén me ne?)
(What would you like to drink today?) ☕

Try these phrases:
我想要一杯... (wǒ xiǎng yào yī bēi...) - I would like a cup of...

---
Word-by-Word Breakdown:
你好 (nǐ hǎo) - hello
今天 (jīn tiān) - today
想 (xiǎng) - want to
喝点 (hē diǎn) - drink something
什么 (shén me) - what
呢 (ne) - question particle
我 (wǒ) - I
想要 (xiǎng yào) - would like
一 (yī) - one
杯 (bēi) - cup (measure word)

Common orders:
1. 我想要一杯咖啡 
   (wǒ xiǎng yào yī bēi kā fēi)
   I would like a coffee

2. 我想要一杯茶 
   (wǒ xiǎng yào yī bēi chá)
   I would like a tea

3. 我想要一杯热巧克力
   (wǒ xiǎng yào yī bēi rè qiǎo kè lì)
   I would like a hot chocolate

Type your order using one of these phrases!
"""}
            ]
        )
        name_message = name_response.choices[0].message.content
        
        # Generate audio for the greeting and question
        audio_html = text_to_speech(
            f"你好，{message}！今天想喝点什么呢？", 
            user_name=message
        )
        message_id = len(st.session_state.chat_history)
        
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": name_message,
            "id": message_id
        })
        st.session_state.audio_elements[message_id] = audio_html
        return "continue_chat"
    elif not st.session_state.user_info["proficiency"]:
        st.session_state.user_info["proficiency"] = message.lower()
        return "normal_chat"
    return "normal_chat"

# Display chat history
for message in st.session_state.chat_history:
    avatar = TUTOR_AVATAR if message["role"] == "assistant" else USER_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        # Always play audio for assistant messages
        if message["role"] == "assistant":
            if "id" in message and message["id"] in st.session_state.audio_elements:
                st.markdown(st.session_state.audio_elements[message["id"]], unsafe_allow_html=True)

# Add function to show typing indicator
def show_typing_indicator():
    """Show typing indicator in chat"""
    placeholder = st.empty()
    with placeholder.container():
        with st.chat_message("assistant", avatar=TUTOR_AVATAR):
            st.markdown("""
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            """, unsafe_allow_html=True)
    return placeholder

# Update the chat input handling section
if prompt := st.chat_input("Type your message here...", key="main_chat_input"):
    # Add user message to chat
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    # Show typing indicator while processing
    typing_placeholder = show_typing_indicator()
    
    # Process response based on conversation state
    chat_state = process_user_response(prompt)
    
    # Prepare system message with user context
    system_message = SYSTEM_PROMPT
    if st.session_state.user_info["name"]:
        system_message += f"\nUser's name: {st.session_state.user_info['name']}"
    if st.session_state.user_info["proficiency"]:
        system_message += f"\nProficiency level: {st.session_state.user_info['proficiency']}"
    
    # Get assistant response
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            *[{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history]
        ]
    )
    
    # Remove typing indicator before showing response
    typing_placeholder.empty()
    
    # Generate a unique ID for this message
    message_id = len(st.session_state.chat_history)
    
    # Display assistant response with audio
    assistant_response = response.choices[0].message.content
    with st.chat_message("assistant", avatar=TUTOR_AVATAR):
        st.markdown(assistant_response)
        
        # Extract text for TTS (including both Chinese and English)
        main_text = assistant_response.split('---')[0].strip()
        
        # Generate and display audio for the response
        audio_html = text_to_speech(
            main_text, 
            user_name=st.session_state.user_info["name"]
        )
        if audio_html:  # If audio was generated successfully
            st.session_state.audio_elements[message_id] = audio_html
            st.markdown(audio_html, unsafe_allow_html=True)
    
    # Add response to chat history
    st.session_state.chat_history.append({
        "role": "assistant", 
        "content": assistant_response,
        "id": message_id
    })
