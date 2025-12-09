import requests
import base64
from config.settings import DOCAI_URL

def process_with_document_ai(
    file_bytes: bytes,
    mime_type: str,
    url=DOCAI_URL
):
    encoded_content = base64.b64encode(file_bytes).decode("utf-8")

    data = {
        "rawDocument": {
            "content": encoded_content,
            "mimeType": mime_type
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("Sending ...")

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()

    return response.json()


# from google.cloud import documentai_v1 as documentai
# from google.oauth2 import service_account
# from config.settings import (
#     DOCAI_PROJECT_ID,
#     DOCAI_LOCATION,
#     DOCAI_PROCESSOR_ID,
#     GOOGLE_APPLICATION_CREDENTIALS
# )

# def process_with_document_ai(file_bytes, filename, file_type):
#     try:
        
#         if not all([DOCAI_PROJECT_ID, DOCAI_PROCESSOR_ID, GOOGLE_APPLICATION_CREDENTIALS]):
#             return {
#                 "status": "error",
#                 "error": "Document AI no está configurado. Faltan variables de entorno."
#             }
#         print("11111111111111111111111111111111111111111111111111111111111111")
#         credentials = service_account.Credentials.from_service_account_file(
#             GOOGLE_APPLICATION_CREDENTIALS
#         )
#         print("2222222222222222222222222222222222222222222222222222222",)
#         client = documentai.DocumentProcessorServiceClient(credentials=credentials)

#         print("3333333333333333333333333333333333333333333333333333333", client)
#         if file_type.startswith("image"):
#             mime_type = file_type
#         elif file_type == "application/pdf":
#             mime_type = "application/pdf"
#         else:
#             mime_type = "application/octet-stream"

#         name = client.processor_path(DOCAI_PROJECT_ID, DOCAI_LOCATION, DOCAI_PROCESSOR_ID)

#         print("444444444444444444444444444444444444444444444444", name)

#         raw_document = documentai.RawDocument(content=file_bytes, mime_type=mime_type)

#         print("555555555555555555555555555555555555555555555555",raw_document)

#         request = documentai.ProcessRequest(name=name, raw_document=raw_document)

#         print("6666666666666666666666666666666666666666666666666666666",request)

#         result = client.process_document(request=request)

#         print("77777777777777777777777777777777777777777777777777777", result)
#         document = result.document
#         print("88888888888888888888888888888888888888888888888888888", document)

#         extracted_data = {
#             "documentType": "invoice",
#             "text": document.text,
#             "entities": [],
#             "pages": len(document.pages),
#             "confidence": 0.0
#         }
#         print("999999999999999999999999999999999999999999999999999999999",extracted_data)
#         if document.entities:
#             for entity in document.entities:
#                 extracted_data["entities"].append({
#                     "type": entity.type_,
#                     "mention_text": entity.mention_text,
#                     "confidence": entity.confidence
#                 })
            
#             if extracted_data["entities"]:
#                 total_confidence = sum(e["confidence"] for e in extracted_data["entities"])
#                 extracted_data["confidence"] = total_confidence / len(extracted_data["entities"])
#         print("11111111111111111111111111111111111111110000000000000000000000000")

#         return {
#             "status": "success",
#             "data": extracted_data,
#             "raw_response": {
#                 "text": document.text,
#                 "pages": len(document.pages)
#             }
#         }

#     except Exception as e:
#         print("EEEEEEEEEEEEEEEEEEERRRRRRRRRRRRRRRRRRROOOOOOOOOOOOORRRRRRRRRRRRRR", e)
#         return {
#             "status": "error",
#             "error": str(e)
#         }
