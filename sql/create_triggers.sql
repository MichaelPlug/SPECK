CREATE TRIGGER "New_process_id_trigger"
    AFTER INSERT
    ON public."cake-db"
    FOR EACH ROW
    EXECUTE FUNCTION public."New_process_id"();
    
CREATE TRIGGER "Row_updated"
    AFTER UPDATE OF "Status"
    ON public."cake-db"
    FOR EACH ROW
    EXECUTE FUNCTION public."Update_a_row"();