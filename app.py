import os

import streamlit as st
from google import genai
from google.genai import types


MODEL_NAME = "gemini-3.8-flash"
MAX_IMAGE_BYTES = 5 * 1024 * 1024
IMAGE_TYPES = ["png", "jpg", "jpeg", "webp"]

SUBJECTS = [
    "Mathematics / గణితం",
    "Physics / భౌతిక శాస్త్రం",
    "Chemistry / రసాయన శాస్త్రం",
    "Biology / జీవశాస్త్రం",
    "Other STEM / ఇతర STEM",
]
GRADE_LEVELS = [
    "Classes 6–8 / 6–8 తరగతులు",
    "Classes 9–10 / 9–10 తరగతులు",
    "Classes 11–12 / 11–12 తరగతులు",
]


def build_tutor_prompt(question: str, subject: str, grade: str) -> str:
    return f"""You are a patient STEM tutor for school students.

Student level: {grade}
Subject: {subject}
Student's question: {question or "Please read the handwritten problem in the attached image and solve it."}

Teach the problem accurately and in an age-appropriate way. Write the explanation in BOTH English and Telugu. For every explanatory section and every numbered step, include both languages (English first, Telugu second). Keep equations, units, and symbols clear.

Use this structure:
## Problem / సమస్య
Restate the problem you understood in English and Telugu. If it came from an image, transcribe the handwritten equation or question. If any part is unclear, say exactly what is uncertain instead of guessing.
## Key idea / ముఖ్య భావన
Explain the concept or formula in both languages.
## Step-by-step solution / దశలవారీ పరిష్కారం
Number the steps. For each step, show the operation and explain why it is needed in both languages.
## Check / తనిఖీ
Check the result, units, or reasoning in both languages.
## Final answer / తుది సమాధానం
State the answer clearly in both languages.

Do not skip algebra or arithmetic steps. If the problem is incomplete or unreadable, explain what information is missing and ask one concise clarification in both languages. Do not invent values that are not in the question."""


def solve_problem(question: str, subject: str, grade: str, image) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Add it in Replit Secrets and restart the app."
        )

    client = genai.Client(api_key=api_key)
    prompt = build_tutor_prompt(question.strip(), subject, grade)
    content = [prompt]

    if image is not None:
        content.append(
            types.Part.from_bytes(
                data=image.getvalue(),
                mime_type=image.type or "image/png",
            )
        )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=content,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=8192,
        ),
    )
    answer = response.text
    if not answer:
        raise RuntimeError("Gemini returned an empty answer. Please try again.")
    return answer


st.set_page_config(
    page_title="STEM Tutor | STEM శిక్షకుడు",
    page_icon="∑",
    layout="centered",
)

st.title("STEM Tutor")
st.caption(
    "Understand the steps, not just the answer. / "
    "సమాధానమే కాదు, పరిష్కార దశలను కూడా అర్థం చేసుకోండి."
)
st.write(
    "Ask a maths or science question, or upload a photo of your handwritten work. "
    "మీ గణితం లేదా సైన్స్ ప్రశ్నను అడగండి, లేదా చేతితో రాసిన సమస్య ఫోటోను అప్‌లోడ్ చేయండి."
)
st.caption(f"Powered by {MODEL_NAME}")

with st.form("tutor_form"):
    question = st.text_area(
        "Your question / మీ ప్రశ్న",
        placeholder="For example: Solve 2x + 5 = 17 / ఉదాహరణ: 2x + 5 = 17 ను పరిష్కరించండి",
        height=120,
    )
    subject = st.selectbox("Subject / విషయం", SUBJECTS)
    grade = st.selectbox("Class level / తరగతి స్థాయి", GRADE_LEVELS)
    uploaded_image = st.file_uploader(
        "Handwritten problem image (optional) / చేతిరాత సమస్య చిత్రం (ఐచ్ఛికం)",
        type=IMAGE_TYPES,
        help="PNG, JPG, or WEBP. Maximum 5 MB. / PNG, JPG లేదా WEBP. గరిష్ఠ పరిమాణం 5 MB.",
    )
    submitted = st.form_submit_button(
        "Explain this problem / ఈ సమస్యను వివరించండి",
        type="primary",
        use_container_width=True,
    )

image_too_large = (
    uploaded_image is not None and uploaded_image.size > MAX_IMAGE_BYTES
)
if uploaded_image is not None:
    if image_too_large:
        st.error("That image is larger than 5 MB. Please upload a smaller image.")
    else:
        st.image(
            uploaded_image,
            caption="Uploaded problem / అప్‌లోడ్ చేసిన సమస్య",
            use_container_width=True,
        )

if submitted:
    st.session_state.pop("tutor_answer", None)

    if image_too_large:
        st.warning(
            "Please upload an image that is 5 MB or smaller. / "
            "దయచేసి 5 MB లేదా అంతకంటే చిన్న చిత్రాన్ని అప్‌లోడ్ చేయండి."
        )
    elif not question.strip() and uploaded_image is None:
        st.warning(
            "Enter a question or upload an image first. / "
            "ముందుగా ప్రశ్నను నమోదు చేయండి లేదా చిత్రాన్ని అప్‌లోడ్ చేయండి."
        )
    else:
        try:
            with st.spinner("Working through the steps… / దశలను వివరిస్తున్నాను…"):
                st.session_state["tutor_answer"] = solve_problem(
                    question,
                    subject,
                    grade,
                    uploaded_image,
                )
        except RuntimeError as error:
            st.error(str(error))
        except Exception as error:
            st.error(
                "The tutor could not get an answer from Gemini "
                f"({type(error).__name__}). Check that the API key is valid and "
                f"that {MODEL_NAME} is enabled for your Google API account, then try again."
            )

if st.session_state.get("tutor_answer"):
    st.divider()
    st.subheader("Worked solution / పరిష్కారం")
    st.markdown(st.session_state["tutor_answer"])
