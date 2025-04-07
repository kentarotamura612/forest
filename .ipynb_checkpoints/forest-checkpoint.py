import streamlit as st
import replicate
import os
import base64

# Set page configuration
st.set_page_config(page_title="Forest of Compassion")

# ---------- Sidebar Settings ----------
api_key_label = "Replicate API Key"
api_key_placeholder = "r8_..."
api_key_error = "Please enter your API key."
temperature_help = "A higher temperature makes responses more creative."
max_tokens_help = "Adjust the length of the generated response."
model_label = "Select a model"
model_options = ["Llama2-7B", "Llama2-13B"]
model_format = lambda name: {
    "Llama2-7B": "Llama2-7B: Light version",
    "Llama2-13B": "Llama2-13B: Standard version"
}[name]
expander_title = "About this app"
expander_text = (
    "'Forest of Compassion' offers gentle and wise counsel to help you with any questions or concerns.\n\n"
    "**How to get an API Key:**\n"
    "1. Visit [Replicate](https://replicate.com/) to obtain your API key."
)
system_prompt = (
    "You are a highly capable English response model. Always respond in English. "
    "If the user's question is ambiguous, do not include unnecessary apologies or requests for context; "
    "please answer directly and concretely."
)
initial_message = (
    "Welcome to Forest of Compassion. Here, we provide gentle and thoughtful advice for your concerns.\n"
    "Please let me know what topic you're interested in or what you'd like to discuss."
)
input_label = "Type your message here"
send_button = "Send"

# Get API key from st.secrets if available, otherwise from the sidebar input
if "REPLICATE_API_TOKEN" in st.secrets:
    api_key = st.secrets["REPLICATE_API_TOKEN"]
else:
    api_key = st.sidebar.text_input(api_key_label, type="password", placeholder=api_key_placeholder)

os.environ["REPLICATE_API_TOKEN"] = api_key

# Parameter Settings
temperature_value = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.01, help=temperature_help)
max_tokens_value = st.sidebar.slider("Max Tokens", min_value=100, max_value=2000, value=500, step=50, help=max_tokens_help)

# Model selection and endpoints dictionary
model_endpoints = {
    "Llama2-7B": "a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea",
    "Llama2-13B": "a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5"
}
model_choice = st.sidebar.selectbox(model_label, model_options, index=0, format_func=model_format)

# App Description
with st.sidebar.expander(expander_title):
    st.write(expander_text)

# ---------- Chat Initialization ----------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": initial_message}]

def get_image_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def render_message(message_text, role):
    is_user = (role == "user")
    icon_path = "images/user_icon.png" if is_user else "images/assistant_icon.png"
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

# ---------- Header Display ----------
st.markdown('<div style="text-align:center; font-size:42px; font-weight:bold; margin-bottom:5px;">Forest of Compassion</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center; font-size:20px; color:#555; margin-bottom:10px;">Providing gentle and wise counsel for your soul</div>', unsafe_allow_html=True)

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] != "system":
        render_message(msg["content"], msg["role"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": initial_message}]
st.sidebar.button("Clear Chat History", on_click=clear_chat_history)

def generate_llama2_response(prompt_input):
    # Concatenate system prompt and conversation history
    dialogue = system_prompt + "\n\n"
    for m in st.session_state.messages:
        if m["role"] == "user":
            dialogue += "User: " + m["content"] + "\n\n"
        else:
            dialogue += "Assistant: " + m["content"] + "\n\n"
    full_prompt = f"{dialogue}User: {prompt_input}\n\nAssistant: "
    
    llama2_model = model_endpoints.get(model_choice)
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
    response_list = list(response)
    return "".join(response_list).strip()

# ---------- User Input and Response Generation ----------
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
