from sqlalchemy import text
from .connection import engine
import streamlit as st

def register_user(username):
    with engine.begin() as conn:
        try:
            result = conn.execute(
                text("""
                    INSERT INTO users (username)
                    VALUES (:u)
                    ON CONFLICT(username) DO NOTHING
                    RETURNING id
                """), {"u": username}
            ).fetchone()
            
            if result:
                return result[0]
            
            user_id = conn.execute(
                text("SELECT id FROM users WHERE username = :u"), {"u": username}
            ).fetchone()[0]
            
            return user_id
            
        except Exception as e:
            st.error(f"Error registering user: {e}")
            raise


from sqlalchemy import text
from .connection import engine
import streamlit as st

def register_user(username):
    with engine.begin() as conn:
        try:
            result = conn.execute(
                text("""
                    INSERT INTO users (username)
                    VALUES (:u)
                    ON CONFLICT(username) DO NOTHING
                    RETURNING id
                """), {"u": username}
            ).fetchone()
            
            if result:
                return result[0]
            
            user_id = conn.execute(
                text("SELECT id FROM users WHERE username = :u"), {"u": username}
            ).fetchone()[0]
            
            return user_id
            
        except Exception as e:
            st.error(f"Error registering user: {e}")
            raise


def get_user_tests(user_id):
    with engine.connect() as conn:
        user_tests = conn.execute(
            text("""
                SELECT 
                    id,
                    filename,
                    file_type,
                    best_response,
                    exec_time_gemini,
                    exec_time_unstract,
                    exec_time_document_ai,
                    created_at
                FROM tests 
                WHERE user_id = :uid 
                ORDER BY created_at DESC
            """),
            {"uid": user_id}
        ).fetchall()
        return user_tests


def get_all_tests():
    with engine.connect() as conn:
        all_tests = conn.execute(text("""
            SELECT 
                t.id,
                u.username,
                t.filename,
                t.file_type,
                t.best_response,
                t.exec_time_gemini,
                t.exec_time_unstract,
                t.exec_time_document_ai,
                t.created_at
            FROM tests t
            JOIN users u ON t.user_id = u.id
            ORDER BY t.created_at DESC
            LIMIT 100
        """)).fetchall()
        return all_tests


def get_statistics():
    with engine.connect() as conn:
        stats = conn.execute(text("""
            SELECT 
                COUNT(*) as total_tests,
                COUNT(CASE WHEN best_response = 'gemini' THEN 1 END) as gemini_wins,
                COUNT(CASE WHEN best_response = 'unstract' THEN 1 END) as unstract_wins,
                COUNT(CASE WHEN best_response = 'document_ai' THEN 1 END) as docai_wins,
                AVG(exec_time_gemini) as avg_gemini_time,
                AVG(exec_time_unstract) as avg_unstract_time,
                AVG(exec_time_document_ai) as avg_docai_time,
                MIN(exec_time_gemini) as min_gemini_time,
                MIN(exec_time_unstract) as min_unstract_time,
                MIN(exec_time_document_ai) as min_docai_time,
                MAX(exec_time_gemini) as max_gemini_time,
                MAX(exec_time_unstract) as max_unstract_time,
                MAX(exec_time_document_ai) as max_docai_time
            FROM tests
        """)).fetchone()
        return stats


def get_recent_tests(limit=10):
    with engine.connect() as conn:
        recent = conn.execute(text("""
            SELECT 
                filename,
                best_response,
                exec_time_gemini,
                exec_time_unstract,
                exec_time_document_ai,
                created_at
            FROM tests
            ORDER BY created_at DESC
            LIMIT :limit
        """), {"limit": limit}).fetchall()
        return recent


def save_test(user_id, filename, file_type, results, exec_times, best):
    import json
    
    print("=" * 60)
    print("DEBUG SAVE_TEST:")
    print(f"user_id: {user_id}")
    print(f"filename: {filename}")
    print(f"file_type: {file_type}")
    print(f"results keys: {list(results.keys())}")
    print(f"exec_times keys: {list(exec_times.keys())}")
    print(f"best: {best}")
    print("=" * 60)
    
    try:
        with engine.begin() as conn:
            data = {
                "uid": user_id,
                "filename": filename,
                "file_type": file_type,
                "gemini": json.dumps(results.get("gemini")) if "gemini" in results else None,
                "exec_gemini": exec_times.get("gemini"),
                "docai": json.dumps(results.get("document_ai")) if "document_ai" in results else None,
                "exec_docai": exec_times.get("document_ai"),
                "unstract": json.dumps(results.get("unstract")) if "unstract" in results else None,
                "exec_unstract": exec_times.get("unstract"),
                "best": best
            }

            result = conn.execute(
                text("""
                    INSERT INTO tests (
                        user_id,
                        filename,
                        file_type,
                        gemini_response,
                        exec_time_gemini,
                        document_ai_response,
                        exec_time_document_ai,
                        unstract_response,
                        exec_time_unstract,
                        best_response
                    )
                    VALUES (
                        :uid,
                        :filename,
                        :file_type,
                        :gemini,
                        :exec_gemini,
                        :docai,
                        :exec_docai,
                        :unstract,
                        :exec_unstract,
                        :best
                    )
                    RETURNING id
                """),
                data
            )
            
            inserted_id = result.fetchone()[0]
            print(f"Saved ID: {inserted_id}")
            return {"success": True, "id": inserted_id}
            
    except Exception as e:
        print(f"ERROR")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise