"""
Authentication UI Component
Handles Google Calendar authentication within Streamlit.
"""
import streamlit as st
from pathlib import Path
import time

from config import TOKEN_FILE
from integrations.gcal_authentication import authenticate as run_google_auth


def check_credentials_file() -> bool:
    """Check if credentials.json exists."""
    credentials_file = Path(__file__).parent.parent.parent / "secrets" / "credentials.json"
    return credentials_file.exists()


def run_authentication() -> bool:
    """
    Run the authentication function directly.
    
    Returns:
        True if authentication was successful, False otherwise
    """
    try:
        # Call the authentication function directly
        success = run_google_auth()
        return success
    except FileNotFoundError as e:
        # Credentials.json not found
        st.error(str(e))
        return False
    except Exception as e:
        st.error(f"Authentication failed: {str(e)}")
        return False


def render_authentication_prompt():
    """
    Render authentication prompt in Streamlit UI.
    Shows instructions and handles authentication flow.
    """
    st.markdown("""
    <h3 style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
       color: #06b6d4; font-weight: 600; margin-bottom: 16px;">
        🔐 Authentication Required
    </h3>
    <hr style="border: 1px solid #64748b; margin: 16px 0;">
    """, unsafe_allow_html=True)
    
    # Check if credentials.json exists
    has_credentials = check_credentials_file()
    
    if not has_credentials:
        st.warning("⚠️ **OAuth Credentials Not Found**")
        st.markdown("""
        You need to set up OAuth credentials first:
        
        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Select your project (or create one)
        3. Enable **Google Calendar API**
        4. Go to **APIs & Services > Credentials**
        5. Click **Create Credentials > OAuth 2.0 Client ID**
        6. Choose **Desktop app** as application type
        7. Download the JSON file
        8. Save it as `secrets/credentials.json`
        """)
        
        with st.expander("📋 Detailed Setup Instructions"):
            st.markdown("""
            **Step-by-Step Guide:**
            
            1. **Create/Select Project:**
               - Visit https://console.cloud.google.com/
               - Create a new project or select an existing one
            
            2. **Enable Google Calendar API:**
               - Go to "APIs & Services" > "Library"
               - Search for "Google Calendar API"
               - Click "Enable"
            
            3. **Create OAuth Credentials:**
               - Go to "APIs & Services" > "Credentials"
               - Click "Create Credentials" > "OAuth 2.0 Client ID"
               - If prompted, configure OAuth consent screen first
               - Choose "Desktop app" as application type
               - Click "Create"
               - Click "Download JSON"
            
            4. **Save Credentials:**
               - Save the downloaded file as `credentials.json`
               - Place it in the `secrets/` folder
            """)
        return False
    
    st.info("""
    **Starting authentication...** 
    
    A browser window will open for you to sign in with your Google account.
    """)
    
    # Automatically start authentication
    with st.spinner("Starting authentication process..."):
        # Show instructions
        st.info("""
        **Authentication Process:**
        1. A browser window will open automatically
        2. Sign in with your Google account
        3. Click "Allow" to grant calendar access
        4. You'll be redirected back automatically
        5. The page will refresh automatically when done
        """)
        
        # Run authentication automatically
        success = run_authentication()
        
        if success:
            st.success("✅ Authentication successful! Refreshing...")
            st.balloons()
            # Clear any cached calendar service - import here to avoid circular import
            try:
                from ui.components.calendar_events import get_calendar_service
                get_calendar_service.clear()
            except:
                pass
            # Clear calendar events cache
            if 'calendar_events' in st.session_state:
                del st.session_state['calendar_events']
            # Small delay to show success message
            time.sleep(1)
            # Rerun to refresh the page
            st.rerun()
        else:
            st.error("❌ Authentication failed. Please check the error messages above.")
            # Show retry button
            if st.button("🔄 Retry Authentication", use_container_width=True, type="primary"):
                st.rerun()
    
    st.markdown("---")
    st.markdown("""
    **Alternative Method:**
    
    If the button above doesn't work, you can also run this command in your terminal:
    
    ```bash
    python integrations/gcal_authentication.py
    ```
    
    Then refresh this page.
    """)
    
    return False

