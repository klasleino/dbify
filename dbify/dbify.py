from decorator import decorator
from inspect import getfullargspec as getargspec

from dbify.connections import DbServer


def dbify(db_name, table, db_server=None):

    db_server = (
        DbServer.from_config(db_name) if db_server is None else db_server)

    def insert(db_cursor, column_names, values):
        query = [f'INSERT INTO {table} (']
        query.append(', '.join([col for col in column_names]))
        query.append(') VALUES (')
        query.append(', '.join([
            str(val) if not isinstance(val, str) else '%s' for val in values
        ]))
        query.append(')')

        print(' '.join(query))

        string_values = tuple([val for val in values if isinstance(val, str)])

        db_cursor.execute(' '.join(query), string_values)

    def create_table(db_cursor):
        db_cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS {} (
                id INT AUTO_INCREMENT PRIMARY KEY, 
                created datetime DEFAULT CURRENT_TIMESTAMP)
            '''
            .format(table))

    def prepare_column_headers(db_cursor, column_names, column_types):
        # Make sure we don't override reserved column names.
        for reserved_name in ['id', 'created', 'modified']:
            if reserved_name in column_names:
                raise ValueError(f'"{reserved_name}" is a reserved column name')

        # Get the existing column names and types.
        db_cursor.execute(f'DESCRIBE {table}')
        existing_column_info = [
            (col_info[0], col_info[1]) for col_info in db_cursor
        ]
        existing_column_names = [info[0] for info in existing_column_info]
        existing_column_types = [info[1] for info in existing_column_info]

        # Make sure all column types match the existing column types.
        for col_name, col_type in zip(column_names, column_types):
            if col_name in existing_column_names and col_type is not None:
                existing_type = existing_column_types[
                    existing_column_names.index(col_name)]

                if (existing_type.strip().lower().split('(')[0] != 
                        col_type.strip().lower().split('(')[0]):
                    raise ValueError(
                        f'Provided type for column "{col_name}" ({col_type}) '
                        f'did not match existing type ({existing_type})')

        # Find all columns that need to be added.
        new_columns = [
            (col_name, col_type) 
            for col_name, col_type in zip(column_names, column_types)
            if col_name not in existing_column_names
        ]

        if new_columns:
            query = [f'ALTER TABLE {table}']
            query.append(', '.join([
                f'ADD COLUMN {new_name} {new_type}'
                for new_name, new_type in new_columns
            ]))

            db_cursor.execute(' '.join(query))

    def get_type(val):
        if isinstance(val, bool):
            return 'TINYINT'

        elif isinstance(val, int):
            return 'INT'

        elif isinstance(val, float):
            return 'FLOAT'

        elif isinstance(val, str):
            return 'VARCHAR(255)'

        else:
            raise ValueError(
                f'Database does not support return type {type(val)}')

    @decorator
    def dbify_dec(fn, *args, **kwargs):

        spec = getargspec(fn)

        arg_names = spec.args
        defaults = [] if spec.defaults is None else spec.defaults

        num_non_kwargs = len(arg_names) - len(defaults)
        default_kwargs = {
            name: val for name, val in zip(arg_names[num_non_kwargs:], defaults)
        }

        # Make a column for each of the arguments passed to the function.
        given_args = {}

        for name in default_kwargs:
            given_args[name] = default_kwargs[name]
        for name in kwargs:
            given_args[name] = kwargs[name]
        for arg, name in zip(args, arg_names):
            given_args[name] = arg

        values = [val for val in given_args.values() if val is not None]
        column_names = [
            key for key in given_args.keys() if given_args[key] is not None
        ]
        column_types = [get_type(val) for val in values]

        # Run the function.
        result = fn(*args, **kwargs)

        # If result is a dictionary, we assume it maps columns in the DB to
        # values.
        if isinstance(result, dict):
            values += [val for val in result.values() if val is not None]
            column_names += [
                key for key in result.keys() if result[key] is not None
            ]
            column_types += [
                get_type(val) for val in result.values() if val is not None
            ]

        # TODO: If a result is a tuple, we assume we should have one column
        # for each entry in the tuple, labeled result0, result1, ..., etc.,
        # with values obtained from corresponding positions in the tuple.

        # TODO: If result is a single primitive object, we assume it's the
        # same as a tuple of one object.

        else:
            raise ValueError('Invalid return type for db-ified function.')

        with db_server as db:

            db_cursor = db.cursor()

            create_table(db_cursor)

            prepare_column_headers(
                db_cursor, column_names, column_types)

            insert(db_cursor, column_names, values)

            db.commit()

        return result

    return dbify_dec
