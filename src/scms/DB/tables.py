from scms.DB.db import engine , Base


try:
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully.")
except Exception as e:
    print(f"❌ ERROR CREATING TABLES: {e}")