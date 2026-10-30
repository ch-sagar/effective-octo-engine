import streamlit as st

from backend import ask

st.set_page_config(page_title="Nimbus Support", page_icon="☁️")
st.title("☁️ Nimbus Cloud Support")
st.caption("Ask about billing, limits, security and onboarding.")

if "history" not in st.session_state:
    st.session_state.history = []

for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("e.g. What does 700k requests cost on Pro?"):
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"), st.spinner("Thinking…"):
        try:
            answer = ask(st.session_state.history)
        except Exception as e:  # show errors instead of a blank page while learning
            answer = f"⚠️ Error calling endpoint: {e}"
        st.markdown(answer)
    st.session_state.history.append({"role": "assistant", "content": answer})
