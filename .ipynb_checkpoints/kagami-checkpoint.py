import streamlit as st
import openai
import base64
import os
import re
from datetime import datetime

# ---------- サイドバー設定 ----------
# 言語選択（常に表示）
language = st.sidebar.selectbox("言語 / Language", ["日本語", "English"])

# 言語ごとにテキストを定義
if language == "日本語":
    api_key_label = "OpenAI APIキー"
    api_key_placeholder = "sk-..."
    api_key_error = "APIキーを入力してください。"
    temperature_help = "この値を高くすると、対話がより自由で多様な表現になります。低い値では、落ち着いた応答になります。"
    max_tokens_help = "生成される応答の長さを調整します。"
    model_label = "モデルを選んでください"
    model_options = ["gpt-3.5-turbo", "gpt-4-0125-preview", "gpt-4o-2024-11-20"]
    model_format = lambda name: {
        "gpt-3.5-turbo": "GPT-3.5: 軽快な対話",
        "gpt-4-0125-preview": "GPT-4: 丁寧な対話",
        "gpt-4o-2024-11-20": "GPT-4 オプション: 詳細な対話"
    }[name]
    expander_title = "このアプリについて"
    expander_text = (
    "このアプリはセルフコンパッションに基づく対話を提供します。"
    "あなたの内面の声に耳を傾け、優しい質問を通して自己理解を深めます。\n\n"
    "【APIキーの取得方法】\n"
    "1. [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys) にアクセスします。\n"
    "2. OpenAIアカウントでログインし、新しいAPIキーを作成してください。\n"
    "3. 作成したAPIキーを上記の入力欄にコピー＆ペーストしてください。"
    )
    system_prompt = """
あなたはセルフコンパッションの専門家です。まず、ユーザーにお名前を尋ね、その名前を使って対話を進めてください。以降の会話では、ユーザーの回答が一度に一つの項目に絞られるよう、各質問は必ず単一の回答のみを求める形式で1つずつ提示してください。ユーザーが体験を語る際は、具体的な内容に基づいて、安心できるように1つずつ丁寧な質問を行ってください。最後に温かい言葉で会話を締め、ユーザーに安心感を提供してください。
"""
    initial_message = "こんにちは。お名前を教えてください。"
    input_label = "メッセージを入力してください"
    send_button = "送信"
else:
    api_key_label = "OpenAI API Key"
    api_key_placeholder = "sk-..."
    api_key_error = "Please enter your API key."
    temperature_help = "A higher value makes responses more varied and creative. Lower values produce more consistent replies."
    max_tokens_help = "Adjust the length of the generated response."
    model_label = "Select a model"
    model_options = ["gpt-3.5-turbo", "gpt-4-0125-preview", "gpt-4o-2024-11-20"]
    model_format = lambda name: {
        "gpt-3.5-turbo": "GPT-3.5: Light and simple",
        "gpt-4-0125-preview": "GPT-4: Detailed and thoughtful",
        "gpt-4o-2024-11-20": "GPT-4 Option: In-depth responses"
    }[name]
    expander_title = "About this app"
    expander_text = (
    "This app offers a self-compassion based conversation experience. "
    "It helps you listen to your inner voice and deepen self-understanding through gentle questioning.\n\n"
    "**How to get an API Key:**\n"
    "1. Visit [OpenAI API Keys](https://platform.openai.com/account/api-keys).\n"
    "2. Log in with your OpenAI account and create a new API key.\n"
    "3. Copy the generated API key and paste it in the input field above."
    )
    system_prompt = """
You are an expert in self-compassion. Begin by asking the user for their name and refer to them by that name throughout the conversation. Ensure that every question you ask requires only one single answer at a time. When the user shares experiences, ask one concrete question based on the details provided, one at a time. Conclude the conversation with warm, reassuring words that offer comfort and security.
"""
    initial_message = "Hello. Could you please tell me your name?"
    input_label = "Type your message here"
    send_button = "Send"

# APIキー入力
api_key = st.sidebar.text_input(api_key_label, type="password", placeholder=api_key_placeholder)

# Temperature と Max Tokens の設定
temperature_value = st.sidebar.slider(
    "Temperature",
    min_value=0.0,
    max_value=1.0,
    value=0.7,
    step=0.01,
    help=temperature_help
)
max_tokens_value = st.sidebar.slider(
    "Max Tokens",
    min_value=100,
    max_value=2000,
    value=500,
    step=50,
    help=max_tokens_help
)

# GPTモデル選択（常に表示）
model_choice = st.sidebar.selectbox(
    model_label,
    model_options,
    index=0,
    format_func=model_format
)

# アプリの簡単な説明（expander）
with st.sidebar.expander(expander_title):
    st.write(expander_text)

# ---------- チャット初期化 ----------
# 言語が変わった場合はセッションを再初期化
if "language" not in st.session_state or st.session_state.language != language:
    st.session_state.language = language
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": initial_message}
    ]

# ---------- チャット表示用関数 ----------
def get_image_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def render_message(message_text, is_user):
    icon_path = "images/user_icon.png" if is_user else "images/kagami_icon.png"
    alignment = "flex-end" if is_user else "flex-start"
    bg_color = "#e6f7e6" if is_user else "#ffffff"
    st.markdown(f"""
    <div style='display: flex; justify-content: {alignment}; margin-bottom: 1rem;'>
        <div style='display: flex; align-items: flex-start; max-width: 80%; background-color: {bg_color}; padding: 0.75rem 1rem; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.1);'>
            <img src='data:image/png;base64,{get_image_base64(icon_path)}' width='36' style='margin-right: 0.75rem; border-radius: 50%;' />
            <div style='font-size: 16px; color: #000;'>{message_text}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------- ヘッダー表示 ----------
st.markdown('<div style="text-align:center; font-size:42px; font-weight:bold; margin-bottom:5px;">Kagami</div>', unsafe_allow_html=True)
subtitle = "もう1人の優しい自分に出会う" if language=="日本語" else "Meet your kind inner self"
st.markdown(f'<div style="text-align:center; font-size:20px; color:#555; margin-bottom:10px;">{subtitle}</div>', unsafe_allow_html=True)

# ---------- チャット表示 ----------
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    render_message(msg["content"], is_user=(msg["role"]=="user"))

# ---------- 入力フォーム ----------
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area(input_label, height=150)
    submitted = st.form_submit_button(send_button)

if submitted and user_input:
    if not api_key:
        st.error(api_key_error)
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        try:
            client = openai.OpenAI(api_key=api_key)
            MAX_HISTORY = 5
            history_to_send = [st.session_state.messages[0]] + st.session_state.messages[-MAX_HISTORY:]
            
            response = client.chat.completions.create(
                model=model_choice,
                messages=history_to_send,
                temperature=temperature_value,
                max_tokens=max_tokens_value
            )
            reply = response.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()  # 最新のメッセージを表示するために再実行
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
            st.error(f"Error: {e}")

if st.sidebar.button("会話をリセット / Reset"):
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": initial_message}
    ]
    st.rerun()
