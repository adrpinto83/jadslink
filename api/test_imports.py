#!/usr/bin/env python3
"""Quick test to validate all imports work"""

try:
    print("Testing imports...")
    from config import Settings, get_settings
    print("✓ config")

    from database import engine, async_session_maker, get_db
    print("✓ database")

    from models import Base, User, Tenant, Node, Plan, Ticket, Session, NodeMetric
    print("✓ models")

    from deps import get_current_user, get_current_tenant, get_node_by_api_key
    print("✓ deps")

    from main import app
    print("✓ main")

    print("\n✅ All imports successful!")
except Exception as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
