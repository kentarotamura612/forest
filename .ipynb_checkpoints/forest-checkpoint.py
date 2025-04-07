import streamlit as st
import replicate
import os
import base64

# Set page configuration
st.set_page_config(page_title="心の森, Forest of Compassion")

# ---------- サイドバー設定 ----------
language = st.sidebar.selectbox("言語 / Language", ["日本語", "English"])

if language == "日本語":
    api_key_label = "Replicate APIキー"
    api_key_placeholder = "r8_..."
    api_key_error = "APIキーを入力してください。"
    temperature_help = "この値を高くすると、対話がより自由で多様な表現になります。"
    max_tokens_help = "生成される応答の長さを調整します。"
    model_label = "モデルを選んでください"
    model_options = ["Llama2-7B", "Llama2-13B"]
    model_format = lambda name: {
        "Llama2-7B": "Llama2-7B (軽量版)",
        "Llama2-13B": "Llama2-13B (標準版)"
    }[name]
    expander_title = "このアプリについて"
    expander_text = (
        "このアプリはセルフコンパッションに基づく対話を提供します。\n"
        "『心の森, Forest of Compassion』は、あなたの内面に寄り添い、優しさと癒しをお届けします。\n\n"
        "【APIキーの取得方法】\n"
        "1. [Replicate](https://replicate.com/) にアクセスし、APIキーを取得してください。"
    )
    system_prompt = (
        "あなたはセルフコンパッションの専門家です。まず、ユーザーにお名前を尋ね、その名前を使って対話を進めてください。"
        "以降の会話では、ユーザーの回答が一度に一つの項目に絞られるよう、各質問は必ず単一の回答のみを求める形式で1つずつ提示してください。"
        "ユーザーが体験を語る際は、具体的な内容に基づいて、安心できるように1つずつ丁寧な質問を行ってください。"
        "最後に温かい言葉で会話を締め、ユーザーに安心感を提供してください。"
    )
    initial_message = "こんにちは。お名前を教えてください。"
    input_label = "メッセージを入力してください"
    send_button = "送信"
else:
    api_key_label = "Replicate API Key"
    api_key_placeholder = "r8_..."
    api_key_error = "Please enter your API key."
    temperature_help = "A higher value makes responses more varied and creative."
    max_tokens_help = "Adjust the length of the generated response."
    model_label = "Select a model"
    model_options = ["Llama2-7B", "Llama2-13B"]
    model_format = lambda name: {
        "Llama2-7B": "Llama2-7B: Light version",
        "Llama2-13B": "Llama2-13B: Standard version"
    }[name]
    expander_title = "About this app"
    expander_text = (
        "This app offers a self-compassion based conversation experience.\n"
        "'Forest of Compassion' is designed to bring you warmth and healing by connecting with your inner self.\n\n"
        "**How to get an API Key:**\n"
        "1. Visit [Replicate](https://replicate.com/) to obtain your API key."
    )
    system_prompt = (
        "You are an expert in self-compassion. Begin by asking the user for their name and refer to them by that name throughout the conversation. "
        "Ensure that every question you ask requires only one single answer at a time. "
        "When the user shares experiences, ask one concrete question based on the details provided, one at a time. "
        "Conclude the conversation with warm, reassuring words that offer comfort and security."
    )
    initial_message = "Hello. Could you please tell me your name?"
    input_label = "Type your message here"
    send_button = "Send"

# APIキー取得：st.secrets に設定済みならそれを利用、なければサイドバー入力
if "REPLICATE_API_TOKEN" in st.secrets:
    api_key = st.secrets["REPLICATE_API_TOKEN"]
else:
    api_key = st.sidebar.text_input(api_key_label, type="password", placeholder=api_key_placeholder)

# Replicate APIキーを環境変数に設定
os.environ["REPLICATE_API_TOKEN"] = api_key

# パラメータ設定
temperature_value = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.01, help=temperature_help)
max_tokens_value = st.sidebar.slider("Max Tokens", min_value=100, max_value=2000, value=500, step=50, help=max_tokens_help)

# モデル選択
model_choice = st.sidebar.selectbox(model_label, model_options, index=0, format_func=model_format)

# アプリの説明
with st.sidebar.expander(expander_title):
    st.write(expander_text)

# ---------- チャット初期化 ----------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": initial_message}]

# ---------- チャット表示用関数 ----------
def get_image_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def render_message(message_text, role):
    is_user = role == "user"
    icon_path = "images/user_icon.png" if is_user else "images/kagami_icon.png"
    alignment = "flex-end" if is_user else "flex-start"
    bg_color = "#e6f7e6" if is_user else "#ffffff"
    st.markdown(
        f"""
        <div style='display: flex; justify-content: {alignment}; margin-bottom: 1rem;'>
            <div style='display: flex; align-items: flex-start; max-width: 80%; background-color: {bg_color}; padding: 0.75rem 1rem; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.1);'>
                <img src='data:image/png;base64,{get_image_base64(icon_path)}' width='36' style='margin-right: 0.75rem; border-radius: 50%;' />
                <div style='font-size: 16px; color: #000;'>{message_text}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- ヘッダー表示 ----------
st.markdown('<div style="text-align:center; font-size:42px; font-weight:bold; margin-bottom:5px;">心の森, Forest of Compassion</div>', unsafe_allow_html=True)
subtitle = "もう1人の優しい自分に出会う" if language == "日本語" else "Meet your kind inner self"
st.markdown(f'<div style="text-align:center; font-size:20px; color:#555; margin-bottom:10px;">{subtitle}</div>', unsafe_allow_html=True)

# チャット履歴の表示
for msg in st.session_state.messages:
    if msg["role"] != "system":
        render_message(msg["content"], msg["role"])

# Clear Chat History ボタン
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": initial_message}]
st.sidebar.button("Clear Chat History", on_click=clear_chat_history)

# ---------- Llama2 応答生成関数 ----------
def generate_llama2_response(prompt_input):
    dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'.\n\n"
    for m in st.session_state.messages:
        if m["role"] == "user":
            dialogue += f"User: {m['content']}\n\n"
        else:
            dialogue += f"Assistant: {m['content']}\n\n"
    full_prompt = f"{dialogue}User: {prompt_input}\n\nAssistant: "
    
    # モデル選択に応じたエンドポイント
    if model_choice == "Llama2-7B":
        llama2_model = "a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea"
    else:
        llama2_model = "a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5"
    
    response = replicate.run(
        llama2_model,
        input={
            "prompt": full_prompt,
            "temperature": temperature_value,
            "top_p": 0.9,  # 必要に応じて調整
            "max_length": max_tokens_value,
            "repetition_penalty": 1
        }
    )
    # generator の場合、リストに変換してから連結
    response_list = list(response)
    return "".join(response_list).strip()

# ---------- ユーザー入力と応答生成 ----------
prompt = st.chat_input(disabled=not api_key)
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    # ユーザー入力後、画面を更新
    st.rerun()

# 直前のメッセージがアシスタントでない場合、応答を生成
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = generate_llama2_response(prompt)
            placeholder = st.empty()
            full_response = ""
            # 応答が複数の部分に分かれている場合は連結
            for part in response_text:
                full_response += part
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()

