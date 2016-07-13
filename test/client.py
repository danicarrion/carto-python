import unittest
import time

from carto import CartoException, APIKeyAuthClient, NoAuthClient, FileImport, URLImport, SQLCLient, FileImportManager, NamedMap, NamedMapManager
from secret import API_KEY, USER, EXISTING_TABLE, IMPORT_FILE, IMPORT_URL, NAMED_MAP_TEMPLATE1, TEMPLATE1_NAME, TEMPLATE1_AUTH_TOKEN, NAMED_MAP_TEMPLATE2, NAMED_MAP_PARAMS


class SQLClientTest(unittest.TestCase):
    def setUp(self):
        self.client = APIKeyAuthClient(API_KEY, USER)
        self.sql = SQLCLient(self.client)

    def test_sql_error(self):
        self.assertRaises(CartoException, self.sql.send, 'select * from non_existing_table')

    def test_sql_error_get(self):
        self.assertRaises(CartoException, self.sql.send, 'select * from non_existing_table', {'do_post': False})

    def test_sql(self, do_post=True):
        data = self.sql.send('select * from ' + EXISTING_TABLE, do_post=do_post)
        self.assertIsNotNone(data)
        self.assertIn('rows', data)
        self.assertIn('total_rows', data)
        self.assertIn('time', data)
        self.assertTrue(len(data['rows']) > 0)

    def test_sql_get(self):
        self.test_sql(do_post=False)


class NoAuthClientTest(unittest.TestCase):
    def setUp(self):
        self.client = NoAuthClient(USER)
        self.sql = SQLCLient(self.client)

    def test_no_api_key(self):
        self.assertFalse(hasattr(self.client, "api_key"))

    def test_sql_error(self):
        self.assertRaises(CartoException, self.sql.send, 'select * from non_existing_table')

    def test_sql_error_get(self):
        self.assertRaises(CartoException, self.sql.send, 'select * from non_existing_table', {'do_post': False})

    def test_sql(self, do_post=True):
        data = self.sql.send('select * from ' + EXISTING_TABLE, do_post=do_post)
        self.assertIsNotNone(data)
        self.assertIn('rows', data)
        self.assertIn('total_rows', data)
        self.assertIn('time', data)
        self.assertTrue(len(data['rows']) > 0)

    def test_sql_get(self):
        self.test_sql(do_post=False)


class FileImportTest(unittest.TestCase):
    def setUp(self):
        self.client = APIKeyAuthClient(API_KEY, USER)

    def test_file_import(self):
        fi = FileImport(IMPORT_FILE, self.client)
        fi.run()
        self.assertIsNotNone(fi.id)

    def test_url_import(self):
        fi = URLImport(IMPORT_URL, self.client)
        fi.run()
        self.assertIsNotNone(fi.id)

    def test_sync_import(self):
        fi = URLImport(IMPORT_URL, self.client, interval=3600)
        fi.run()
        self.assertIsNotNone(fi.id)

    def test_import_jobs_length(self):
        import_id = None
        manager = FileImportManager(self.client)
        all_imports = manager.all()
        self.assertEqual(len(all_imports), 1)
        import_id = all_imports[0].id
        self.assertIsNotNone(import_id)

    def test_updated_job_id(self):
        fi = FileImport(IMPORT_FILE, self.client)
        fi.run()
        self.assertEqual(fi.success, True)
        initial_id = fi.id
        has_state = True if hasattr(fi, "state") else False
        self.assertEqual(has_state, False)
        fi.update()
        time.sleep(5)
        self.assertEqual(fi.state, 'pending')
        final_id = fi.id
        self.assertEqual(initial_id, final_id)


class ImportErrorTest(unittest.TestCase):
    def setUp(self):
        self.client = APIKeyAuthClient(API_KEY, USER)

    def test_error_handling(self):
        fi = FileImport("test/fake.html", self.client)
        fi.run()
        self.assertEqual(fi.success, True)
        fi.update()
        count = 0
        while fi.state != 'failure':
            if count == 10:
                raise Exception("The state is incorrectly stored as: " + fi.state)
            time.sleep(5)
            fi.update()
            count += 1
        self.assertEqual(fi.state, 'failure')


class NamedMapTest(unittest.TestCase):
    def setUp(self):
        self.client = APIKeyAuthClient(API_KEY, USER)

    def test_named_map_methods(self):
        named = NamedMap(self.client, NAMED_MAP_TEMPLATE1)
        named.create()
        self.assertIsNotNone(named.template_name)
        self.assertIsNotNone(named.template_id)
        temp_id = named.template_id
        named.instantiate(NAMED_MAP_PARAMS, TEMPLATE1_AUTH_TOKEN)
        self.assertIsNotNone(named.layergroupid)
        named.update()
        self.assertEqual(named.template_id, temp_id)
        check_deleted = named.delete()
        self.assertEqual(check_deleted, 204)
    
    def test_named_map_manager(self):
        named = NamedMap(self.client, NAMED_MAP_TEMPLATE1)
        named_manager = NamedMapManager(self.client)
        initial_maps = named_manager.all(ids_only=False)
        named.create()
        named.instantiate(NAMED_MAP_PARAMS, TEMPLATE1_AUTH_TOKEN)
        temp_id = named.template_id
        test = named_manager.get(id=TEMPLATE1_NAME)
        test.update()
        self.assertEqual(temp_id, test.template_id)
        named2 = NamedMap(self.client, NAMED_MAP_TEMPLATE2)
        named2.create()
        all_maps = named_manager.all(ids_only=False)
        self.assertEqual(len(initial_maps) + 2, len(all_maps))
        all_maps[0].update()
        check_deleted = named.delete()
        self.assertEqual(check_deleted, 204)
        check_deleted2 = named2.delete()
        self.assertEqual(check_deleted2, 204)


if __name__ == '__main__':
    unittest.main()
