def get_custom_css() -> str:
    """Return custom CSS for the chatbot UI."""
    return """
<style>
    /* Main container for each conversation item */
    div[data-testid="stHorizontalBlock"] {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 6px 10px;
        margin-bottom: 3px;
        height: 40px;
        display: flex;
        align-items: center;
        width: 95%;
        box-sizing: border-box;
        background-color: #fafafa;
    }

    div[data-testid="stHorizontalBlock"] .stButton {
        height: 100%;
        width: 100%;
    }

    div[data-testid="stHorizontalBlock"] .stButton button {
        background-color: transparent;
        border: none;
        padding: 0;
        margin: 0;
        height: 100%;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    div[data-testid="stHorizontalBlock"] > div:first-child .stButton button {
        justify-content: flex-start;
        font-weight: 500;
        color: #262730 !important;
        font-size: 0.9em;
    }
    div[data-testid="stHorizontalBlock"] > div:first-child .stButton button:hover {
        color: #FF4B4B !important;
        background-color: #f0f0f0;
    }

    div[data-testid="stHorizontalBlock"] > div:not(:first-child) .stButton button {
        font-size: 1.1em;
        color: #666 !important;
    }
    div[data-testid="stHorizontalBlock"] > div:not(:first-child) .stButton button:hover {
        color: #262730 !important;
        background-color: #f0f0f0;
    }

    /* Custom style for the source buttons */
    .source-btn button {
        background-color: transparent;
        border: 1px solid #ccc;
        border-radius: 15px;
        padding: 5px 10px;
        color: #333;
        font-weight: 400;
        font-size: 0.9em;
        transition: all 0.2s;
    }
    .source-btn button:hover {
        background-color: #f0f2f6;
        border-color: #aaa;
        color: #000;
    }
</style>
"""


def get_new_conversation_button_style() -> str:
    """Return CSS for the new conversation button."""
    return """
<style>
.new-conversation-btn {
    background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0 16px 0;
    width: 100%;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    text-align: center;
}
.new-conversation-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}
</style>
"""

