from trio_mysql import cursors, OperationalError, Warning
from trio_mysql.tests import base

import os
import warnings

__all__ = ["TestLoadLocal"]


class TestLoadLocal(base.TrioMySQLTestCase):
    def test_no_file(self):
        """Test load local infile when the file does not exist"""
        conn = self.connections[0]
        c = conn.cursor()
        await c.execute("CREATE TABLE test_load_local (a INTEGER, b INTEGER)")
        try:
            self.assertRaises(
                OperationalError,
                await c.execute,
                ("LOAD DATA LOCAL INFILE 'no_data.txt' INTO TABLE "
                 "test_load_local fields terminated by ','")
            )
        finally:
            await c.execute("DROP TABLE test_load_local")
            c.close()

    def test_load_file(self):
        """Test load local infile with a valid file"""
        conn = self.connections[0]
        c = conn.cursor()
        await c.execute("CREATE TABLE test_load_local (a INTEGER, b INTEGER)")
        filename = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'data',
                                'load_local_data.txt')
        try:
            await c.execute(
                ("LOAD DATA LOCAL INFILE '{0}' INTO TABLE " +
                 "test_load_local FIELDS TERMINATED BY ','").format(filename)
            )
            await c.execute("SELECT COUNT(*) FROM test_load_local")
            self.assertEqual(22749, (await c.fetchone())[0])
        finally:
            await c.execute("DROP TABLE test_load_local")

    def test_unbuffered_load_file(self):
        """Test unbuffered load local infile with a valid file"""
        conn = self.connections[0]
        c = conn.cursor(cursors.SSCursor)
        await c.execute("CREATE TABLE test_load_local (a INTEGER, b INTEGER)")
        filename = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'data',
                                'load_local_data.txt')
        try:
            await c.execute(
                ("LOAD DATA LOCAL INFILE '{0}' INTO TABLE " +
                 "test_load_local FIELDS TERMINATED BY ','").format(filename)
            )
            await c.execute("SELECT COUNT(*) FROM test_load_local")
            self.assertEqual(22749, (await c.fetchone())[0])
        finally:
            c.close()
            conn.close()
            conn.connect()
            c = conn.cursor()
            await c.execute("DROP TABLE test_load_local")

    def test_load_warnings(self):
        """Test load local infile produces the appropriate warnings"""
        conn = self.connections[0]
        c = conn.cursor()
        await c.execute("CREATE TABLE test_load_local (a INTEGER, b INTEGER)")
        filename = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'data',
                                'load_local_warn_data.txt')
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                await c.execute(
                    ("LOAD DATA LOCAL INFILE '{0}' INTO TABLE " +
                     "test_load_local FIELDS TERMINATED BY ','").format(filename)
                )
                self.assertEqual(w[0].category, Warning)
                expected_message = "Incorrect integer value"
                if expected_message not in str(w[-1].message):
                    self.fail("%r not in %r" % (expected_message, w[-1].message))
        finally:
            await c.execute("DROP TABLE test_load_local")
            c.close()
