-- Initialize Database and Roles
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'stoic_trader') THEN
        CREATE ROLE stoic_trader WITH LOGIN PASSWORD 'Zuvs!vNMXKnWPwq3wnzmJ^iW1XDza9*A';
    END IF;
END
$$;

-- Grant privileges
ALTER ROLE stoic_trader CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE trading_analytics TO stoic_trader;
