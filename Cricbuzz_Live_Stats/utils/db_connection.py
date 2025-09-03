#utils/db_connection.py
import mysql.connector
import os
from dotenv import load_dotenv
from mysql.connector import Error

# Load environment variables
load_dotenv()

def get_db_connection():
    """Establish and return database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def execute_query(query, params=None, fetch=True):
    """Execute SQL query and return results"""
    connection = get_db_connection()
    if connection is None:
        return None
        
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        
        if fetch:
            result = cursor.fetchall()
        else:
            connection.commit()
            result = cursor.rowcount
        
        cursor.close()
        connection.close()
        return result
        
    except Error as e:
        print(f"Error executing query: {e}")
        return None
    
def test_connection():
    """
    Test database connection and basic functionality
    Returns: Dictionary with connection status and table info
    """
    result = {
        'connected': False,
        'tables': [],
        'player_copy_count': 0
    }
    
    try:
        # Test connection
        connection = get_db_connection()
        if connection and connection.is_connected():
            result['connected'] = True
            
            # Get list of tables
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            # Extract table names - handle both tuple and dictionary results
            if tables and isinstance(tables[0], dict):
                # Dictionary cursor result
                db_name = os.getenv('DB_NAME', 'cricket_db1')
                result['tables'] = [table[f'Tables_in_{db_name}'] for table in tables]
            else:
                # Tuple cursor result
                result['tables'] = [table[0] for table in tables]
            
            # Get crud_info count
            if 'crud_info' in result['tables']:
                cursor.execute("SELECT COUNT(*) as count FROM crud_info")
                count_result = cursor.fetchone()
                if isinstance(count_result, dict):
                    result['player_copy_count'] = count_result['count']
                else:
                    result['player_copy_count'] = count_result[0]
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"Connection test failed: {e}")
    
    return result