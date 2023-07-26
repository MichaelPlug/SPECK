CREATE FUNCTION public."New_process_id"() RETURNS trigger
    LANGUAGE plpgsql
    AS $$BEGIN
  -- Your logic here
  -- This code will be executed when a new row is added to the 'input' table
  
  -- Example: Print the inserted row values
  
  RAISE NOTICE 'New row added: %', NEW;
  PERFORM pg_notify( CAST('update_notification' AS text), row_to_json(NEW)::text);
  RETURN NEW;
END;$$;


ALTER FUNCTION public."New_process_id"() OWNER TO root;

COMMENT ON FUNCTION public."New_process_id"() IS 'A entries id added to the database';

CREATE FUNCTION public."Update_a_row"() RETURNS trigger
    LANGUAGE plpgsql
    AS $$BEGIN
  -- Your logic here
  -- This code will be executed when a new row is added to the 'input' table
  
  -- Example: Print the inserted row values
  
  RAISE NOTICE 'Row updated: %', NEW;
  PERFORM pg_notify( CAST('update_a_row_notification' AS text), row_to_json(NEW)::text);
  RETURN NEW;
END;$$;


ALTER FUNCTION public."Update_a_row"() OWNER TO root;
