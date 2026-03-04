import sys
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Fixes MySQL M2M and FK constraints after migrating from auth.User to accounts_customuser'

    def handle(self, *args, **options):
        self.stdout.write("Starting MySQL schema alignment for CustomUser migration...\n")

        with connection.cursor() as cursor:
            # 1. Rename auto-generated M2M columns
            m2m_tables = [
                'home_article_likes', 
                'home_flamescourse_instructor', 
                'student_course_instructors'
            ]
            for t in m2m_tables:
                try:
                    cursor.execute(f"SHOW COLUMNS FROM {t};")
                    cols = [row[0] for row in cursor.fetchall()]
                    if 'user_id' in cols and 'customuser_id' not in cols:
                        self.stdout.write(f"Renaming 'user_id' to 'customuser_id' in {t}...")
                        try:
                            cursor.execute(f"ALTER TABLE {t} RENAME COLUMN user_id TO customuser_id;")
                            self.stdout.write(self.style.SUCCESS(f"  -> Success via RENAME COLUMN"))
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"  -> RENAME COLUMN failed: {e}. Trying CHANGE..."))
                            cursor.execute(f"SHOW COLUMNS FROM {t} LIKE 'user_id';")
                            col_type = cursor.fetchone()[1]
                            
                            # Drop FK if exists
                            cursor.execute(f"SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{t}' AND COLUMN_NAME='user_id' AND REFERENCED_TABLE_NAME IS NOT NULL;")
                            fk = cursor.fetchone()
                            if fk:
                                cursor.execute(f"ALTER TABLE {t} DROP FOREIGN KEY {fk[0]};")
                            
                            cursor.execute(f"ALTER TABLE {t} CHANGE user_id customuser_id {col_type};")
                            self.stdout.write(self.style.SUCCESS(f"  -> Success via CHANGE"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error checking table {t}: {e}"))
            
            # 2. Rewire Built-in FK Constraints (AllAuth, Admin Logs)
            query = """
            SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE REFERENCED_TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME = 'auth_user';
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            tables_to_rewire = [
                'account_emailaddress',
                'django_admin_log',
                'home_article_likes',
                'home_comment',
                'home_flamesteam',
                'socialaccount_socialaccount'
            ]

            for row in rows:
                table_name, col_name, constraint_name = row[0], row[1], row[2]
                if table_name in tables_to_rewire:
                    self.stdout.write(f"Rewiring {table_name}.{col_name} (Constraint: {constraint_name})")
                    try:
                        cursor.execute(f"ALTER TABLE {table_name} DROP FOREIGN KEY {constraint_name};")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  -> Error dropping old FK: {e}"))
                    
                    # Check nullability and column type (Must be BIGINT for CustomUser pk)
                    cursor.execute(f"SELECT IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table_name}' AND COLUMN_NAME='{col_name}';")
                    col_info = cursor.fetchone()
                    null_str = 'NULL' if col_info and col_info[0] == 'YES' else 'NOT NULL'
                    
                    try:
                        cursor.execute(f"ALTER TABLE {table_name} MODIFY {col_name} BIGINT {null_str};")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  -> Error modifying column type: {e}"))
                    
                    new_fk_name = f"{table_name}_{col_name}_fk_customuser"[:64]
                    try:
                        cursor.execute(f"ALTER TABLE {table_name} ADD CONSTRAINT {new_fk_name} FOREIGN KEY ({col_name}) REFERENCES accounts_customuser(id);")
                        self.stdout.write(self.style.SUCCESS(f"  -> Successfully rewired constraint to accounts_customuser!"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  -> Error adding new FK: {e}"))
        
        self.stdout.write(self.style.SUCCESS("\nSchema alignment complete! Your production database is now synced."))
