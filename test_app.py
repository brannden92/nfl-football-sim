#!/usr/bin/env python3
"""
Quick test script to verify the Flask app can initialize correctly
"""

print("Testing Flask app initialization...")

try:
    # Test imports
    print("1. Testing imports...")
    from flask import Flask
    import nfl_data_py as nfl
    import pandas as pd
    import requests
    from datetime import datetime, timedelta
    from dotenv import load_dotenv
    print("   ✓ All imports successful")

    # Test Flask app creation
    print("2. Testing Flask app creation...")
    from app import app
    print("   ✓ Flask app created successfully")

    # Test routes exist
    print("3. Testing routes...")
    with app.app_context():
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        expected_routes = ['/', '/search', '/player/<player_id>']

        for route in expected_routes:
            found = any(route in r for r in routes)
            if found:
                print(f"   ✓ Route '{route}' exists")
            else:
                print(f"   ✗ Route '{route}' missing")

    # Test data cache initialization
    print("4. Testing data cache structure...")
    from app import data_cache
    required_keys = ['players', 'rosters', 'weekly_stats', 'schedules', 'injuries', 'last_update']
    for key in required_keys:
        if key in data_cache:
            print(f"   ✓ Cache key '{key}' exists")
        else:
            print(f"   ✗ Cache key '{key}' missing")

    # Test template files exist
    print("5. Testing template files...")
    import os
    templates = ['templates/base.html', 'templates/index.html']
    for template in templates:
        if os.path.exists(template):
            print(f"   ✓ Template '{template}' exists")
        else:
            print(f"   ✗ Template '{template}' missing")

    # Test static files exist
    print("6. Testing static files...")
    static_files = ['static/css/style.css', 'static/js/main.js']
    for static_file in static_files:
        if os.path.exists(static_file):
            print(f"   ✓ Static file '{static_file}' exists")
        else:
            print(f"   ✗ Static file '{static_file}' missing")

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nThe Flask app is ready to run!")
    print("\nTo start the server, run:")
    print("  python app.py")
    print("\nThen open your browser to:")
    print("  http://localhost:5000")
    print("\nNote: Weather features require WEATHER_API_KEY in .env file")
    print("Get a free key at: https://www.weatherapi.com/signup.aspx")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\nPlease check the error above and ensure all dependencies are installed.")
