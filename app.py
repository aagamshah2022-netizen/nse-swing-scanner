import streamlit as st

st.set_page_config(
page_title="NSE Swing Scanner",
page_icon="📈"
)

st.title("📈 NSE Swing Scanner")

st.write("App code loaded successfully.")

def is_red(row):
return row["Close"] < row["Open"]

def test_function():
data = None

```
if data is None:
    return "OK"

return "ERROR"
```

result = test_function()

st.success(result)
