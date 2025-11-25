import sqlite3
import pandas as pd
from pathlib import Path
from data_loader import DataLoader


class SQLiteStorage:
    @staticmethod
    def create_database(db_path: str = "market_data.db", schema_path: str = "data/schema.sql") -> None:
        """
        Create SQLite database from schema.sql.
        
        Args:
            db_path: Path to create/overwrite the database
            schema_path: Path to schema.sql file
        """
        # Remove existing database if it exists (fresh start)
        Path(db_path).unlink(missing_ok=True)
        
        # Connect and read schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        
        # Execute all SQL statements in schema
        cursor.executescript(schema_sql)
        conn.commit()
        conn.close()
        
        print(f"✓ Database created at {db_path}")

    @staticmethod
    def insert_data(df: pd.DataFrame = None, db_path: str = "market_data.db") -> None:
        """
        Insert validated market data into SQLite database.
        
        Args:
            df: DataFrame from DataLoader (if None, loads from CSV)
            db_path: Path to SQLite database
        """
        if df is None:
            df = DataLoader.load_from_csv()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert tickers (avoiding duplicates)
        unique_tickers = df["ticker"].unique()
        for ticker in unique_tickers:
            try:
                cursor.execute(
                    "INSERT INTO tickers (symbol) VALUES (?)",
                    (ticker,)
                )
            except sqlite3.IntegrityError:
                # Ticker already exists, skip
                pass
        
        conn.commit()
        
        # Fetch ticker_id mapping
        cursor.execute("SELECT ticker_id, symbol FROM tickers")
        ticker_map = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Insert price data
        for _, row in df.iterrows():
            ticker_id = ticker_map[row["ticker"]]
            cursor.execute(
                """
                INSERT INTO prices (timestamp, ticker_id, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row["timestamp"]),
                    ticker_id,
                    float(row["open"]),
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                    int(row["volume"])
                )
            )
        
        conn.commit()
        conn.close()
        
        print(f"✓ Inserted {len(df)} rows into {db_path}")

    @staticmethod
    def query_tsla_date_range(start_date: str, end_date: str, db_path: str = "market_data.db") -> pd.DataFrame:
        """
        Retrieve all data for TSLA between start_date and end_date.
        
        Args:
            start_date: Start date (format: "2025-11-17" or "2025-11-17 09:30:00")
            end_date: End date (format: "2025-11-17" or "2025-11-17 09:30:00")
            db_path: Path to SQLite database
            
        Returns:
            DataFrame with TSLA data in date range
        """
        conn = sqlite3.connect(db_path)
        query = """
            SELECT 
                p.timestamp,
                t.symbol,
                p.open,
                p.high,
                p.low,
                p.close,
                p.volume
            FROM prices p
            JOIN tickers t ON p.ticker_id = t.ticker_id
            WHERE t.symbol = 'TSLA'
                AND p.timestamp BETWEEN ? AND ?
            ORDER BY p.timestamp
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df

    @staticmethod
    def query_avg_daily_volume(db_path: str = "market_data.db") -> pd.DataFrame:
        """
        Calculate average daily volume per ticker.
        
        Args:
            db_path: Path to SQLite database
            
        Returns:
            DataFrame with ticker and avg_daily_volume
        """
        conn = sqlite3.connect(db_path)
        query = """
            SELECT 
                t.symbol,
                AVG(p.volume) as avg_daily_volume
            FROM prices p
            JOIN tickers t ON p.ticker_id = t.ticker_id
            GROUP BY t.symbol
            ORDER BY t.symbol
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    @staticmethod
    def query_top_3_tickers_by_return(db_path: str = "market_data.db") -> pd.DataFrame:
        """
        Identify top 3 tickers by return over the full period.
        
        Return is calculated as: (last_close - first_close) / first_close * 100
        
        Args:
            db_path: Path to SQLite database
            
        Returns:
            DataFrame with ticker, first_close, last_close, return_pct
        """
        conn = sqlite3.connect(db_path)
        query = """
            WITH first_last_prices AS (
                SELECT 
                    t.symbol,
                    (SELECT p.close 
                     FROM prices p 
                     WHERE p.ticker_id = t.ticker_id 
                     ORDER BY p.timestamp ASC 
                     LIMIT 1) as first_close,
                    (SELECT p.close 
                     FROM prices p 
                     WHERE p.ticker_id = t.ticker_id 
                     ORDER BY p.timestamp DESC 
                     LIMIT 1) as last_close
                FROM tickers t
            )
            SELECT 
                symbol,
                first_close,
                last_close,
                ROUND(((last_close - first_close) / first_close) * 100, 2) as return_pct
            FROM first_last_prices
            WHERE first_close IS NOT NULL AND last_close IS NOT NULL
            ORDER BY return_pct DESC
            LIMIT 3
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    @staticmethod
    def query_first_last_price_per_day(db_path: str = "market_data.db") -> pd.DataFrame:
        """
        Find first and last trade price for each ticker per day.
        
        Args:
            db_path: Path to SQLite database
            
        Returns:
            DataFrame with ticker, date, first_price, last_price
        """
        conn = sqlite3.connect(db_path)
        query = """
            SELECT 
                t.symbol,
                DATE(p.timestamp) as date,
                (SELECT p2.close 
                 FROM prices p2 
                 WHERE p2.ticker_id = p.ticker_id 
                   AND DATE(p2.timestamp) = DATE(p.timestamp)
                 ORDER BY p2.timestamp ASC 
                 LIMIT 1) as first_price,
                (SELECT p3.close 
                 FROM prices p3 
                 WHERE p3.ticker_id = p.ticker_id 
                   AND DATE(p3.timestamp) = DATE(p.timestamp)
                 ORDER BY p3.timestamp DESC 
                 LIMIT 1) as last_price
            FROM prices p
            JOIN tickers t ON p.ticker_id = t.ticker_id
            GROUP BY t.symbol, DATE(p.timestamp)
            ORDER BY t.symbol, date
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df


if __name__ == "__main__":
    # Create database
    SQLiteStorage.create_database()
    
    # Load and insert data
    df = DataLoader.load_from_csv()
    SQLiteStorage.insert_data(df)
    
    # Run queries
    print("\n*** Query 1: TSLA Data Range 2025-11-17 to 2025-11-18 ***")
    print(SQLiteStorage.query_tsla_date_range("2025-11-17", "2025-11-18"))
    
    print("\n*** Query 2: Average Daily Volume Per Ticker ***")
    print(SQLiteStorage.query_avg_daily_volume())
    
    print("\n*** Query 3: Top 3 Tickers by Return ***")
    print(SQLiteStorage.query_top_3_tickers_by_return())
    
    print("\n*** Query 4: First and Last Price Per Day ***")
    print(SQLiteStorage.query_first_last_price_per_day())