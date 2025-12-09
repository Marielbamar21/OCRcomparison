from google import genai
from google.genai import types
from config.settings import GOOGLE_API_KEY

def process_with_gemini(file_bytes, filename, file_type):
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)

        if file_type.startswith("image"):
            mime_type = file_type
        else:
            mime_type = "application/pdf"

        part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)

        prompt = """
        Analyze the following document containing invoice data.  

        Your goal is to extract as much information as possible and return it in a structured JSON object.

        Always return a JSON with this structure:

        {
          "documentType": "invoice",
          "invoiceNumber": "",
          "invoiceSeries": "",
          "issueDate": "",
          "dueDate": "",
          "seller": {
            "name": "",
            "taxId": "",
            "address": "",
            "phone": "",
            "email": ""
          },
          "buyer": {
            "name": "",
            "taxId": "",
            "address": "",
            "phone": "",
            "email": ""
          },
          "items": [
            {
              "description": "",
              "quantity": "",
              "unitPrice": "",
              "subtotal": ""
            }
          ],
          "subtotal": "",
          "tax": "",
          "discount": "",
          "total": "",
          "currency": "",
          "paymentMethod": "",
          "paymentStatus": "",
          "notes": ""
        }

        Important rules:
        - If a field does not exist in the document, leave it as an empty string "".
        - Detect data even if the names change.
        - Extract numbers even if they have different formats.
        - Returns only valid JSON, without comments or explanations.
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[part, prompt]
        )

        return {
            "status": "success",
            "data": response.text,
            "model": "gemini-2.5-flash"
        }

    except Exception as e:
        if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
            return {
                "status": "error",
                "error": "Gemini API quota exceeded. Please wait or upgrade your plan.",
                "error_type": "quota_exceeded"
            }
        return {
            "status": "error",
            "error": str(e)
        }

