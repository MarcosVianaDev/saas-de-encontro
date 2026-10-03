from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("audit", "0001_initial")]
    operations = [migrations.RunSQL(
        sql="""
        CREATE FUNCTION reject_audit_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Audit logs are append-only';
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER audit_no_update_delete
            BEFORE UPDATE OR DELETE ON audit_auditlog
            FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation();
        CREATE TRIGGER audit_no_truncate
            BEFORE TRUNCATE ON audit_auditlog
            FOR EACH STATEMENT EXECUTE FUNCTION reject_audit_mutation();
        """,
        reverse_sql="""
        DROP TRIGGER audit_no_truncate ON audit_auditlog;
        DROP TRIGGER audit_no_update_delete ON audit_auditlog;
        DROP FUNCTION reject_audit_mutation();
        """,
    )]
