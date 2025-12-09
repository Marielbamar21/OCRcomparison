from sqlalchemy import text
from .connection import engine
import streamlit as st

def init_db():
    with engine.begin() as conn:
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """))
            
            conn.execute(text("""
                DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'response_type') THEN
                        CREATE TYPE response_type AS ENUM ('unstract', 'gemini', 'document_ai');
                    END IF;
                END
                $$ LANGUAGE plpgsql;
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tests (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    filename TEXT,
                    file_type TEXT,
                    unstract_response JSONB,
                    exec_time_unstract NUMERIC,
                    gemini_response JSONB,
                    exec_time_gemini NUMERIC,
                    document_ai_response JSONB,
                    exec_time_document_ai NUMERIC,
                    best_response response_type,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """))
            
        except Exception as e:
            st.error(f"DB Initialization Error: {e}")
            raise
