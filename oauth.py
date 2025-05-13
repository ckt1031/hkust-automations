import http.server
import socket
import socketserver
import threading
import webbrowser
from os import getenv
from urllib.parse import parse_qs, urlparse

import requests

MSFT_REDIRECT_URI = "http://localhost:53682"


class OAuthRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handles the OAuth redirect and extracts the authorization code."""

    def do_GET(self):
        """Handles GET requests, specifically for the redirect URI."""
        global auth_code  # Use the global variable to store the code
        query_components = parse_qs(urlparse(self.path).query)
        auth_code = query_components.get("code", [None])[0]  # Extract the code

        if auth_code:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><head><title>Authentication Successful</title></head><body><h1>Authentication Successful!</h1><p>You can close this window now.</p></body></html>"
            )
            # Signal the main thread that the code has been received
            global code_received_event
            code_received_event.set()
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><head><title>Authentication Failed</title></head><body><h1>Authentication Failed!</h1><p>Authorization code not found.</p></body></html>"
            )


def start_http_server():
    """Starts a simple HTTP server to listen for the OAuth redirect."""
    global httpd
    port = 53682
    handler = OAuthRequestHandler

    # Check if the port is already in use
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)  # Short timeout for checking
    result = sock.connect_ex(("localhost", port))
    sock.close()

    if result == 0:
        print(
            f"Port {port} is already in use.  Please close the application using this port."
        )
        return False

    try:
        httpd = socketserver.TCPServer(("", port), handler)
        print(f"Serving at port {port}")
        httpd.serve_forever()
    except OSError as e:
        print(f"Error starting server: {e}")
        return False
    return True


def get_fresh_refresh_token() -> str:
    """Get a fresh OAuth token by opening browser and listening on a port."""
    global auth_code
    global code_received_event
    auth_code = None
    code_received_event = threading.Event()

    client_id = getenv("MICROSOFT_CLIENT_ID")
    client_secret = getenv("MICROSOFT_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise Exception("Microsoft client ID or client secret is not set")

    scopes = [
        "email",
        "profile",
        "offline_access",  # Required for refresh token
        "openid",  # Required for ID token
        "Files.Read",
        "Files.ReadWrite",
        "Mail.Read",
        "Tasks.Read",
        "Tasks.ReadWrite",
    ]

    # Generate authorization URL
    auth_url = (
        "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
        f"client_id={client_id}&"
        "response_type=code&"
        f"redirect_uri={MSFT_REDIRECT_URI}&"
        "response_mode=query&"
        "scope=" + " ".join(scopes)
    )

    # Start the HTTP server in a separate thread
    server_thread = threading.Thread(target=start_http_server, daemon=True)
    server_thread.start()

    # Open browser for user to authenticate
    webbrowser.open(auth_url)
    print(
        "Please authenticate in browser.  The browser will redirect you back to the application."
    )

    # Wait for the authorization code to be received
    code_received_event.wait(timeout=60)  # Wait for a maximum of 60 seconds

    # Stop the HTTP server
    global httpd
    if "httpd" in globals() and httpd:
        httpd.shutdown()
        httpd.server_close()

    if not auth_code:
        raise Exception("Authorization code not received within the timeout period.")

    # Exchange code for tokens
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "redirect_uri": MSFT_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    response = requests.post(token_url, data=payload, timeout=5)
    if response.status_code != 200:
        raise Exception("Error exchanging auth code for token: " + response.text)

    with open("tokens.json", "w") as f:
        f.write(response.text)

    return response.json()["refresh_token"]


if __name__ == "__main__":
    try:
        token = get_fresh_refresh_token()
        print("Refresh Token:", token)
    except Exception as e:
        print("Error:", e)
