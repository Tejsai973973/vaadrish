import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from api.core.config import Settings

async def setup():
    settings = Settings()
    print(f"📌 Using database: {settings.database_url}")
    
    print("🔄 Creating tables...")
    engine = create_async_engine(settings.database_url)
    
    async with engine.begin() as conn:
        # Create tables manually
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS aqi_readings (
                id SERIAL PRIMARY KEY,
                city TEXT,
                date TIMESTAMP,
                aqi INTEGER,
                category TEXT,
                lat REAL,
                lon REAL
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS model_metrics (
                id SERIAL PRIMARY KEY,
                model_name TEXT,
                rmse REAL,
                r2 REAL,
                mae REAL,
                bias REAL,
                pearson_r REAL,
                date TIMESTAMP
            )
        """))
        
        print("✅ Tables created!")
        
        # Check if data exists
        result = await conn.execute(text("SELECT COUNT(*) FROM aqi_readings"))
        count = result.scalar()
        
        if count == 0:
            # Sample AQI data
            await conn.execute(text("""
                INSERT INTO aqi_readings (city, date, aqi, category, lat, lon)
                VALUES 
                    ('Delhi', NOW(), 185, 'Poor', 28.6139, 77.2090),
                    ('Mumbai', NOW(), 162, 'Moderate', 19.0760, 72.8777),
                    ('Bangalore', NOW(), 85, 'Satisfactory', 12.9716, 77.5946)
            """))
            
            # Sample model metrics
            await conn.execute(text("""
                INSERT INTO model_metrics (model_name, rmse, r2, mae, bias, pearson_r, date)
                VALUES ('CNN-LSTM-Attention', 12.4, 0.89, 8.7, 1.2, 0.92, NOW())
            """))
            
            print("✅ Sample data added!")
        else:
            print(f"✅ Data already exists ({count} records)")

asyncio.run(setup())