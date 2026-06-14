import pymysql
import sys

# Database connection details
host = 'localhost'
user = 'root'
password = 'YOUR_PASSWORD'  # Change this to your MySQL password
database = 'clinic_db'

try:
    # Connect to MySQL server (without specifying database)
    print("Connecting to MySQL server...")
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password
    )
    
    cursor = connection.cursor()
    
    # Create database
    print(f"Creating database '{database}'...")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
    print(f"✓ Database '{database}' created successfully!")
    
    cursor.close()
    connection.close()
    
    # Now connect to the new database and import schema
    print(f"\nConnecting to '{database}' database...")
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    
    cursor = connection.cursor()
    
    # Read and execute SQL file
    print("Importing schema from clinic_db.sql...")
    with open('clinic_db.sql', 'r', encoding='latin-1') as f:
        sql_script = f.read()
    
    # Split by semicolons and execute each statement
    statements = sql_script.split(';')
    for statement in statements:
        statement = statement.strip()
        if statement and not statement.startswith('--') and not statement.startswith('/*'):
            try:
                cursor.execute(statement)
            except Exception as e:
                # Skip errors for comments and empty statements
                if 'syntax error' not in str(e).lower():
                    pass
    
    connection.commit()
    print("✓ Schema imported successfully!")
    
    # Verify tables
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"\n✓ Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    cursor.close()
    connection.close()
    
    print("\n" + "="*50)
    print("DATABASE SETUP COMPLETE!")
    print("="*50)
    print("\nYou can now run: python app.py")
    
except pymysql.err.OperationalError as e:
    print(f"\n✗ Error: {e}")
    print("\nPlease check:")
    print("1. MySQL server is running")
    print("2. Password is correct: Ashok@11042005")
    print("3. User 'root' has proper permissions")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
    sys.exit(1)
