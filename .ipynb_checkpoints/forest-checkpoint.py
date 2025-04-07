import streamlit as st
import replicate
import os
import base64

# Set page configuration
st.set_page_config(page_title="心の森")

# ---------- サイドバー設定 ----------
language = st.sidebar.selectbox("言語 / Language", ["日本語", "English"])

if language == "日本語":
    api_key_label = "Replicate APIキー"
    api_key_placeholder = "r8_..."
    api_key_error = "APIキーを入力してください。"
    temperature_help = "この値を高くすると、対話がより自由で多様な表現になります。"
    max_tokens_help = "生成される応答の長さを調整します。"
    model_label = "モデルを選んでください"
    # モデルオプションに Llama2-70B を追加
    model_options = ["Llama2-7B", "Llama2-13B", "Llama2-70B"]
    model_format = lambda name: {
        "Llama2-7B": "Llama2-7B (軽量版)",
        "Llama2-13B": "Llama2-13B (標準版)",
        "Llama2-70B": "Llama2-70B (高精度版)"
    }[name]
    expander_title = "このアプリについて"
    expander_text = (
        "このアプリはあなたの心の悩みや疑問に寄り添い、温かく的確なアドバイスを提供するチャットアプリです。\n\n"
        "【APIキーの取得方法】\n"
        "1. [Replicate](https://replicate.com/) にアクセスし、APIキーを取得してください。"
    )
    # システムプロンプトは余計な謝罪や確認をせず、直接回答するよう指示
    system_prompt = (
        "あなたは非常に有能な日本語応答モデルです。必ず日本語で回答してください。\n"
        "質問が曖昧な場合でも、不要な謝罪や文脈確認はせず、できる限り直接的に回答してください。"
    )
    # 初期メッセージは純粋な日本語のみ
    initial_message = (
        "ようこそ。こちらは心の悩みや疑問に寄り添うカウンセリングアプリです。\n"
        "まずは、どのような内容でお悩みか、または知りたいことを教えてください。"
    )
    input_label = "メッセージを入力してください"
    send_button = "送信"
else:
    api_key_label = "Replicate API Key"
    api_key_placeholder = "r8_..."
    api_key_error = "Please enter your API key."
    temperature_help = "A higher value makes responses more varied and creative."
    max_tokens_help = "Adjust the length of the generated response."
    model_label = "Select a model"
    model_options = ["Llama2-7B", "Llama2-13B", "Llama2-70B"]
    model_format = lambda name: {
        "Llama2-7B": "Llama2-7B: Light version",
        "Llama2-13B": "Llama2-13B: Standard version",
        "Llama2-70B": "Llama2-70B: High-accuracy version"
    }[name]
    expander_title = "About this app"
    expander_text = (
        "'Forest of Compassion' offers gentle and wise counsel to help you with any questions or concerns.\n\n"
        "**How to get an API Key:**\n"
        "1. Visit [Replicate](https://replicate.com/) to obtain your API key."
    )
    system_prompt = (
        "You are a highly capable English response model. Always respond in English.\n"
        "Even if the user's question is ambiguous, do not include unnecessary apologies or context confirmation messages; "
        "please answer directly and concretely."
    )
    initial_message = (
        "Welcome. This is a counseling app that offers gentle and thoughtful advice for your concerns.\n"
        "Please let me know what topic you're interested in or what you'd like to discuss."
    )
    input_label = "Type your message here"
    send_button = "Send"

# APIキー取得：st.secrets に設定済みならそれを利用、なければサイドバーから入力
if "REPLICATE_API_TOKEN" in st.secrets:
    api_key = st.secrets["REPLICATE_API_TOKEN"]
else:
    api_key = st.sidebar.text_input(api_key_label, type="password", placeholder=api_key_placeholder)

os.environ["REPLICATE_API_TOKEN"] = api_key

# パラメータ設定
temperature_value = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.01, help=temperature_help)
max_tokens_value = st.sidebar.slider("Max Tokens", min_value=100, max_value=2000, value=500, step=50, help=max_tokens_help)

# モデル選択とエンドポイントの辞書
model_endpoints = {
    "Llama2-7B": "a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea",
    "Llama2-13B": "a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5",
    # 70B のエンドポイント：必要に応じて owner を追加してください
    "Llama2-70B": "llama-2-70b-chat:2c1608e18606fad2812020dc541930f2d0495ce32eee50074220b87300bc16e1"
}
model_choice = st.sidebar.selectbox(model_label, model_options, index=0, format_func=model_format)

# アプリの説明
with st.sidebar.expander(expander_title):
    st.write(expander_text)

# ---------- チャット初期化 ----------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": initial_message}]

def get_image_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def render_message(message_text, role):
    is_user = (role == "user")
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
if language == "日本語":
    st.markdown('<div style="text-align:center; font-size:42px; font-weight:bold; margin-bottom:5px;">心の森</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center; font-size:20px; color:#555; margin-bottom:10px;">あなたの心に寄り添います</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align:center; font-size:42px; font-weight:bold; margin-bottom:5px;">Forest of Compassion</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center; font-size:20px; color:#555; margin-bottom:10px;">Providing gentle and wise counsel for your soul</div>', unsafe_allow_html=True)

# チャット履歴の表示
for msg in st.session_state.messages:
    if msg["role"] != "system":
        render_message(msg["content"], msg["role"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": initial_message}]
st.sidebar.button("Clear Chat History", on_click=clear_chat_history)

def generate_llama2_response(prompt_input):
    # 会話履歴とシステムプロンプトを連結
    dialogue = system_prompt + "\n\n"
    for m in st.session_state.messages:
        if m["role"] == "user":
            dialogue += "User: " + m["content"] + "\n\n"
        else:
            dialogue += "Assistant: " + m["content"] + "\n\n"
    full_prompt = f"{dialogue}User: {prompt_input}\n\nAssistant: "
    
    # 選択したモデルのエンドポイントを使用
    llama2_model = model_endpoints.get(model_choice)
    
    try:
        response = replicate.run(
            llama2_model,
            input={
                "prompt": full_prompt,
                "temperature": temperature_value,
                "top_p": 0.9,
                "max_length": max_tokens_value,
                "repetition_penalty": 1
            }
        )
    except ValueError as ve:
        if model_choice == "Llama2-70B":
            st.error("70Bモデルの呼び出しに失敗しました。エンドポイントの指定が正しいか確認してください。")
            return "70Bモデルの呼び出しに失敗しました。"
        else:
            raise ve

    response_list = list(response)
    return "".join(response_list).strip()

# ---------- ユーザー入力と応答生成 ----------
prompt = st.chat_input(disabled=not api_key)
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    st.rerun()

if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = generate_llama2_response(prompt)
            placeholder = st.empty()
            placeholder.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()
