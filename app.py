import streamlit as st
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from config.settings import DOCAI_URL 

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

# Importar desde módulos locales
from database.models import init_db
from database.queries import register_user, get_user_tests, get_all_tests, get_statistics, get_recent_tests, save_test
from services.gemini_service import process_with_gemini
from services.unstract_service import run_unstract_workflow
from services.document_ai_service import process_with_document_ai
from ui.styles import CUSTOM_CSS
from config.settings import UNSTRACT_API_KEY, UNSTRACT_URL_WORKFLOW

# ==========================
# Streamlit config
# ==========================
st.set_page_config(
    page_title="OCR Invoice Comparator", 
    page_icon="📄", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==========================
# DB Init
# ==========================
init_db()

# ==========================
# Login UI
# ==========================
if 'username' not in st.session_state:
    st.session_state.username = None
    st.session_state.user_id = None

if st.session_state.username is None:
    st.title("🔐 Enter Your Username")
    st.markdown("Please enter your username to use the OCR comparator")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username_input = st.text_input("Username", placeholder="e.g., marielba.maldonado")
        if st.button("Log In", key="login_button", use_container_width=True):
            if username_input.strip():
                user_id = register_user(username_input.strip())
                st.session_state.username = username_input.strip()
                st.session_state.user_id = user_id
                st.rerun()
            else:
                st.error("Please enter a valid username")
    st.stop()

# ==========================
# Header
# ==========================
col1, col2 = st.columns([3,1])
with col1:
    st.title("🔍 OCR Invoice Platform Comparison")
    st.markdown("**Comparing: Unstract vs Google Gemini AI vs Google Document AI**")
with col2:
    st.markdown(f"**User:** `{st.session_state.username}`")
    if st.button("🚪 Log Out", key="logout_button"):
        st.session_state.username = None
        st.session_state.user_id = None
        st.rerun()

# ==========================
# Tabs
# ==========================
tab1, tab2, tab3 = st.tabs([
    "📤 Process Invoice",
    "📜 My History",
    "📊 Statistics"
])

# --------------------------
# Tab 1: Upload & OCR
# --------------------------
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

with tab1:
    st.header("Upload and Process Invoice")
    
    # Initialize session state variables
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'exec_times' not in st.session_state:
        st.session_state.exec_times = None
    if 'current_filename' not in st.session_state:
        st.session_state.current_filename = None
    if 'current_file_type' not in st.session_state:
        st.session_state.current_file_type = None
    if 'file_bytes_stored' not in st.session_state:
        st.session_state.file_bytes_stored = None

    # Initialize platform checkboxes
    if 'run_gemini' not in st.session_state:
        st.session_state.run_gemini = True
    if 'run_unstract' not in st.session_state:
        st.session_state.run_unstract = True
    if 'run_documentai' not in st.session_state:
        st.session_state.run_documentai = True
    
    uploaded_file = st.file_uploader(
        "Select an invoice (image or PDF)", 
        type=['png','jpg','jpeg','pdf'], 
        key="upload_file",
        disabled=st.session_state.processing
    )
    
    if uploaded_file:
        filename = uploaded_file.name
        file_bytes = uploaded_file.read()
        file_type = uploaded_file.type
        
        col1, col2 = st.columns([1,2])
        
        with col1:
            st.subheader("Preview")
            if file_type.startswith('image'):
                st.image(file_bytes, use_container_width=True)
            else:
                st.info(f"📄 PDF uploaded: **{filename}**")
        
        with col2:
            st.subheader("Select platforms to evaluate")
            
            st.session_state.run_gemini = st.checkbox(
                "🤖 Google Gemini AI", 
                value=st.session_state.run_gemini, 
                key="check_gemini",
                disabled=st.session_state.processing
            )
            st.session_state.run_unstract = st.checkbox(
                "🔧 Unstract", 
                value=st.session_state.run_unstract, 
                key="check_unstract",
                disabled=st.session_state.processing
            )
            # st.session_state.run_documentai = st.checkbox(
            #     "📄 Google Document AI", 
            #     value=st.session_state.run_documentai,
            #     key="check_documentai",
            #     disabled=st.session_state.processing
            # )
            
            if st.button(
                "🚀 Process with selected platforms", 
                key="process_button",
                disabled=st.session_state.processing or (
                    not st.session_state.run_gemini and 
                    not st.session_state.run_unstract and 
                    not st.session_state.run_documentai
                ),
                use_container_width=True
            ):
                st.session_state.processing = True
                st.session_state.file_bytes_stored = file_bytes
                st.session_state.current_filename = filename
                st.session_state.current_file_type = file_type
                st.rerun()
    
    # Processing logic
    if st.session_state.processing and st.session_state.file_bytes_stored:
        results = {}
        exec_times = {}
        
        file_bytes = st.session_state.file_bytes_stored
        filename = st.session_state.current_filename
        file_type = st.session_state.current_file_type

        # Progress container
        progress_container = st.container()
        with progress_container:
            st.markdown("### 🔄 Processing...")
            progress_bar = st.progress(0)
            status_text = st.empty()

            total_platforms = sum([
                st.session_state.run_gemini,
                st.session_state.run_unstract,
                st.session_state.run_documentai
            ])
            current = 0

            futures = {}
            start_times = {}

            with ThreadPoolExecutor(max_workers=3) as executor:

                if st.session_state.run_gemini:
                    status_text.markdown("**⏳ Submitting Gemini AI...**")
                    start_times["gemini"] = time.time()
                    futures[executor.submit(process_with_gemini, file_bytes, filename, file_type)] = "gemini"

                if st.session_state.run_unstract:
                    status_text.markdown("**⏳ Submitting Unstract...**")
                    start_times["unstract"] = time.time()
                    futures[executor.submit(run_unstract_workflow, file_bytes=file_bytes, filename=filename, file_type=file_type)] = "unstract"

                # if st.session_state.run_documentai:
                #     status_text.markdown("**⏳ Submitting Google Document AI...**")
                #     start_times["document_ai"] = time.time()
                #     futures[executor.submit(process_with_document_ai, file_bytes, file_type,DOCAI_URL)] = "document_ai"

                # Collect async results
                for future in as_completed(futures):
                    platform = futures[future]
                    try:
                        results[platform] = future.result()
                        exec_times[platform] = time.time() - start_times[platform]
                    except Exception as e:
                        results[platform] = {"status": "error", "error": str(e)}
                        exec_times[platform] = None

                    current += 1
                    progress_bar.progress(current / total_platforms)

            status_text.markdown("**✅ Processing complete!**")
            time.sleep(0.5)

        st.session_state.results = results
        st.session_state.exec_times = exec_times
        st.session_state.processing = False
        st.rerun()

    if st.session_state.results and st.session_state.exec_times:
        # Display results
        st.markdown("---")
        st.header("📊 Results")
        
        # Execution times metrics
        cols = st.columns(len(st.session_state.exec_times))
        for idx, (platform, exec_time) in enumerate(st.session_state.exec_times.items()):
            with cols[idx]:
                st.metric(
                    label=f"{platform.upper()} Execution Time",
                    value=f"{exec_time:.2f}s" if exec_time else "N/A"
                )
        
        # Show results for each platform
        for platform, result in st.session_state.results.items():
            with st.expander(f"📄 {platform.upper()} Results", expanded=True):
                if result.get("status") == "error":
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                else:
                    st.json(result)
        
        # Best result selection
        st.markdown("---")
        st.subheader("🏆 Select the best result")
        
        available_options = list(st.session_state.results.keys())

        platform_display_names = {
            "gemini": "🤖 Google Gemini AI",
            "unstract": "🔧 Unstract",
            # "document_ai": "📄 Google Document AI"
        }
        display_to_enum = {v: k for k, v in platform_display_names.items()}
        display_options = [platform_display_names[opt] for opt in available_options]
        if 'best_selection' not in st.session_state:
            st.session_state.best_selection = display_options[0]
        
        best_display = st.radio(
            "Which platform performed best?",
            display_options,
            key="best_radio",
            index=display_options.index(st.session_state.best_selection) if st.session_state.best_selection in display_options else 0,
            horizontal=True
        )
        
        if best_display != st.session_state.best_selection:
            st.session_state.best_selection = best_display

        best = display_to_enum[best_display]
        
        print(f"Selected platform: {best}")
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            if st.button("💾 Save Test", key="save_test_button", use_container_width=True):
                try:
                    print("=" * 60)
                    print("GUARDANDO TEST")
                    print(f"Username: {st.session_state.username}")
                    print(f"User ID: {st.session_state.user_id}")
                    print(f"Filename: {st.session_state.current_filename}")
                    print(f"File type: {st.session_state.current_file_type}")
                    print(f"Results keys: {list(st.session_state.results.keys())}")
                    print(f"Exec times: {st.session_state.exec_times}")
                    print(f"Best: {best}")
                    print("=" * 60)
                    
                    result = save_test(
                        user_id=st.session_state.user_id,
                        filename=st.session_state.current_filename,
                        file_type=st.session_state.current_file_type,
                        results=st.session_state.results,
                        exec_times=st.session_state.exec_times,
                        best=best
                    )
                    
                    if result and result.get("success"):
                        st.success(f"✅ Test saved successfully with ID: {result['id']}")
                        st.balloons()
                        st.session_state.results = None
                        st.session_state.exec_times = None
                        st.session_state.current_filename = None
                        st.session_state.current_file_type = None
                        st.session_state.file_bytes_stored = None
                        st.session_state.best_selection = None
                    else:
                        st.error("❌ Error: Test not saved")
                        
                except Exception as e:
                    st.error(f"❌ Error saving test: {e}")
                    print(f"ERROR COMPLETO: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Reset button
        if st.button("🔄 Process Another Invoice", key="reset_button"):
            st.session_state.results = None
            st.session_state.exec_times = None
            st.session_state.current_filename = None
            st.session_state.current_file_type = None
            st.session_state.file_bytes_stored = None
            st.session_state.best_selection = None
            st.session_state.processing = False
            st.rerun()
# --------------------------
# Tab 2: User History
# --------------------------
with tab2:
    st.header(f"📜 My History ({st.session_state.username})")
    
    try:
        user_tests = get_user_tests(st.session_state.user_id)
        
        if user_tests:
            # Create DataFrame
            df = pd.DataFrame(user_tests, columns=[
                'ID', 'Filename', 'File Type', 'Best Platform', 
                'Gemini Time (s)', 'Unstract Time (s)', 'Document AI Time (s)', 'Date'
            ])
            
            # Format times
            for col in ['Gemini Time (s)', 'Unstract Time (s)', 'Document AI Time (s)']:
                df[col] = df[col].apply(lambda x: f"{x:.2f}" if x is not None else "N/A")
            
            # Format date
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download All History as CSV",
                data=csv,
                file_name="all_ocr_history.csv",
                mime="text/csv"
            )
        else:
            st.info("📭 No tests found yet!")
            
    except Exception as e:
        st.error(f"❌ Error loading history: {e}")

# --------------------------
# Tab 4: Statistics
# --------------------------
with tab3:
    st.header("📊 Platform Performance Statistics")
    
    try:
        # Get all statistics
        stats = get_statistics()
    
        if stats[0] > 0:  # If there are tests
            total_tests = stats[0]
            
            # Overall metrics
            st.subheader("🎯 Overall Performance")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Tests", total_tests)
            
            with col2:
                gemini_pct = (stats[1] / total_tests * 100) if stats[1] else 0
                st.metric("🤖 Gemini Wins", f"{stats[1]} ({gemini_pct:.1f}%)")
            
            with col3:
                unstract_pct = (stats[2] / total_tests * 100) if stats[2] else 0
                st.metric("🔧 Unstract Wins", f"{stats[2]} ({unstract_pct:.1f}%)")
            
            with col4:
                docai_pct = (stats[3] / total_tests * 100) if stats[3] else 0
                st.metric("📄 Document AI Wins", f"{stats[3]} ({docai_pct:.1f}%)")
            
            st.markdown("---")
            
            # Execution time comparison
            st.subheader("⏱️ Average Execution Time Comparison")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if stats[4]:
                    st.metric(
                        "🤖 Gemini AI",
                        f"{stats[4]:.2f}s",
                        delta=None
                    )
                    st.caption(f"Min: {stats[7]:.2f}s | Max: {stats[10]:.2f}s")
                else:
                    st.metric("🤖 Gemini AI", "N/A")
            
            with col2:
                if stats[5]:
                    st.metric(
                        "🔧 Unstract",
                        f"{stats[5]:.2f}s",
                        delta=None
                    )
                    st.caption(f"Min: {stats[8]:.2f}s | Max: {stats[11]:.2f}s")
                else:
                    st.metric("🔧 Unstract", "N/A")
            
            with col3:
                if stats[6]:
                    st.metric(
                        "📄 Document AI",
                        f"{stats[6]:.2f}s",
                        delta=None
                    )
                    st.caption(f"Min: {stats[9]:.2f}s | Max: {stats[12]:.2f}s")
                else:
                    st.metric("📄 Document AI", "N/A")
            
            st.markdown("---")
            
            # Winner announcement
            st.subheader("🏆 Performance Summary")
            
            # Find fastest platform
            times = {
                'Gemini AI': stats[4],
                'Unstract': stats[5],
                'Document AI': stats[6]
            }
            valid_times = {k: v for k, v in times.items() if v is not None}
            
            if valid_times:
                fastest = min(valid_times, key=valid_times.get)
                st.success(f"🚀 **Fastest Platform:** {fastest} ({valid_times[fastest]:.2f}s average)")
            
            # Find most accurate platform
            wins = {
                'Gemini AI': stats[1],
                'Unstract': stats[2],
                'Document AI': stats[3]
            }
            most_accurate = max(wins, key=wins.get)
            
            if wins[most_accurate] > 0:
                st.success(f"🎯 **Most Accurate Platform:** {most_accurate} ({wins[most_accurate]} wins, {wins[most_accurate]/total_tests*100:.1f}%)")
            
            # Chart: Win distribution
            st.markdown("---")
            st.subheader("📈 Win Distribution")
            
            win_data = pd.DataFrame({
                'Platform': ['Gemini AI', 'Unstract', 'Document AI'],
                'Wins': [stats[1], stats[2], stats[3]]
            })
            
            st.bar_chart(win_data.set_index('Platform'))
            
            # Recent trends
            st.markdown("---")
            st.subheader("📅 Recent Activity (Last 10 Tests)")
            
            recent = get_recent_tests(10)
            
            recent_df = pd.DataFrame(recent, columns=[
                'Filename', 'Winner', 'Gemini Time', 'Unstract Time', 'Doc AI Time', 'Date'
            ])
            
            # Format
            for col in ['Gemini Time', 'Unstract Time', 'Doc AI Time']:
                recent_df[col] = recent_df[col].apply(lambda x: f"{x:.2f}s" if x is not None else "N/A")
            
            recent_df['Date'] = pd.to_datetime(recent_df['Date']).dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(recent_df, use_container_width=True, hide_index=True)
            
        else:
            st.info("📭 No statistics available yet. Process some invoices first!")
            
    except Exception as e:
        st.error(f"❌ Error loading statistics: {e}")

#Footer
st.divider()
# st.markdown("""
# <div style='text-align: center; color: #666;'>
#     <p>📄 OCR Invoice Comparator | Built with Streamlit | Powered by Gemini AI, Unstract & Document AI</p>
# </div>
# """, unsafe_allow_html=True) = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d %H:%M')
            
#             st.dataframe(
#                 df,
#                 use_container_width=True,
#                 hide_index=True
#             )
            
#             # Download button
#             csv = df.to_csv(index=False)
#             st.download_button(
#                 label="📥 Download History as CSV",
#                 data=csv,
#                 file_name=f"my_ocr_history_{st.session_state.username}.csv",
#                 mime="text/csv"
#             )
#         else:
#             st.info("📭 No tests found. Process your first invoice in the 'Process Invoice' tab!")
            
#     except Exception as e:
#         st.error(f"❌ Error loading history: {e}")

# # --------------------------
# # Tab 3: All Users History
# # --------------------------
# with tab3:
#     st.header("👥 All Users History")
    
#     try:
#         all_tests = get_all_tests()
    
#         if all_tests:
#             df = pd.DataFrame(all_tests, columns=[
#                 'ID', 'Username', 'Filename', 'File Type', 'Best Platform',
#                 'Gemini Time (s)', 'Unstract Time (s)', 'Document AI Time (s)', 'Date'
#             ])
            
#             # Format times
#             for col in ['Gemini Time (s)', 'Unstract Time (s)', 'Document AI Time (s)']:
#                 df[col] = df[col].apply(lambda x: f"{x:.2f}" if x is not None else "N/A")
            
#             # Format date
#             df['Date']

