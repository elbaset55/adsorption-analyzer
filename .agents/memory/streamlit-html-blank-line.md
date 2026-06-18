---
name: Streamlit unsafe_allow_html blank line bug
description: Triple-quote f-strings with conditional expressions that evaluate to "" create blank lines that break Python-Markdown HTML block parsing
---

## The Rule
When using `st.markdown(..., unsafe_allow_html=True)`, NEVER use triple-quoted f-strings that can produce a blank line inside the HTML block.

**Why:** Streamlit uses Python-Markdown internally. Python-Markdown ends an HTML block at the first blank line it encounters. A conditional expression like `{"<span>...</span>" if cond else ""}` evaluates to an empty string when `cond=False`, producing a blank line in the rendered string. Everything after that blank line is treated as plain text and HTML tags are escaped/shown as raw text.

**How to apply:**
1. Pre-compute ALL conditional values into variables BEFORE the f-string.
2. Build HTML as adjacent single-quoted f-string literals (no triple quotes), so there are no blank lines.
3. Place optional elements inline on the same line as surrounding HTML, never on their own line.

```python
# WRONG — empty line when ib=False breaks markdown parser
st.markdown(f"""
<div class="card">
    <span>{name}</span>
    {"<span class='badge'>BEST</span>" if ib else ""}
</div>""", unsafe_allow_html=True)

# CORRECT — pre-compute, no blank lines possible
_bdg = f"<span class='badge'>BEST</span>" if ib else ""
st.markdown(
    f'<div class="card"><span>{name}</span>{_bdg}</div>',
    unsafe_allow_html=True)
```
