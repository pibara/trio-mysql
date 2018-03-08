from . import capabilities
import trio_mysql
from trio_mysql.tests import base
import warnings

warnings.filterwarnings('error')

class test_MySQLdb(capabilities.DatabaseTest):

    db_module = trio_mysql
    connect_args = ()
    connect_kwargs = base.TrioMySQLTestCase.databases[0].copy()
    connect_kwargs.update(dict(read_default_file='~/.my.cnf',
                          use_unicode=True, binary_prefix=True,
                          charset='utf8', sql_mode="ANSI,STRICT_TRANS_TABLES,TRADITIONAL"))

    create_table_extra = "ENGINE=INNODB CHARACTER SET UTF8"
    leak_test = False

    def quote_identifier(self, ident):
        return "`%s`" % ident

    def test_TIME(self):
        from datetime import timedelta
        def generator(row,col):
            return timedelta(0, row*8000)
        self.check_data_integrity(
                 ('col1 TIME',),
                 generator)

    def test_TINYINT(self):
        # Number data
        def generator(row,col):
            v = (row*row) % 256
            if v > 127:
                v = v-256
            return v
        self.check_data_integrity(
            ('col1 TINYINT',),
            generator)

    def test_stored_procedures(self):
        db = self.connection
        c = self.cursor
        try:
            self.create_table(('pos INT', 'tree CHAR(20)'))
            await c.executemany("INSERT INTO %s (pos,tree) VALUES (%%s,%%s)" % self.table,
                          list(enumerate('ash birch cedar larch pine'.split())))
            await db.commit()

            await c.execute("""
            CREATE PROCEDURE test_sp(IN t VARCHAR(255))
            BEGIN
                SELECT pos FROM %s WHERE tree = t;
            END
            """ % self.table)
            await db.commit()

            await c.callproc('test_sp', ('larch',))
            rows = await c.fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0], 3)
            await c.nextset()
        finally:
            await c.execute("DROP PROCEDURE IF EXISTS test_sp")
            await c.execute('drop table %s' % (self.table))

    def test_small_CHAR(self):
        # Character data
        def generator(row,col):
            i = ((row+1)*(col+1)+62)%256
            if i == 62: return ''
            if i == 63: return None
            return chr(i)
        self.check_data_integrity(
            ('col1 char(1)','col2 char(1)'),
            generator)

    def test_bug_2671682(self):
        from trio_mysql.constants import ER
        try:
            await self.cursor.execute("describe some_non_existent_table");
        except self.connection.ProgrammingError as msg:
            self.assertEqual(msg.args[0], ER.NO_SUCH_TABLE)

    def test_ping(self):
        await self.connection.ping()

    def test_literal_int(self):
        self.assertTrue("2" == self.connection.literal(2))

    def test_literal_float(self):
        self.assertTrue("3.1415" == self.connection.literal(3.1415))

    def test_literal_string(self):
        self.assertTrue("'foo'" == self.connection.literal("foo"))