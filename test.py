import json
import streamlit as st

# This works ONLY IF the secret is stored as one giant string under the exact key "credentials.json"
credentials_dict = json.loads(st.secrets["credentials.json"])