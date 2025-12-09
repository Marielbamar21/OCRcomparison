from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from config.settings import UNSTRACT_API_KEY, UNSTRACT_URL_WORKFLOW, GOOGLE_API_KEY

print("=" * 60)
print("🔍 VERIFICANDO VARIABLES DE ENTORNO")
print("=" * 60)

print(f"\n✅ UNSTRACT_API_KEY: {UNSTRACT_API_KEY[:20]}..." if UNSTRACT_API_KEY else "❌ UNSTRACT_API_KEY: None")
print(f"✅ UNSTRACT_URL_WORKFLOW: {UNSTRACT_URL_WORKFLOW}" if UNSTRACT_URL_WORKFLOW else "❌ UNSTRACT_URL_WORKFLOW: None")
print(f"✅ GOOGLE_API_KEY: {GOOGLE_API_KEY[:20]}..." if GOOGLE_API_KEY else "❌ GOOGLE_API_KEY: None")

print("\n" + "=" * 60)

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def verify_database_connection():
    """Verificar conexión a la base de datos"""
    try:
        engine = create_engine(DB_URL, future=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Conexión a la base de datos exitosa")
            return True
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return False

def verify_enum_values():
    """Verificar valores del enum response_type"""
    try:
        engine = create_engine(DB_URL, future=True)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT e.enumlabel 
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = 'response_type'
                ORDER BY e.enumsortorder;
            """))
            values = [row[0] for row in result]
            print(f"✅ Valores del enum response_type: {values}")
            
            expected = ['unstract', 'gemini', 'document_ai']
            if set(values) == set(expected):
                print("✅ Enum tiene los valores correctos")
            else:
                print(f"⚠️  Valores esperados: {expected}")
                print(f"⚠️  Valores actuales: {values}")
            return values
    except Exception as e:
        print(f"❌ Error verificando enum: {e}")
        return []

def verify_tables():
    """Verificar que las tablas existan"""
    try:
        engine = create_engine(DB_URL, future=True)
        with engine.connect() as conn:
            # Verificar tabla users
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                );
            """))
            if result.fetchone()[0]:
                print("✅ Tabla 'users' existe")
            else:
                print("❌ Tabla 'users' no existe")
            
            # Verificar tabla tests
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'tests'
                );
            """))
            if result.fetchone()[0]:
                print("✅ Tabla 'tests' existe")
            else:
                print("❌ Tabla 'tests' no existe")
            
            # Contar registros
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            print(f"📊 Total de usuarios: {user_count}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM tests"))
            test_count = result.fetchone()[0]
            print(f"📊 Total de tests: {test_count}")
            
            return True
    except Exception as e:
        print(f"❌ Error verificando tablas: {e}")
        return False

def verify_imports():
    """Verificar que todos los módulos se puedan importar"""
    print("\n🔍 Verificando imports...")
    
    try:
        from config.settings import DB_URL, GOOGLE_API_KEY
        print("✅ config.settings importado correctamente")
    except Exception as e:
        print(f"❌ Error importando config.settings: {e}")
    
    try:
        from database.connection import engine, get_engine
        print("✅ database.connection importado correctamente")
    except Exception as e:
        print(f"❌ Error importando database.connection: {e}")
    
    try:
        from database.models import init_db
        print("✅ database.models importado correctamente")
    except Exception as e:
        print(f"❌ Error importando database.models: {e}")
    
    try:
        from database.queries import (
            register_user, 
            get_user_tests, 
            get_all_tests, 
            get_statistics, 
            get_recent_tests, 
            save_test
        )
        print("✅ database.queries importado correctamente")
    except Exception as e:
        print(f"❌ Error importando database.queries: {e}")
    
    try:
        from services.gemini_service import process_with_gemini
        print("✅ services.gemini_service importado correctamente")
    except Exception as e:
        print(f"❌ Error importando services.gemini_service: {e}")
    
    try:
        from services.unstract_service import run_unstract_workflow
        print("✅ services.unstract_service importado correctamente")
    except Exception as e:
        print(f"❌ Error importando services.unstract_service: {e}")
    
    try:
        from services.document_ai_service import process_with_document_ai
        print("✅ services.document_ai_service importado correctamente")
    except Exception as e:
        print(f"❌ Error importando services.document_ai_service: {e}")
    
    try:
        from ui.styles import CUSTOM_CSS
        print("✅ ui.styles importado correctamente")
    except Exception as e:
        print(f"❌ Error importando ui.styles: {e}")

def test_queries():
    """Probar las funciones de queries"""
    print("\n🧪 Probando queries...")
    
    try:
        from database.queries import get_statistics
        stats = get_statistics()
        print(f"✅ get_statistics() funciona - Total tests: {stats[0]}")
    except Exception as e:
        print(f"❌ Error en get_statistics(): {e}")
    
    try:
        from database.queries import get_all_tests
        all_tests = get_all_tests()
        print(f"✅ get_all_tests() funciona - Registros obtenidos: {len(all_tests)}")
    except Exception as e:
        print(f"❌ Error en get_all_tests(): {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 VERIFICACIÓN DEL SETUP DEL PROYECTO")
    print("=" * 60)
    
    print("\n1️⃣ Verificando conexión a base de datos...")
    verify_database_connection()
    
    print("\n2️⃣ Verificando valores del enum...")
    verify_enum_values()
    
    print("\n3️⃣ Verificando tablas...")
    verify_tables()
    
    print("\n4️⃣ Verificando imports...")
    verify_imports()
    
    print("\n5️⃣ Probando queries...")
    test_queries()
    
    print("\n" + "=" * 60)
    print("✅ Verificación completada")
    print("=" * 60)