from dotenv import load_dotenv
import os

# Auto-load .env file — no manual env vars needed!
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
