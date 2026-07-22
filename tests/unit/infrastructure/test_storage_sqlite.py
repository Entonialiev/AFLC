"""
Tests for SQLite Storage
"""

import pytest
import os
import json

from aflc.infrastructure.storage.sqlite import SQLiteStorage


class TestSQLiteStorage:
    def setup_method(self):
        self.db_path = "test_aflc.db"
        self.storage = SQLiteStorage(db_path=self.db_path)

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_and_load(self):
        self.storage.save("key1", "value1")
        assert self.storage.load("key1") == "value1"

    def test_save_and_load_complex(self):
        data = {"name": "test", "values": [1, 2, 3]}
        self.storage.save("complex", data)
        loaded = self.storage.load("complex")
        assert loaded == data

    def test_update(self):
        self.storage.save("key1", "value1")
        self.storage.save("key1", "value2")
        assert self.storage.load("key1") == "value2"

    def test_delete(self):
        self.storage.save("key1", "value1")
        self.storage.delete("key1")
        assert self.storage.load("key1") is None

    def test_list_keys(self):
        self.storage.save("prefix_1", "value1")
        self.storage.save("prefix_2", "value2")
        self.storage.save("other_1", "value3")

        keys = self.storage.list_keys("prefix_")
        assert set(keys) == {"prefix_1", "prefix_2"}

    def test_clear(self):
        self.storage.save("key1", "value1")
        self.storage.save("key2", "value2")
        self.storage.clear()
        assert self.storage.count() == 0

    def test_count(self):
        assert self.storage.count() == 0
        self.storage.save("key1", "value1")
        assert self.storage.count() == 1
        self.storage.save("key2", "value2")
        assert self.storage.count() == 2

    def test_get_all(self):
        self.storage.save("key1", "value1")
        self.storage.save("key2", "value2")
        all_data = self.storage.get_all()
        assert all_data == {"key1": "value1", "key2": "value2"}

    def test_json_serialization(self):
        data = {"nested": {"array": [1, 2, 3]}}
        self.storage.save("json_data", data)
        loaded = self.storage.load("json_data")
        assert loaded == data

    def test_persistence(self):
        """Test that data persists across instances."""
        self.storage.save("persistent", "value")
        
        # Create new instance with same db path
        new_storage = SQLiteStorage(db_path=self.db_path)
        assert new_storage.load("persistent") == "value"
