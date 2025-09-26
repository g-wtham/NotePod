import os
import json
from dotenv import load_dotenv
from google import genai

# --- Load API Key ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_quiz(transcript: str) -> dict:
    """Generates a multiple-choice quiz from a video transcript."""
    prompt = f"""
    Based on the following video transcript, generate a 5-question multiple-choice quiz
    to test a student's understanding of the key concepts.
    
    The output MUST be a valid JSON array.
    Each item must have this structure:
    {{
      "question": "The question text?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "The correct option text"
    }}

    Transcript:
    ---
    {transcript}
    ---
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        json_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(json_response)
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return [
            {"question": "What is the primary topic of the video?", "options": ["A", "B", "C", "D"], "answer": "A"},
            {"question": "This is a fallback question.", "options": ["Correct", "Incorrect", "Maybe", "None"], "answer": "Correct"}
        ]


def evaluate_submission(transcript: str, notes_bytes: bytes, notes_content_type: str, quiz_answers: list) -> dict:
    """Performs a holistic evaluation of a student's notes and quiz answers using the File API."""
    uploaded_file = None
    temp_file_name = None

    try:
        # Save uploaded file temporarily
        extension = notes_content_type.split('/')[-1]
        temp_file_name = f"student_notes.{extension}"
        with open(temp_file_name, "wb") as f:
            f.write(notes_bytes)

        print("Uploading file to Gemini...")
        uploaded_file = client.files.upload(file=temp_file_name)
        print(f"File uploaded successfully: {uploaded_file=}")

        prompt = f"""
        You are an expert Computer Science instructor evaluating a student's submission.
        Analyze based on:
        1. Transcript (truth source)
        2. Student's handwritten notes (uploaded file)
        3. Quiz answers

        **Scoring Rules:**
        - Notes quality
        - Quiz accuracy
        - Combined score = weighted mix of both
        - Passing threshold = 80%

        **Output MUST be a valid JSON object:**
        {{
          "combined_score": <0-100>,
          "is_approved": <true|false>,
          "feedback": "<detailed feedback>"
        }}

        Transcript:
        ---
        {transcript}
        ---
        Student's Quiz Answers (JSON):
        {json.dumps(quiz_answers, indent=2)}
        ---
        """

        print("Generating evaluation...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[uploaded_file, prompt]
        )

        print("Generating evaluation...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[uploaded_file, prompt]
        )

        print(f"Raw Gemini response: {response}")

        output = getattr(response, "text", None) or getattr(response, "output_text", None)
        if not output:
            raise ValueError("No output returned from Gemini.")

        print(f"Gemini raw text output: {output}")  # ✅ extra logging

        json_response = output.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(json_response)

    except Exception as e:
        print(f"Error evaluating submission: {e}")
        return {
            "combined_score": 0,
            "is_approved": False,
            "feedback": "An error occurred during evaluation. Please try submitting again."
        }
    finally:
        if uploaded_file:
            print(f"Deleting uploaded file: {uploaded_file.name}")
            client.files.delete(name=uploaded_file.name)
        if temp_file_name and os.path.exists(temp_file_name):
            os.remove(temp_file_name)


def summarize_pdf(pdf_path: str):
    """Example: Summarize a PDF file."""
    sample_pdf = client.files.upload(file=pdf_path)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=["Give me a summary of this pdf file.", sample_pdf],
    )
    return response.text


def analyze_image(image_path: str):
    """Example: Analyze an image file."""
    myfile = client.files.upload(file=image_path)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[myfile, "Can you tell me about the content of this image?"],
    )
    return response.text
