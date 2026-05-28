from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from app.config import settings
from sqlalchemy import text


Base = declarative_base()
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      
    pool_recycle=1800,       
    connect_args={
        "command_timeout": 30, 
        "timeout": 10          
    }
)
new_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with new_session() as session:
        yield session

def init_db():
    Base.metadata.create_all(bind=engine)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text(SQL_CREATE_FUNCTION))
        await conn.execute(text(SQL_CREATE_TRIGGER))
        await conn.execute(text(SQL_CREATE_UPDATED_AT_FUNCTION))
        await conn.execute(text(SQL_CREATE_UPDATED_AT_TRIGGER))

async def delete_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)



SQL_CREATE_FUNCTION = """
CREATE OR REPLACE FUNCTION notify_new_task() RETURNS trigger AS $$
BEGIN
  -- Уведомляем только при вставке новой или если статус сменился на pending
  IF (TG_OP = 'INSERT' AND NEW.status = 'pending') OR 
     (TG_OP = 'UPDATE' AND NEW.status = 'pending' AND OLD.status != 'pending') THEN
    PERFORM pg_notify('new_task_channel', NEW.id::text);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

SQL_CREATE_TRIGGER = """
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_trigger
    WHERE tgname = 'trigger_new_task'
      AND tgrelid = 'tasks'::regclass
  ) THEN
    CREATE TRIGGER trigger_new_task
    AFTER INSERT OR UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION notify_new_task();
  END IF;
END;
$$;
"""

SQL_CREATE_UPDATED_AT_FUNCTION = """
CREATE OR REPLACE FUNCTION set_task_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

SQL_CREATE_UPDATED_AT_TRIGGER = """
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_trigger
    WHERE tgname = 'trigger_set_task_updated_at'
      AND tgrelid = 'tasks'::regclass
  ) THEN
    CREATE TRIGGER trigger_set_task_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION set_task_updated_at();
  END IF;
END;
$$;
"""
