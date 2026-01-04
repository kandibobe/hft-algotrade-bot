import sys

from src.database.db_manager import Base, DatabaseManager

# Importing the models is crucial so they are registered with Base.metadata


def main():
    print("Initializing database...")
    try:
        engine = DatabaseManager.get_engine()

        # This will create all tables that are registered with Base.metadata
        Base.metadata.create_all(bind=engine)

        print("✅ Successfully created database tables: trades, signals, executions, system_events")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
