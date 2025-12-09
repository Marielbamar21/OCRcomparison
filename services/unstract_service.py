import requests
import urllib.parse
import time
from config.settings import UNSTRACT_API_KEY, UNSTRACT_URL_WORKFLOW

def run_unstract_workflow(
    file_bytes,
    filename,          
    file_type,         
    api_key=UNSTRACT_API_KEY,
    workflow_url=UNSTRACT_URL_WORKFLOW,
    poll_interval=5,   
    timeout=300        
):
    import mimetypes
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    headers = {"Authorization": f"Bearer {"a877dca1-b121-4209-82c1-62db54369652"}"}
    files = {"files": (filename, file_bytes, mime_type)} 

    try:
        response = requests.post(workflow_url, headers=headers, files=files, verify=False)
        response.raise_for_status()
        resp_json = response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error al enviar archivo a Unstract: {str(e)}"}
    
    status_api_url = resp_json['message']['status_api']
    parsed_url = urllib.parse.urlparse(status_api_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    execution_id = query_params.get("execution_id", [None])[0]
    
    if not execution_id:
        return {"error": "No se recibió execution_id de Unstract", "response": resp_json}

    status_url = f"{workflow_url.rstrip('/')}/?execution_id={execution_id}"
    start_time = time.time()
    
    while True:
        if time.time() - start_time > timeout:
            return {"error": "Timeout alcanzado esperando a que la ejecución se complete"}
        
        try:
            status_resp = requests.get(status_url, headers=headers, verify=False)
            try:
                status_resp.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if status_resp.status_code != 422:
                    return {"error": f"HTTP error consultando status: {e}"}
            
            status_json = status_resp.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Error consultando status: {str(e)}"}

        status = status_json.get("status", "").upper()
        
        if status in ("COMPLETED", "ERROR", "STOPPED"):
            return status_json
        elif status in ("PENDING", "EXECUTING"):
            time.sleep(poll_interval)
        else:
            return {"error": f"Status desconocido: {status}"}

